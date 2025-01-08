# 从视频中提取片段，并保存到指定目录
# 需选择待提取的原视频文件，以及分析得到时间轴文件

import json
import subprocess
import os
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askopenfilenames
import re

def time_to_seconds(time_str):
    # 将 "分:秒" 格式转换为秒数
    parts = time_str.split(':')
    return int(parts[0]) * 60 + float(parts[1])

def cut_video(input_file, output_dir, timeline_file):
    try:
        # 获取视频文件名
        video_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # 从文件名中提取基础名称和Part编号
        base_name = re.sub(r'^Part\d+_|_compressedPart\d+.*$', '', video_name)
        part_match = re.search(r'Part(\d+)', video_name)
        if not part_match:
            print(f"警告：无法从文件名 {video_name} 中提取Part编号")
            return False
            
        part_number = part_match.group(1)
        
        # 创建主文件夹和提取结果子文件夹
        main_folder = os.path.join('outputs', base_name)
        extract_dir = os.path.join(main_folder, 'extract')
        
        # 检查目录是否存在，如果不存在则创建
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir, exist_ok=True)
            print(f"创建新的提取输出目录：{extract_dir}")
        else:
            print(f"使用已存在的提取输出目录：{extract_dir}")
        
        print(f"视频输出目录：{extract_dir}")
        
        # 读取时间轴文件
        with open(timeline_file, 'r', encoding='utf-8') as f:
            timeline = json.load(f)
        
        # 遍历每个时间段并切割视频
        for i, clip in enumerate(timeline['Appearances']):
            # 计算开始和结束时间，前后各延长1秒
            start_time = max(0, time_to_seconds(clip['start']) - 1)  # 确保不会小于0
            end_time = time_to_seconds(clip['end']) + 1
            duration = end_time - start_time
            
            # 在文件名前添加Part信息
            output_file = os.path.join(extract_dir, f'Part{part_number}_clip_{i+1}.mp4')
            
            print(f'正在处理片段 {i+1}: {clip["start"]} - {clip["end"]} (已扩展前后1秒)')
            # 使用 FFmpeg 切割视频
            command = [
                # r'C:\Disk\Software\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe',
                'ffmpeg',
                '-y',  # 添加 -y 参数，自动覆盖已存在的文件
                '-i', input_file,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c:v', 'libx264',  # 使用 H.264 编码
                '-c:a', 'aac',      # 使用 AAC 音频编码
                output_file
            ]
            
            subprocess.run(command)

        print(f"\n处理完成！")
        
    except Exception as e:
        print(f"处理视频时发生错误: {str(e)}")
        raise  # 重新抛出异常，以便调用者知道发生了错误

if __name__ == '__main__':
    # 隐藏主窗口
    Tk().withdraw()
    
    # 选择视频文件
    input_file = askopenfilename(
        title="选择要切割的视频文件",
        filetypes=[("视频文件", "*.mp4;*.mkv;*.avi;*.mov;*.wmv")]
    )
    
    if not input_file:
        print("未选择视频文件，程序退出")
        exit(1)
        
    # 选择时间轴JSON文件
    timeline_file = askopenfilename(
        title="选择时间轴JSON文件",
        filetypes=[("JSON文件", "*.json")]
    )
    
    if not timeline_file:
        print("未选择JSON文件，程序退出")
        exit(1)
    
    # 创建输出目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    video_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.join("outputs", "final_clips", f"{video_name}_{timestamp}")
    
    print(f"\n开始处理：")
    print(f"输入视频：{input_file}")
    print(f"时间轴文件：{timeline_file}")
    print(f"输出目录：{output_dir}\n")
    
    cut_video(input_file, output_dir, timeline_file)
    
    print(f"\n处理完成！")
    print(f"输出目录：{output_dir}") 