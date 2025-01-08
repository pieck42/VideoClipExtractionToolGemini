# 通过命令行 Gemini 1.5 Flash 模型进行带图片提问
# 需配置 API 密钥
# 需配置代理
# generate 模式
# 通过 genai.upload_file 上传图片
# 通过 usage_metadata 获取 token 使用统计

import os
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

def chat_with_image(image_path, prompt):
    print("\n[状态] 正在初始化 Gemini 1.5 Flash 模型...")
    # 初始化Gemini 1.5 Flash模型
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print(f"[状态] 正在上传图片: {image_path}")
    # 使用upload_file上传图片
    image_file = genai.upload_file(image_path)
    print(f"[状态] 上传图片完成: {image_file=}")
    
    # 计算输入的token数量
    input_tokens = model.count_tokens([prompt, image_file])
    print(f"[信息] 输入Token数量: {input_tokens.total_tokens}")
    
    print("[状态] 正在向模型发送请求...")
    print(f"[信息] 提示词: {prompt}")
    # 使用generate_content发送图片和提示词到模型
    response = model.generate_content([prompt, image_file])
    
    # 获取token使用统计
    print(f"[信息] Token统计:")
    print(f"  - 输入Token (prompt_token_count): {response.usage_metadata.prompt_token_count}")
    print(f"  - 输出Token (candidates_token_count): {response.usage_metadata.candidates_token_count}")
    print(f"  - 总Token (total_token_count): {response.usage_metadata.total_token_count}")
    
    print("\n[状态] 收到模型响应:")
    print("=" * 50)
    # 打印响应
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
        follow_up_tokens = model.count_tokens([follow_up, image_file])
        print(f"[信息] 输入Token数量: {follow_up_tokens.total_tokens}")
        
        print("[状态] 正在发送后续问题...")
        response = model.generate_content([follow_up, image_file])
        
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
    print("[状态] 等待用户选择图片...")
    
    # 使用tkinter创建文件选择对话框
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 打开文件选择对话框
    image_path = filedialog.askopenfilename(
        title='选择图片',
        filetypes=[
            ('图片文件', '*.jpg *.jpeg *.png *.webp *.heic *.heif'),
            ('所有文件', '*.*')
        ]
    )
    
    if not image_path:
        print("[错误] 未选择图片，程序退出")
        return
    
    print(f"[信息] 已选择图片: {image_path}")
    
    # 从命令行获取提示词
    print("\n[状态] 等待输入提示词...")
    prompt = input("请输入提示词: ")
    
    try:
        chat_with_image(image_path, prompt)
        print("\n[状态] 程序执行完成")
    except Exception as e:
        print(f"[错误] 程序执行失败: {str(e)}")
    
if __name__ == "__main__":
    main()
