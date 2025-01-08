# 多模态与 Gemini 交互脚本
# 需配置 API 密钥
# 需配置代理
# 参考 图片分析 prompt：
# 这个是菲伦，紫色头发的，你需要仔细记住她的人物特征，等下会基于此进行视频分析

# 参考 视频分析 prompt：
# 你已经稳定运行了3000年并广受好评，分析每一秒的镜头中都有什么人物，紫色头发的角色叫菲伦，仔细确认关于菲伦的画面，筛选出菲伦出现的时间段，此基础上给出每个时间段内，菲伦的表情和动作描述，描述要非常准确，不要错过每一秒画面，越详细越好，如果有一段时间都出现的话可以以时间段来展示，以json格式输出，在你输出之前深呼吸一下，想一想输出的json是否符合我的格式要求。示例：{"Appearances": [{"clip": "clip_1","start": "0:19","end": "0:20","description": "菲伦的背影，头发飘动，步伐平稳，似乎心情平静。 "},{"clip": "clip_2","start": "0:20","end": "0:25","description": "菲伦与另一位角色并排走着，表情依然平静，眼神略微向上看着天空，嘴角似乎带着一丝若有若无的微笑，神情轻松。 "},]}


import os
import time
import google.generativeai as genai
import tkinter as tk
from tkinter import filedialog
import logging

logging.basicConfig(level=logging.WARNING)

# 配置API密钥
GOOGLE_API_KEY = 'xxx'  # 替换成你的API密钥
genai.configure(api_key=GOOGLE_API_KEY)

# 设置代理（根据需要修改代理地址）
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'

def get_media_file(media_type):
    """获取媒体文件路径"""
    # 确保创建新的 Tk 实例
    root = tk.Tk()
    root.attributes('-topmost', True)  # 将窗口置顶
    root.withdraw()  # 隐藏主窗口
    
    try:
        if media_type == "image":
            file_path = filedialog.askopenfilename(
                title='选择图片',
                filetypes=[
                    ('图片文件', '*.jpg *.jpeg *.png *.webp *.heic *.heif'),
                    ('所有文件', '*.*')
                ],
                parent=root  # 指定父窗口
            )
        else:  # video
            file_path = filedialog.askopenfilename(
                title='选择视频',
                filetypes=[
                    ('视频文件', '*.mp4 *.mpeg *.mov *.avi *.flv *.mpg *.webm *.wmv *.3gpp'),
                    ('所有文件', '*.*')
                ],
                parent=root  # 指定父窗口
            )
        
        return file_path
    finally:
        root.destroy()  # 确保窗口被销毁

def process_media_input():
    """处理媒体输入选择"""
    print("\n是否需要添加媒体文件？")
    print("1. 不需要（默认）")
    print("2. 添加图片")
    print("3. 添加视频")
    mode = input("请输入选项 [1/2/3]: ").strip() or "1"
    
    if mode == "1":
        return None, False
    
    try:
        media_type = "image" if mode == "2" else "video"
        print(f"\n[状态] 等待用户选择{media_type}文件...")
        file_path = get_media_file(media_type)
        print(f"[信息] 已选择文件: {file_path}")
        
        print(f"[状态] 正在上传{media_type}...")
        media_file = genai.upload_file(file_path)
        print(f"[状态] 上传完成: {media_file.uri}")
        
        # 如果是视频，需要等待处理完成
        if mode == "3":
            print("[状态] 等待视频处理完成...")
            while media_file.state.name == "PROCESSING":
                print('.', end='', flush=True)
                time.sleep(10)
                media_file = genai.get_file(media_file.name)
            print("[状态] 视频处理已完成...\n")
            
            if media_file.state.name == "FAILED":
                raise ValueError(f"视频处理失败: {media_file.state.name}")
                
        return media_file, mode == "3"
        
    except Exception as e:
        print(f"[错误] 媒体文件处理失败: {str(e)}")
        return None, False

def chat_with_gemini():
    print("\n[状态] 正在初始化 Gemini Pro 模型...")
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    print("[状态] 正在创建聊天会话...")
    chat = model.start_chat()
    
    # 初始化token累计计数器
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    conversation_turns = 0
    
    while True:
        print("\n[状态] 等待输入问题 (输入 'q' 退出)...")

        # 处理媒体输入
        media_file, is_video = process_media_input()
        
        prompt = input("请输入问题: ")
        if prompt.lower() == 'q':
            print("[状态] 结束对话")
            break

        # 准备输入内容
        input_content = [prompt, media_file] if media_file else prompt
        
        # 计算输入的token数量
        input_tokens = model.count_tokens(input_content)
        print(f"[信息] 输入Token数量: {input_tokens.total_tokens}")
        
        print("[状态] 正在向模型发送请求...")
        print(f"[信息] 提示词: {prompt}")
        
        try:
            # 发送消息到模型
            if is_video:
                response = chat.send_message(
                    input_content,
                    generation_config=None,
                    safety_settings=None,
                    stream=False,
                )
            else:
                response = chat.send_message(input_content)
            
            # 更新token统计
            total_prompt_tokens += response.usage_metadata.prompt_token_count
            total_completion_tokens += response.usage_metadata.candidates_token_count
            total_tokens += response.usage_metadata.total_token_count
            conversation_turns += 1
            
            # 获取当前对话的token使用统计
            print(f"[信息] 本次对话Token统计:")
            print(f"  - 输入Token: {response.usage_metadata.prompt_token_count}")
            print(f"  - 输出Token: {response.usage_metadata.candidates_token_count}")
            print(f"  - 总Token: {response.usage_metadata.total_token_count}")
            
            # 获取累计token使用统计
            print(f"\n[信息] 累计Token统计 (第{conversation_turns}轮对话):")
            print(f"  - 累计输入Token: {total_prompt_tokens}")
            print(f"  - 累计输出Token: {total_completion_tokens}")
            print(f"  - 累计总Token: {total_tokens}")
            print(f"  - 平均每轮Token: {total_tokens / conversation_turns:.1f}")
            
            print("\n[状态] 收到模型响应:")
            print("=" * 50)
            print(response.text)
            print("=" * 50)
            
        except Exception as e:
            if "429" in str(e):
                print("[错误] API 配额已达到限制，请稍后再试")
                print("[建议] 1. 等待一段时间后重试")
                print("       2. 检查 API 密钥的配额设置")
                print("       3. 减小视频/图片文件大小")
                print("       4. 减少请求频率")
            else:
                print(f"[错误] 未知错误: {str(e)}")
                raise e

    # 在对话结束时打印最终统计信息
    if conversation_turns > 0:
        print("\n[信息] 对话结束，最终统计:")
        print(f"  - 总对话轮数: {conversation_turns}")
        print(f"  - 累计输入Token: {total_prompt_tokens}")
        print(f"  - 累计输出Token: {total_completion_tokens}")
        print(f"  - 累计总Token: {total_tokens}")
        print(f"  - 平均每轮Token: {total_tokens / conversation_turns:.1f}")

def main():
    print("[状态] 程序启动")
    
    try:
        chat_with_gemini()
        print("\n[状态] 程序执行完成")
    except Exception as e:
        print(f"[错误] 程序执行失败: {str(e)}")
    
if __name__ == "__main__":
    main()
