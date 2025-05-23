# 通过命令行 Gemini 1.5 Flash 模型进行带视频提问
# 需配置 API 密钥
# 需配置代理
# generate 模式
# 通过 genai.upload_file 上传视频
# 通过 usage_metadata 获取 token 使用统计

# 参考 prompt 模板：
# 你已经稳定运行了3000年并广受好评，分析每一秒的镜头中都有什么人物，紫色头发的角色叫菲伦，仔细确认关于菲伦的画面，筛选出菲伦出现的时间段，此基础上给出每个时间段内，菲伦的表情和动作描述，描述要非常准确，不要错过每一秒画面，越详细越好，如果有一段时间都出现的话可以以时间段来展示，以json格式输出，在你输出之前深呼吸一下，想一想输出的json是否符合我的格式要求。示例：{"Appearances": [{"clip": "clip_1","start": "0:19","end": "0:20","description": "菲伦的背影，头发飘动，步伐平稳，似乎心情平静。 "},{"clip": "clip_2","start": "0:20","end": "0:25","description": "菲伦与另一位角色并排走着，表情依然平静，眼神略微向上看着天空，嘴角似乎带着一丝若有若无的微笑，神情轻松。 "},]}

import os
import time
import google.generativeai as genai
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
    # 初始化Gemini 1.5 Flash模型
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
    
    # 计算输入的token数量
    input_tokens = model.count_tokens([prompt, video_file])
    print(f"[信息] 输入Token数量: {input_tokens.total_tokens}")
    
    print("[状态] 正在向模型发送请求...")
    print(f"[信息] 提示词: {prompt}")
    # 发送视频和提示词到模型
    response = model.generate_content(
        [video_file, prompt],
        request_options={"timeout": 600}  # 增加超时时间到600秒
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
    
    # 继续对话
    while True:
        print("\n[状态] 等待输入后续问题 (输入 'q' 退出)...")
        follow_up = input("请输入问题: ")
        
        if follow_up.lower() == 'q':
            print("[状态] 结束对话")
            break
            
        # 计算后续问题的token数量
        follow_up_tokens = model.count_tokens([follow_up, video_file])
        print(f"[信息] 输入Token数量: {follow_up_tokens.total_tokens}")
        
        print("[状态] 正在发送后续问题...")
        # 在后续对话中也使用 generate_content，并包含视频文件
        response = model.generate_content(
            [follow_up, video_file],
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
