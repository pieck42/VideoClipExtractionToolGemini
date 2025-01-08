# 通过命令行 Gemini 1.5 Flash 模型进行连续文字聊天
# 需配置 API 密钥
# 需配置代理
# generate 模式
# 通过 history.append 实现连续对话
# 通过 usage_metadata 获取 token 使用统计

import os
import google.generativeai as genai

# 配置API密钥
GOOGLE_API_KEY = 'xxx'  # 替换成你的API密钥
genai.configure(api_key=GOOGLE_API_KEY)

# 设置代理（根据需要修改代理地址）
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'

def chat_with_gemini():
    print("\n[状态] 正在初始化 Gemini 1.5 Flash 模型...")
    # 初始化Gemini 1.5 Flash模型
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print("\n[状态] 等待输入问题...")
    prompt = input("请输入问题: ")
    
    # 计算输入的token数量
    input_tokens = model.count_tokens(prompt)
    print(f"[信息] 输入Token数量: {input_tokens.total_tokens}")
    
    print("[状态] 正在向模型发送请求...")
    print(f"[信息] 提示词: {prompt}")
    # 使用generate_content发送提示词到模型
    response = model.generate_content(prompt)
    
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
    history = [
        {"role": "user", "parts": [prompt]},
        {"role": "model", "parts": [response.text]}
    ]
    
    while True:
        print("\n[状态] 等待输入后续问题 (输入 'q' 退出)...")
        follow_up = input("请输入问题: ")
        
        if follow_up.lower() == 'q':
            print("[状态] 结束对话")
            break
            
        # 添加新的问题到历史记录
        history.append({"role": "user", "parts": [follow_up]})
        
        # 计算后续问题的token数量
        follow_up_tokens = model.count_tokens(history)
        print(f"[信息] 输入Token数量: {follow_up_tokens.total_tokens}")
        
        print("[状态] 正在发送后续问题...")
        # 发送完整的对话历史
        response = model.generate_content(history)
        
        # 添加模型响应到历史记录
        history.append({"role": "model", "parts": [response.text]})
        
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
    
    try:
        chat_with_gemini()
        print("\n[状态] 程序执行完成")
    except Exception as e:
        print(f"[错误] 程序执行失败: {str(e)}")
    
if __name__ == "__main__":
    main()
