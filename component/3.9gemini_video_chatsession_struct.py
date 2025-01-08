# 通过命令行 Gemini 1.5 Flash 模型进行带视频提问
# 需配置 API 密钥
# 需配置代理
# chatsession 模式，结构化输出
# 通过 genai.upload_file 上传视频
# 通过 usage_metadata 获取 token 使用统计
# 通过 response_schema 获取 JSON 输出结构

# 参考 prompt 模板：
# 你已经稳定运行了3000年并广受好评，分析每一秒的镜头中都有什么人物，紫色头发的角色叫菲伦，仔细确认关于菲伦的画面，筛选出菲伦出现的时间段，此基础上给出每个时间段内，菲伦的表情和动作描述，描述要非常准确，不要错过每一秒画面，越详细越好，如果有一段时间都出现的话可以以时间段来展示，以json格式输出，在你输出之前深呼吸一下，想一想输出的json是否符合我的格式要求。示例：{"Appearances": [{"clip": "clip_1","start": "0:19","end": "0:20","description": "菲伦的背影，头发飘动，步伐平稳，似乎心情平静。 "},{"clip": "clip_2","start": "0:20","end": "0:25","description": "菲伦与另一位角色并排走着，表情依然平静，眼神略微向上看着天空，嘴角似乎带着一丝若有若无的微笑，神情轻松。 "},]}

# Gemini 使用结构化输出时，经常出现分析结果不准确的情况，
# 后来放弃了，使用了保存对话结果然后再提取 json 的方法
# 不知道是我使用的方法不对，还是说 Gemini 的结构化输出本身效果就不好，欢迎大家找我讨论

import os
import time
import json
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content

import PIL.Image
import tkinter as tk
from tkinter import filedialog

# 配置API密钥
GOOGLE_API_KEY = 'xxx'  # 替换成你的API密钥
genai.configure(api_key=GOOGLE_API_KEY)

# 设置代理（根据需要修改代理地址）
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'

