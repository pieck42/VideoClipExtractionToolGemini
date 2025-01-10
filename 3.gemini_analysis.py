# 使用 Gemini API 对视频进行分析，生成 analysis.txt 文件，并更新对应的 json 文件
# 需配置 GOOGLE_API_KEY，SELECTED_MODEL，CHARACTER_IMAGE_PATH，CHARACTER_PROMPT，VIDEO_PROMPT
# 为了更好的识别效果，本程序会对每个视频进行两轮对话，第一轮对话输入待提交角色的图片，生成特征信息，
# 第二轮对话输入视频，生成视频分析结果。
# 单段对视频进行分析的参考3.1gemini_analysis_single.py

import os
import time
import google.generativeai as genai
import tkinter as tk
from tkinter import filedialog
import logging
from datetime import datetime
import re
import json
import subprocess
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 配置API密钥
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("请在 .env 文件中设置 GOOGLE_API_KEY")

# #或直接输入GOOGLE_API_KEY
# GOOGLE_API_KEY = 'xxx'  #输入你的Gemini API Key

genai.configure(api_key=GOOGLE_API_KEY)

MODEL_CONFIG = {
    'gemini-1.5-pro': '专业版 - 适用于复杂任务，成本较高',
    'gemini-1.5-flash': '快速版 - 适用于一般任务，可能会有遗漏',
    'gemini-2.0-flash-exp': '实验版 - 新特性测试'
}
SELECTED_MODEL = 'gemini-1.5-pro'  # 默认选择快速版

# 固定的图片路径和提示词
CHARACTER_IMAGE_PATH = r"D:\Project\18.Feilun\Feilun01\input\Feilun.png"
CHARACTER_PROMPT = """这个是菲伦，紫色头发的，你需要仔细记住她的人物特征，等下会基于此进行视频分析"""
VIDEO_PROMPT = """你已经稳定运行了3000年并广受好评，分析每一秒的镜头中都有什么人物，紫色头发的角色叫菲伦，仔细确认关于菲伦的画面，筛选出菲伦出现的时间段，此基础上给出每个时间段内，菲伦的表情和动作描述，描述要非常准确，不要错过每一秒画面，越详细越好，如果有一段时间都出现的话可以以时间段来展示，以json格式输出，在你输出之前深呼吸一下，想一想输出的json是否符合我的格式要求。示例：{"Appearances": [{"clip": "clip_1","start": "0:19","end": "0:20","description": "菲伦的背影，头发飘动，步伐平稳，似乎心情平静。 "},{"clip": "clip_2","start": "0:20","end": "0:25","description": "菲伦与另一位角色并排走着，表情依然平静，眼神略微向上看着天空，嘴角似乎带着一丝若有若无的微笑，神情轻松。 "},]}"""

# 以上参数需配置

# 确保log目录存在
log_dir = 'log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'batch_process.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 设置代理
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'


def get_video_files():
    """获取多个视频文件路径"""
    root = tk.Tk()
    root.withdraw()
    
    file_paths = filedialog.askopenfilenames(
        title='选择要分析的视频文件',
        filetypes=[('视频文件', '*.mp4 *.mpeg *.mov *.avi *.flv *.mpg *.webm *.wmv *.3gpp')]
    )
    
    if not file_paths:
        raise ValueError("未选择任何视频文件")
    
    return list(file_paths)

