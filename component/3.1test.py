# 测试 Gemini API 是否能正常通信

import os
import google.generativeai as genai
import json
import requests

# 设置 API 密钥
API_KEY = 'xxx'  # 替换成你的 API 密钥

def test_api_direct():
    """使用 requests 直接测试 API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    data = {
        "contents": [{
            "parts": [{"text": "Explain how AI works"}]
        }]
    }
    
    print("正在测试直接 API 调用...")
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        print("响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"直接 API 调用出错: {str(e)}")

def test_api_library():
    """使用 google.generativeai 库测试 API"""
    print("\n正在测试通过库调用 API...")
    try:
        # 配置 API
        genai.configure(api_key=API_KEY)
        
        # 初始化模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 发送测试请求
        response = model.generate_content("Explain how AI works")
        
        print("响应内容:")
        print(response.text)
    except Exception as e:
        print(f"库调用出错: {str(e)}")

if __name__ == "__main__":
    print("=== Gemini API 测试开始 ===")
    
    # 测试直接 API 调用
    test_api_direct()
    
    # 测试通过库调用
    # test_api_library()
    
    print("\n=== 测试结束 ===")