def chat_with_video(video_path, prompt):
    print("\n[状态] 正在初始化 Gemini 1.5 Flash 模型...")
    # 定义JSON输出结构
    generation_config = {
        "max_output_tokens": 8192,
        "response_schema": content.Schema(
            type=content.Type.OBJECT,
            properties={
                "response": content.Schema(  # 添加外层 response 字段
                    type=content.Type.OBJECT,
                    properties={
                        "Appearances": content.Schema(
                            type=content.Type.ARRAY,
                            items=content.Schema(
                                type=content.Type.OBJECT,
                                required=["clip", "start", "end", "description"],  # 添加必需字段
                                properties={
                                    "clip": content.Schema(type=content.Type.STRING),
                                    "start": content.Schema(type=content.Type.STRING),
                                    "end": content.Schema(type=content.Type.STRING),
                                    "description": content.Schema(type=content.Type.STRING),
                                }
                            )
                        )
                    }
                )
            }
        ),
        "response_mime_type": "application/json",
    }
    # 初始化Gemini 1.5 Flash模型
    model = genai.GenerativeModel(
       model_name="gemini-1.5-flash",
       generation_config=generation_config
    )
   
    print(f"[状态] 正在上传视频: {video_path}")
    # 使用File API上传视频
    video_file = genai.upload_file(video_path)
    print(f"[状态] 上传视频完成: {video_file.uri}")
   
    print("[状态] 等待视频处理完成...")
    # 等待视频处理完成
    while video_file.state.name == "PROCESSING":
        print('.', end='', flush=True)
        time.sleep(10)
        video_file = genai.get_file(video_file.name)
    print("\n")
   
    if video_file.state.name == "FAILED":
        raise ValueError(f"视频处理失败: {video_file.state.name}")
   
    print("[状态] 正在创建聊天会话...")
    chat = model.start_chat()
   
    # 计算输入的token数量
    input_tokens = model.count_tokens([prompt, video_file])
    print(f"[信息] 输入Token数量: {input_tokens.total_tokens}")
   
    print("[状态] 正在向模型发送请求...")
    print(f"[信息] 提示词: {prompt}")
    try:
        # 发送视频和提示词到模型
        response = chat.send_message(
            [video_file, prompt],
            request_options={"timeout": 600}
        )
   
        # 获取token使用统计
        print(f"[信息] Token统计:")
        print(f"  - 输入Token: {response.usage_metadata.prompt_token_count}")
        print(f"  - 输出Token: {response.usage_metadata.candidates_token_count}")
        print(f"  - 总Token: {response.usage_metadata.total_token_count}")
   
        print("\n[状态] 收到模型响应:")
        print("=" * 50)
        print(response.text)
        print("=" * 50)

        # 保存JSON结果
        output_filename = os.path.splitext(os.path.basename(video_path))[0] + "_analysis.json"
        try:
            # 如果response.text已经是字符串形式的JSON
            if isinstance(response.text, str):
                response_json = json.loads(response.text)
            else:
                # 如果response.text是dict，直接使用
                response_json = response.text
            
            # 提取实际的JSON内容
            if "response" in response_json:
                try:
                    actual_json = json.loads(response_json["response"])
                except:
                    actual_json = response_json["response"]
            else:
                actual_json = response_json
            
            # 确保Appearances列表按clip编号排序
            if "Appearances" in actual_json:
                actual_json["Appearances"].sort(
                    key=lambda x: int(x["clip"].split("_")[1])
                )
            
            # 保存到文件，使用有序字典保持字段顺序
            ordered_json = {
                "Appearances": [
                    {
                        "clip": item["clip"],
                        "start": item["start"],
                        "end": item["end"],
                        "description": item["description"]
                    } for item in actual_json["Appearances"]
                ]
            }
            
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(ordered_json, f, ensure_ascii=False, indent=2)
            print(f"\n[信息] 分析结果已保存到: {output_filename}")
            
        except Exception as e:
            print(f"[错误] JSON处理失败: {str(e)}")
            print(f"[错误] 原始响应: {response.text}")
            raise e
       
        return response.text
       
    except Exception as e:
        print(f"[错误] 请求失败: {str(e)}")
        raise e
   
    # 继续对话
    while True:
        print("\n[状态] 等待输入后续问题 (输入 'q' 退出)...")
        follow_up = input("请输入问题: ")
       
        if follow_up.lower() == 'q':
            print("[状态] 结束对话")
            break
           
        # 计算后续问题的token数量
        follow_up_tokens = model.count_tokens(follow_up)
        print(f"[信息] 输入Token数量: {follow_up_tokens.total_tokens}")
       
        print("[状态] 正在发送后续问题...")
        # 直接发送文本问题，不需要重新发送视频
        try:
            response = chat.send_message(
                follow_up,
                request_options={"timeout": 600}
            )
       
            # 获取token使用统计
            print(f"[信息] Token统计:")
            print(f"  - 输入Token: {response.usage_metadata.prompt_token_count}")
            print(f"  - 输出Token: {response.usage_metadata.candidates_token_count}")
            print(f"  - 总Token: {response.usage_metadata.total_token_count}")
       
            print("\n[状态] 收到模型响应:")
            print("=" * 50)
            print(response.text)
            print("=" * 50)
            # 保存JSON结果
            output_filename = os.path.splitext(os.path.basename(video_path))[0] + "_analysis.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(json.loads(response.text), f, ensure_ascii=False, indent=2)
            print(f"\n[信息] 分析结果已保存到: {output_filename}")
       
            return response.text
       
        except Exception as e:
            print(f"[错误] 请求失败: {str(e)}")
            raise e

def main():
    print("[状态] 程序启动")
    print("[状态] 等待用户选择视频文件...")
    
    # 使用tkinter创建文件选择对话框
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 打开文件选择对话框
    video_path = filedialog.askopenfilename(
        title='选择视频',
        filetypes=[
            ('视频文件', '*.mp4 *.mpeg *.mov *.avi *.flv *.mpg *.webm *.wmv *.3gpp'),
            ('所有文件', '*.*')
        ]
    )
    
    if not os.path.exists(video_path):
        print("[错误] 视频文件不存在，程序退出")
        return
    
    print(f"[信息] 已选择视频: {video_path}")
    
    # 从命令行获取提示词
    print("\n[状态] 等待输入提示词...")
    prompt = input("请输入提示词: ")
    
    try:
        chat_with_video(video_path, prompt)
        print("\n[状态] 程序执行完成")
    except Exception as e:
        print(f"[错误] 程序执行失败: {str(e)}")
    
if __name__ == "__main__":
    main()
