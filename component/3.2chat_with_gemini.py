# 通过界面与 Gemini 进行连续文字聊天
# 需配置 API 密钥
# 需配置代理
# 需安装 gradio 库 

import os
import google.generativeai as genai
import gradio as gr
import logging
import time
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import webbrowser
import threading
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置代理（根据需要修改代理地址）
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'

# 配置API密钥
API_KEY = 'xxx'  # 替换成你的 API 密钥
genai.configure(api_key=API_KEY)

# 初始化聊天模型
try:
    logger.info("正在初始化 Gemini 模型...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    chat = model.start_chat(history=[])
    logger.info("模型初始化成功")
except Exception as e:
    logger.error(f"初始化失败: {str(e)}")
    raise

# 在文件开头添加全局变量
total_session_tokens = 0
stats_history = []

def process_chat(message, history, stats):
    """处理聊天消息并返回统计信息"""
    global total_session_tokens, stats_history
    try:
        start_time = time.time()
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # 记录问题
        logger.info("==================== 开始新对话 ====================")
        logger.info(f"问题: {message}")
        
        # 发送消息并获取流式响应
        response = chat.send_message(message, stream=True)
        
        # 收集完整的响应文本
        full_response = ""
        for chunk in response:
            if chunk.text:
                full_response += chunk.text
        
        # 计算响应时间
        end_time = time.time()
        response_time = end_time - start_time
        
        # 获取token统计，添加时间戳
        stats_text = f"[{current_time}] 响应时间: {response_time:.2f}秒\n"
        try:
            # 计算当前问题的token
            prompt_tokens = model.count_tokens(message).total_tokens
            stats_text += f"[{current_time}] 提问消耗tokens: {prompt_tokens}\n"
            
            # 计算回答的token
            response_tokens = model.count_tokens(full_response).total_tokens
            stats_text += f"[{current_time}] 回答消耗tokens: {response_tokens}\n"
            
            # 计算本次对话token
            total_tokens = prompt_tokens + response_tokens
            stats_text += f"[{current_time}] 本次对话消耗tokens: {total_tokens}\n"
            
            # 更新并显示本轮对话总token
            total_session_tokens += total_tokens
            stats_text += f"[{current_time}] 本轮对话总tokens: {total_session_tokens}"
            
        except Exception as e:
            stats_text += f"[{current_time}] Token统计不可用: {str(e)}"
        
        # 添加到历史记录（在开头插入新记录）
        stats_history.insert(0, stats_text)
        # 合并所有历史记录，用双换行分隔
        full_stats = "\n\n".join(stats_history)
        
        logger.info(f"回答: {full_response}")
        logger.info("==================== 对话结束 ====================\n")
        
        # 格式化消息以符合 Gradio chatbot 要求
        history = history or []
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": full_response})
        
        return history, full_stats
    except Exception as e:
        error_msg = f"处理消息时出错: {str(e)}"
        logger.error(error_msg)
        return [], f"错误: {error_msg}"

def clear_chat():
    """清除对话历史"""
    global chat, total_session_tokens, stats_history
    try:
        chat = model.start_chat(history=[])
        total_session_tokens = 0
        stats_history = []  # 清空统计历史
        logger.info("对话历史已清除")
        return [], ""
    except Exception as e:
        error_msg = f"清除历史失败: {str(e)}"
        logger.error(error_msg)
        return [], f"错误: {error_msg}"

# 修改Gradio界面，调整布局比例
with gr.Blocks(title="Gemini AI 聊天助手", theme=gr.themes.Soft()) as iface:
    gr.Markdown("# Gemini AI 聊天助手")
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                height=400,
                type="messages",
                show_copy_button=True,  # 添加复制按钮
                bubble_full_width=False  # 让对话气泡自适应内容宽度
            )
            msg = gr.Textbox(
                label="输入消息",
                placeholder="在这里输入您的消息...",
                lines=3,
                value="",  # 确保初始值为空
                autofocus=True,  # 自动聚焦
                container=True,  # 使用容器样式
                scale=7  # 调整输入框大小
            )
            with gr.Row():
                submit = gr.Button("发送", variant="primary")
                clear = gr.Button("清除历史")
        
        with gr.Column(scale=1):
            stats_display = gr.Textbox(
                label="统计信息",
                lines=25,
                interactive=False,
                container=True,    # 使用容器样式
                show_copy_button=True  # 添加复制按钮
            )
    
    # 更新事件处理
    def process_message(message, history, stats):
        if message.strip() == "":  # 检查消息是否为空
            return history, stats, message
        new_history, new_stats = process_chat(message, history, stats)
        return new_history, new_stats, ""  # 返回空字符串来清空输入框
    
    # 设置提交事件
    msg.submit(
        fn=process_message,
        inputs=[msg, chatbot, stats_display],
        outputs=[chatbot, stats_display, msg],
        queue=True
    )
    
    # 发送按钮点击事件
    submit.click(
        fn=process_message,
        inputs=[msg, chatbot, stats_display],
        outputs=[chatbot, stats_display, msg],
        queue=True
    )
    
    # 清除历史按钮点击事件
    clear.click(
        fn=clear_chat,
        outputs=[chatbot, stats_display],
        queue=True
    )
    
    # 添加快捷键支持
    msg.blur(lambda: None)  # 防止失去焦点
    msg.change(lambda: None)  # 监听输入变化

# 启动应用
if __name__ == "__main__":
    logger.info("正在启动Gradio界面...")
    
    # 创建一个函数来打开浏览器
    def open_browser():
        time.sleep(2)  # 等待2秒确保服务器已启动
        webbrowser.open("http://127.0.0.1:7861")  # 注意这里端口是7861
    
    # 创建一个线程来运行打开浏览器的函数
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 启动 Gradio 应用
    iface.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=False,
        debug=True,
        show_error=True
    )
