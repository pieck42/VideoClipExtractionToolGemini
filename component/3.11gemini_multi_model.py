# 多模态与Gemini交互，使用 gradio 界面
# 需配置 API 密钥
# 需配置代理
# 参考 图片分析 prompt：
# 这个是菲伦，紫色头发的，你需要仔细记住她的人物特征，等下会基于此进行视频分析

# 参考 视频分析 prompt：
# 你已经稳定运行了3000年并广受好评，分析每一秒的镜头中都有什么人物，紫色头发的角色叫菲伦，仔细确认关于菲伦的画面，筛选出菲伦出现的时间段，此基础上给出每个时间段内，菲伦的表情和动作描述，描述要非常准确，不要错过每一秒画面，越详细越好，如果有一段时间都出现的话可以以时间段来展示，以json格式输出，在你输出之前深呼吸一下，想一想输出的json是否符合我的格式要求。示例：{"Appearances": [{"clip": "clip_1","start": "0:19","end": "0:20","description": "菲伦的背影，头发飘动，步伐平稳，似乎心情平静。 "},{"clip": "clip_2","start": "0:20","end": "0:25","description": "菲伦与另一位角色并排走着，表情依然平静，眼神略微向上看着天空，嘴角似乎带着一丝若有若无的微笑，神情轻松。 "},]}

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
import PIL.Image
import base64
import io

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置代理（根据需要修改代理地址）
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'

# 配置API密钥
API_KEY = 'xxx'
genai.configure(api_key=API_KEY)

# 初始化聊天模型
try:
    logger.info("正在初始化 Gemini 模型...")
    # 添加生成配置
    generation_config = {
        "temperature": 1.2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config
    )
    chat = model.start_chat(history=[])
    logger.info("模型初始化成功")
except Exception as e:
    logger.error(f"初始化失败: {str(e)}")
    raise

# 在文件开头添加全局变量
total_session_tokens = 0
stats_history = []

def upload_to_gemini(file, mime_type=None):
    """上传文件到 Gemini"""
    if file is None:
        return None
    
    try:
        # 上传文件
        uploaded_file = genai.upload_file(file, mime_type=mime_type)
        logger.info(f"文件上传成功: {uploaded_file.mime_type}")
        return uploaded_file
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        return None

def wait_for_files_active(files):
    """等待文件处理完成"""
    logger.info("等待文件处理...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            time.sleep(2)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"文件 {file.name} 处理失败")
    logger.info("所有文件处理完成")

def process_chat(message, history, stats, image=None, video=None):
    """处理聊天消息并返回统计信息"""
    global total_session_tokens, stats_history
    try:
        start_time = time.time()
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # 记录问题
        logger.info("==================== 开始新对话 ====================")
        logger.info(f"问题: {message}")
        
        # 准备发送内容
        content = []
        
        # 处理图片
        if image is not None:
            image_file = upload_to_gemini(image, mime_type="image/png")
            if image_file:
                content.append(image_file)
                
        # 处理视频
        if video is not None:
            video_file = upload_to_gemini(video, mime_type="video/mp4")
            if video_file:
                content.append(video_file)
                # 等待视频处理完成
                wait_for_files_active([video_file])
                
        content.append(message)
        
        # 发送消息并获取流式响应
        response = chat.send_message(content, stream=True)
        
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
        if image is not None:
            # 如果有图片，将图片和消息组合在一起
            history.append({
                "role": "user",
                "content": f"<img src='{image}'>\n{message}"
            })
        else:
            history.append({
                "role": "user",
                "content": message
            })
        
        history.append({
            "role": "assistant",
            "content": full_response
        })
        
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

# 修改Gradio界面，添加图片上传功能
with gr.Blocks(title="Gemini AI 聊天助手", theme=gr.themes.Soft()) as iface:
    gr.Markdown("# Gemini AI 聊天助手")
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                height=400,
                type="messages",
                show_copy_button=True,
                bubble_full_width=False
            )
            
            # 添加文件上传组件
            with gr.Row():
                image_upload = gr.Image(
                    label="上传图片（可选）",
                    type="pil",
                    sources=["upload", "clipboard"],
                    height=200
                )
                video_upload = gr.Video(
                    label="上传视频（可选）",
                    sources=["upload"],
                    height=200
                )
            
            msg = gr.Textbox(
                label="输入消息",
                placeholder="在这里输入您的消息...",
                lines=3,
                value="",
                autofocus=True,
                container=True,
                scale=7
            )
            with gr.Row():
                submit = gr.Button("发送", variant="primary")
                clear = gr.Button("清除历史")
                clear_image = gr.Button("清除图片")
        
        with gr.Column(scale=1):
            stats_display = gr.Textbox(
                label="统计信息",
                lines=25,
                interactive=False,
                container=True,    # 使用容器样式
                show_copy_button=True  # 添加复制按钮
            )
    
    # 更新事件处理
    def process_message(message, history, stats, image, video):
        if message.strip() == "":  # 检查消息是否为空
            return history, stats, message, image, video
        new_history, new_stats = process_chat(message, history, stats, image, video)
        return new_history, new_stats, "", None, None  # 清空消息和图片
    
    def clear_image_fn():
        """清除上传的图片"""
        return None
    
    # 设置提交事件
    msg.submit(
        fn=process_message,
        inputs=[msg, chatbot, stats_display, image_upload, video_upload],
        outputs=[chatbot, stats_display, msg, image_upload, video_upload],
        queue=True
    )
    
    # 发送按钮点击事件
    submit.click(
        fn=process_message,
        inputs=[msg, chatbot, stats_display, image_upload, video_upload],
        outputs=[chatbot, stats_display, msg, image_upload, video_upload],
        queue=True
    )
    
    # 清除历史按钮点击事件
    clear.click(
        fn=clear_chat,
        outputs=[chatbot, stats_display],
        queue=True
    )
    
    # 清除图片按钮点击事件
    clear_image.click(
        fn=clear_image_fn,
        outputs=[image_upload],
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
