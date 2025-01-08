# 分割视频文件为 120s 或 180s 的片段，方便 Gemini 分析时得到准确结果。
# 分割同时还会生成对应的 JSON 文件，方便后续保存对应分析结果。

import subprocess
import os
from datetime import datetime
import json
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import time
import logging

logger = logging.getLogger(__name__)

def get_video_info(input_file):
    """获取视频信息"""
    # ffmpeg_cmd = r'C:\Disk\Software\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe'
    
    # cmd = [ffmpeg_cmd, '-i', str(input_file)]
    cmd = ['ffmpeg', '-i', str(input_file)]
    try:
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
            print("警告：无法从视频中获取时长信息")
            
        return duration
        
    except Exception as e:
        print(f"获取视频信息失败: {str(e)}")
        return 0

def split_video(input_file, segment_duration):
    """分割视频为指定时长的片段"""
    if not os.path.exists(input_file):
        return False, f"输入文件不存在: {input_file}"

    try:
        # 获取视频文件名
        filename = os.path.basename(input_file)
        name, ext = os.path.splitext(filename)
        
        # 创建以视频名命名的主文件夹
        main_folder = os.path.join('outputs', name)
        split_output_dir = os.path.join(main_folder, 'split')
        json_output_dir = os.path.join(main_folder, 'splitjson')
        
        # 确保输出目录存在
        os.makedirs(split_output_dir, exist_ok=True)
        os.makedirs(json_output_dir, exist_ok=True)
        print(f"输出目录已创建/确认：{main_folder}")
        
        print(f"视频输出目录：{split_output_dir}")
        print(f"JSON输出目录：{json_output_dir}")
        
        # ffmpeg_cmd = r'C:\Disk\Software\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe'
        
        # 修改输出文件名格式
        output_pattern = os.path.join(split_output_dir, f'Part%d_{name}.mp4')
        
        cmd = [
            # ffmpeg_cmd,
            'ffmpeg',
            '-i', input_file,
            '-map', '0:v:0',  # 只选择第一个视频流
            '-map', '0:a:0',  # 只选择第一个音频流
            '-c:v', 'copy',   # 复制视频流
            '-c:a', 'copy',   # 复制音频流
            '-f', 'segment',  # 使用分段格式
            '-segment_time', str(segment_duration),
            '-reset_timestamps', '1',
            '-avoid_negative_ts', 'make_zero',  # 避免负时间戳
            '-y',  # 覆盖已存在的文件
            output_pattern
        ]
        
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if process.returncode == 0:
            # 获取所有生成的视频文件
            split_files = [f for f in os.listdir(split_output_dir) 
                         if f.startswith(f'Part') and f.endswith('.mp4') and name in f]
            
            # 为每个视频文件创建对应的JSON文件
            for video_file in split_files:
                json_name = os.path.splitext(video_file)[0] + '.json'
                json_path = os.path.join(json_output_dir, json_name)
                
                # 获取视频时长
                video_full_path = os.path.join(split_output_dir, video_file)
                duration = get_video_info(video_full_path)
                
                # 创建JSON内容
                json_content = {
                    f"{os.path.splitext(video_file)[0]}_time": str(int(duration)),
                    "Appearances": []
                }
                
                # 写入JSON文件
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_content, f, ensure_ascii=False, indent=4)
            
            print(f"成功分割视频为 {len(split_files)} 个片段")
            
            # 计算处理时间
            end_time = time.time()
            total_time = end_time - start_time
            minutes = int(total_time // 60)
            seconds = int(total_time % 60)

            # 直接打印处理结果
            logger.info("=== 视频分割完成 ===")
            logger.info(f"处理耗时：{minutes}分{seconds}秒")
            logger.info(f"输出目录：")
            logger.info(f"视频：outputs/{name}/split")
            logger.info(f"JSON：outputs/{name}/splitjson")
            
            return True
            
        else:
            logger.error(f"分割过程中出现错误: {process.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"分割失败: {str(e)}")
        return False

if __name__ == '__main__':
    # 隐藏主窗口
    Tk().withdraw()
    
    # 弹出文件选择对话框
    input_file = askopenfilename(
        title="选择要分割的视频文件",
        filetypes=[("视频文件", "*.mp4;*.mkv;*.avi;*.mov;*.wmv")]
    )
    
    if not input_file:
        print("未选择文件，程序退出")
        exit(1)

    print(f"选择的文件：{input_file}")

    # 让用户输入分段时长
    while True:
        try:
            segment_duration = float(input("请输入分段时长（秒）[默认120]: ") or "120")
            if segment_duration > 0:
                break
            else:
                print("分段时长必须大于0")
        except ValueError:
            print("请输入有效的数字")

    # 记录开始时间
    start_time = time.time()
    
    # 执行分割
    success = split_video(input_file, segment_duration)
    if success:
        # 显示结果
        print("处理完成")
    else:
        print("视频分割失败，请查看控制台输出了解详细信息")