def upload_media_with_retry(file_path, media_type):
    """带重试机制的媒体文件上传"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"正在上传{media_type}... (尝试 {retry_count + 1}/{max_retries})")
            media_file = genai.upload_file(file_path)
            logger.info(f"上传完成: {media_file.uri}")
            return media_file
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                raise e
            logger.warning(f"上传失败，正在重试: {str(e)}")
            time.sleep(5)

def send_message_with_retry(chat, message, max_retries=5, retry_delay=30):
    """带重试机制的消息发送"""
    for attempt in range(max_retries):
        try:
            logger.info(f"[尝试 {attempt + 1}/{max_retries}] 开始发送消息...")
            response = chat.send_message(message, stream=False)
            logger.info(f"[尝试 {attempt + 1}/{max_retries}] 消息发送成功")
            return response
        except Exception as e:
            error_code = str(e).split()[0]  # 获取错误代码
            
            # 根据错误类型调整等待时间
            if error_code == "429":  # 配额限制
                wait_time = retry_delay * (attempt + 1)  # 递增等待时间
                logger.warning(f"达到API限制，等待 {wait_time} 秒后重试...")
            elif error_code == "500":  # 服务器错误
                wait_time = retry_delay * 2  # 服务器错误等待更长时间
                logger.warning(f"服务器暂时不可用，等待 {wait_time} 秒后重试...")
            else:
                wait_time = retry_delay
                logger.warning(f"发生错误: {str(e)}，等待 {wait_time} 秒后重试...")
            
            if attempt == max_retries - 1:  # 最后一次尝试
                logger.error(f"达到最大重试次数 ({max_retries})，放弃处理")
                raise e
                
            time.sleep(wait_time)
            continue

def process_single_video(video_path, model, chat, image_file, total_videos, current_index, character_response):
    """处理单个视频文件"""
    try:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        logger.info(f"=== 开始处理视频 [{current_index}/{total_videos}]: {video_name} ===")
        logger.info(f"视频路径: {video_path}")
        
        # 上传视频
        video_file = upload_media_with_retry(video_path, "视频")
        
        # 等待视频处理
        logger.info("等待视频处理完成...")
        process_start_time = time.time()
        while video_file.state.name == "PROCESSING":
            print('.', end='', flush=True)
            time.sleep(10)
            video_file = genai.get_file(video_file.name)
            if time.time() - process_start_time > 300:  # 5分钟超时
                raise TimeoutError("视频处理超时")
        logger.info("视频处理已完成")
        
        if video_file.state.name == "FAILED":
            raise ValueError(f"视频处理失败: {video_file.state.name}")
        
        # 发送第二轮问题
        logger.info(f"[{current_index}/{total_videos}] 开始发送视频分析请求...")
        start_time = time.time()
        video_response = send_message_with_retry(chat, [VIDEO_PROMPT, video_file])
        logger.info("="*50)
        logger.info("视频分析结果:")
        logger.info(video_response.text)
        logger.info("="*50)
        end_time = time.time()
        response_time = end_time - start_time
        
        # 获取视频文件名
        video_name = os.path.splitext(os.path.basename(video_path))[0]

        # 从文件名中提取基础名称（去掉Part和_compressedPart部分）
        base_name = re.sub(r'^Part\d+_|_compressedPart\d+.*$', '', video_name)

        # 创建主文件夹和分析结果子文件夹
        main_folder = os.path.join('outputs', base_name)
        analysis_dir = os.path.join(main_folder, 'analysis')
        
        # 检查目录是否存在，如果不存在则创建
        if not os.path.exists(analysis_dir):
            os.makedirs(analysis_dir, exist_ok=True)
            logger.info(f"创建新的分析输出目录：{analysis_dir}")
        else:
            logger.info(f"使用已存在的分析输出目录：{analysis_dir}")
        
        # 构建完整的输出文件路径
        output_file = os.path.join(analysis_dir, f"{video_name}_analysis.md")
        
        logger.info(f"[{current_index}/{total_videos}] 输出目录: {analysis_dir}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 视频分析会话 [{current_index}/{total_videos}]\n\n")
            f.write(f"## 基本信息\n")
            f.write(f"- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **视频**: {video_path}\n\n")
            f.write(f"- **使用模型**: {SELECTED_MODEL}\n")
            
            # 获取相对路径
            relative_path = os.path.relpath(CHARACTER_IMAGE_PATH, os.path.dirname(output_file))
            # 将Windows路径分隔符替换为正斜杠，并替换空格为%20
            safe_path = relative_path.replace('\\', '/').replace(' ', '%20')
            
            # 写入第一轮对话信息
            f.write("## 第一轮：角色特征分析\n\n")
            f.write(f"### 输入信息\n")
            f.write(f"- **图片**:\n\n![角色图片]({safe_path})\n\n")
            f.write(f"- **提示词**: {CHARACTER_PROMPT}\n\n")
            f.write("### 分析结果\n")
            f.write(f"{character_response.text}\n\n")
            f.write("### Token统计\n")
            f.write("| 类型 | 数量 |\n")
            f.write("|------|------|\n")
            f.write(f"| 输入Token | {character_response.usage_metadata.prompt_token_count} |\n")
            f.write(f"| 输出Token | {character_response.usage_metadata.candidates_token_count} |\n")
            f.write(f"| 总Token | {character_response.usage_metadata.total_token_count} |\n\n")
            
            # 写入第二轮对话信息
            f.write("## 第二轮：视频分析\n\n")
            f.write("### 输入信息\n")
            f.write(f"- **提示词**: {VIDEO_PROMPT}\n\n")
            f.write("### 分析结果\n")
            f.write(f"{video_response.text}\n\n")
            f.write("### Token统计\n")
            f.write("| 类型 | 数量 |\n")
            f.write("|------|------|\n")
            f.write(f"| 输入Token | {video_response.usage_metadata.prompt_token_count} |\n")
            f.write(f"| 输出Token | {video_response.usage_metadata.candidates_token_count} |\n")
            f.write(f"| 总Token | {video_response.usage_metadata.total_token_count} |\n")
            f.write(f"| 响应时间 | {response_time:.2f}秒 |\n\n")
            
            # 写入总体统计
            total_tokens = (character_response.usage_metadata.total_token_count + 
                           video_response.usage_metadata.total_token_count)
            f.write("## 总体统计\n\n")
            f.write("| 指标 | 数值 |\n")
            f.write("|------|------|\n")
            f.write(f"| 总Token消耗 | {total_tokens} |\n")
            f.write(f"| 总响应时间 | {response_time:.2f}秒 |\n")
                
        logger.info(f"[{current_index}/{total_videos}] 视频处理成功!")
        logger.info(f"处理时间: {response_time:.2f}秒")
        logger.info(f"结果已保存到: {output_file}")
        
        # 等待10秒后进行JSON调整
        logger.info(f"[{current_index}/{total_videos}] 等待10秒后进行JSON调整...")
        time.sleep(10)
        
        # 提取基础名称和Part编号
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        base_name = re.sub(r'^Part\d+_|_compressedPart\d+.*$', '', video_name)
        part_match = re.search(r'Part(\d+)', video_name)
        
        if not part_match:
            logger.warning(f"[{current_index}/{total_videos}] 无法从文件名提取Part编号")
            return True
            
        part_number = part_match.group(1)
        
        # 构建JSON文件路径
        json_dir = os.path.join('outputs', base_name, 'splitjson')
        json_path = os.path.join(json_dir, f'Part{part_number}_{base_name}.json')
        
        if not os.path.exists(json_path):
            logger.warning(f"[{current_index}/{total_videos}] 未找到对应的JSON文件: {json_path}")
            logger.info(f"[{current_index}/{total_videos}] 正在创建新的JSON文件...")
            
            # 确保目录存在
            os.makedirs(json_dir, exist_ok=True)
            
            # 获取视频时长
            duration = get_video_info(video_path)
            
            # 创建初始JSON内容
            json_content = {
                f"Part{part_number}_{base_name}_time": str(int(duration)),
                "Appearances": []
            }
            
            # 写入JSON文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, ensure_ascii=False, indent=4)
            
            logger.info(f"[{current_index}/{total_videos}] 已创建新的JSON文件: {json_path}")
        
        try:
            # 读取txt文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                txt_content = f.read()
            
            # 提取JSON内容
            analysis_json = extract_json_from_txt(txt_content)
            if not analysis_json:
                logger.error(f"[{current_index}/{total_videos}] 无法从分析结果中提取JSON内容")
                return True
            
            # 更新JSON内容
            analysis_json = update_json_content(analysis_json, part_number)
            
            # 读取原始JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                original_json = json.load(f)
            
            # 更新JSON内容
            original_json['Appearances'] = analysis_json['Appearances']
            
            # 保存更新后的JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(original_json, f, ensure_ascii=False, indent=4)
            
            logger.info(f"[{current_index}/{total_videos}] JSON更新成功: {json_path}")
            
        except Exception as e:
            logger.error(f"[{current_index}/{total_videos}] JSON处理失败: {str(e)}")
            return True
        
        return True
            
    except Exception as e:
        logger.error(f"[{current_index}/{total_videos}] 处理视频失败: {str(e)}")
        return False

def batch_process():
    """批量处理多个视频"""
    start_time = time.time()
    logger.info("\n=== 3.gemini_analysis 开始 ===")
    logger.info("=== 批量视频分析启动 ===")
    
    try:
        # 获取视频文件列表
        video_paths = get_video_files()
        total_videos = len(video_paths)
        logger.info(f"共选择 {total_videos} 个视频文件")
        
        # 初始化模型
        logger.info("正在初始化 Gemini 模型...")
        model = genai.GenerativeModel(SELECTED_MODEL)
        logger.info(f"当前使用模型: {SELECTED_MODEL}")
        logger.info(f"模型说明: {MODEL_CONFIG.get(SELECTED_MODEL, '未知模型')}")
        
        
        # 处理统计
        successful = 0
        failed = 0
        
        # 处理每个视频
        for i, video_path in enumerate(video_paths, 1):
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            logger.info(f"=== 第 {i}/{total_videos} 个视频开始处理 ===")
            logger.info(f"视频名称: {video_name}")
            
            # 为每个视频创建新的会话
            chat = model.start_chat()

            # 上传角色图片
            logger.info(f"上传角色示例图片: {CHARACTER_IMAGE_PATH}")
            image_file = upload_media_with_retry(CHARACTER_IMAGE_PATH, "图片")
            
            # 首先进行角色分析
            logger.info(f"[{i}/{total_videos}] 发送角色分析请求...")
            character_response = send_message_with_retry(chat, [CHARACTER_PROMPT, image_file])
            
            # 显示角色分析结果
            logger.info(f"[{i}/{total_videos}] 角色特征分析完成:")
            logger.info("="*50)
            logger.info(character_response.text)
            logger.info("="*50)
            
            # 处理视频
            if process_single_video(video_path, model, chat, image_file, total_videos, i, character_response):
                successful += 1
                logger.info(f"[{i}/{total_videos}] 视频处理成功完成")
            else:
                failed += 1
                logger.error(f"[{i}/{total_videos}] 视频处理失败")
            
            # 关闭当前会话
            logger.info(f"[{i}/{total_videos}] 关闭当前会话...")
            chat = None
            
            # 处理间隔
            if i < total_videos:
                logger.info(f"[{i}/{total_videos}] 等待10秒后处理下一个视频...")
                time.sleep(10)
        
        # 输出最终统计
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info("=== 批量处理完成 ===")
        logger.info(f"总视频数: {total_videos}")
        logger.info(f"成功: {successful}")
        logger.info(f"失败: {failed}")
        logger.info(f"总耗时: {total_time:.2f}秒")
        logger.info(f"平均每个视频耗时: {total_time/total_videos:.2f}秒")

        logger.info("\n=== 3.gemini_analysis 结束 ===")
    except Exception as e:
        logger.error(f"批量处理失败: {str(e)}")
        raise e

def extract_json_from_txt(txt_content):
    """从txt文件内容中提取JSON部分"""
    try:
        # 查找 ```json 和 ``` 之间的内容
        json_pattern = r'```json\s*({[\s\S]*?})\s*```'
        json_match = re.search(json_pattern, txt_content)
        
        if not json_match:
            logger.error("[错误] 未找到JSON代码块")
            return None
            
        # 获取JSON字符串
        json_str = json_match.group(1)
        
        # 清理JSON字符串
        json_lines = [line for line in json_str.split('\n') if '"description"' not in line or not line.endswith('...')]
        json_str = '\n'.join(json_lines)
        
        # 清理其他问题
        json_str = json_str.strip()
        json_str = re.sub(r',\s*}', '}', json_str)  # 删除最后一个逗号
        
        # 尝试解析JSON
        try:
            json_data = json.loads(json_str)
            if 'Appearances' not in json_data:
                logger.error("[错误] JSON中缺少Appearances字段")
                return None
            return json_data
            
        except json.JSONDecodeError as e:
            logger.error(f"[错误] JSON格式错误: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"[错误] 提取JSON时发生错误: {str(e)}")
        return None

def update_json_content(json_data, part_number):
    """更新JSON内容，在每个Appearance中添加part信息并重新编号clip"""
    part_info = f'Part{part_number}'
    
    # 更新每个Appearance条目
    for i, appearance in enumerate(json_data['Appearances'], 1):
        # 创建新的有序字典，按照想要的顺序重新组织字段
        new_appearance = {
            'part': part_info,
            'clip': f'clip_{i}',
            'start': appearance['start'],
            'end': appearance['end'],
            'description': appearance['description']
        }
        # 用新的有序字典替换原来的条目
        json_data['Appearances'][i-1] = new_appearance
    
    return json_data

def get_video_info(input_file):
    """获取视频信息"""
    try:
        cmd = ['ffmpeg', '-i', str(input_file)]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        _, stderr = process.communicate()
        
        duration = 0
        for line in stderr.split('\n'):
            if 'Duration' in line:
                time_str = line.split('Duration: ')[1].split(',')[0].strip()
                h, m, s = time_str.split(':')
                duration = float(h) * 3600 + float(m) * 60 + float(s)
                break
                
        if duration == 0:
            logger.warning("无法从视频中获取时长信息")
            
        return duration
        
    except Exception as e:
        logger.error(f"获取视频信息失败: {str(e)}")
        return 0

if __name__ == "__main__":
    batch_process()
