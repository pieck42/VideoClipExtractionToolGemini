# 压缩视频文件

import subprocess
import os
import math
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilenames
from tkinter import messagebox
import re
import sys
import winsound

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

def compress_video(input_file, output_file, target_size_mb=200, remove_audio=False):
    """压缩视频到指定大小"""
    if not os.path.exists(input_file):
        print(f"输入文件不存在: {input_file}")
        return False

    # 获取视频时长
    duration = get_video_info(input_file)
    if duration == 0:
        print("无法获取视频时长")
        return False

    # 计算目标比特率（根据是否保留音频调整）
    target_size_bits = target_size_mb * 8 * 1024 * 1024
    audio_bitrate = 128 * 1024 if not remove_audio else 0  # 128kbps for audio
    video_bitrate = int((target_size_bits / duration) - audio_bitrate)

    if video_bitrate < 100 * 1024:
        print("警告：计算出的视频比特率太低，可能会严重影响视频质量")
        video_bitrate = 100 * 1024

    print(f"目标视频比特率：{video_bitrate/1024:.2f}k")
    if remove_audio:
        print("音频：已移除")
    else:
        print("音频：保留")

    # cmd = [
    #     r'C:\Disk\Software\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe',
    #     '-i', input_file,
    # ]
    cmd = ['ffmpeg', '-i', input_file]
    
    if remove_audio:
        cmd.append('-an')  # 只在需要时移除音频
    
    cmd.extend([
        '-c:v', 'libx264',    # 视频编码器
        '-b:v', f'{video_bitrate}',  # 视频比特率
        '-preset', 'medium',   # 编码速度预设
        '-y',                  # 覆盖输出文件
    ])

    if not remove_audio:
        cmd.extend([
            '-c:a', 'aac',     # 音频编码器
            '-b:a', '128k'     # 音频比特率
        ])

    cmd.append(output_file)

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        # 等待进程完成
        process.communicate()

        if process.returncode == 0:
            print(f"压缩完成！输出文件：{output_file}")
            return True
        else:
            print("压缩过程中出现错误")
            return False
            
    except Exception as e:
        print(f"压缩失败: {str(e)}")
        return False

if __name__ == '__main__':
    # 创建主窗口
    root = Tk()
    
    # 设置窗口标题
    root.title("视频压缩工具")
    
    # 设置窗口大小为最小化
    root.iconify()
    
    # 保持主窗口在其他窗口之上
    root.attributes('-topmost', True)
    
    # 弹出文件选择对话框，允许多选
    input_files = askopenfilenames(
        title="选择要压缩的视频文件（可多选）", 
        filetypes=[("视频文件", "*.mp4;*.mkv;*.avi;*.mov;*.wmv")]
    )
    
    if not input_files:
        print("未选择文件，程序退出")
        exit(1)

    print(f"选择了 {len(input_files)} 个文件")

    # 让用户输入目标大小
    while True:
        try:
            target_size = float(input("请输入目标文件大小（MB）[默认50]: ") or "50")
            if target_size > 0:
                break
            else:
                print("文件大小必须大于0")
        except ValueError:
            print("请输入有效的数字")

    # 询问是否移除音频
    remove_audio_input = input("是否移除音频？(y/n) [默认n]: ") or 'n'
    remove_audio = remove_audio_input.lower() == 'y'

    # 初始化计数器
    success_count = 0
    fail_count = 0
    total_start_time = time.time()  # 添加总计时器

    # 处理所有选中的文件
    for input_file in input_files:
        video_name = os.path.splitext(os.path.basename(input_file))[0]
        base_name = re.sub(r'^Part\d+_|_compressedPart\d+.*$', '', video_name)
        
        # 创建输出目录结构
        output_dirs = {
            'main': os.path.join('outputs', base_name),
            'compressed': os.path.join('outputs', base_name, 'compressed')
        }

        # 创建所有必要的目录
        for dir_name, dir_path in output_dirs.items():
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"创建新的{dir_name}目录：{dir_path}")
            else:
                print(f"使用已存在的{dir_name}目录：{dir_path}")

        # 生成输出文件名
        filename = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dirs['compressed'], f"{filename}_compressed.mp4")
        
        print(f"输出文件：{output_file}")
        print(f"目标大小：{target_size}MB\n")
        
        file_start_time = time.time()
        if compress_video(input_file, output_file, target_size, remove_audio):
            success_count += 1
        else:
            fail_count += 1
            
        # 显示单个文件处理时间
        file_elapsed_time = time.time() - file_start_time
        print(f"本文件处理耗时：{int(file_elapsed_time//60)}分{int(file_elapsed_time%60)}秒\n")

    # 将这些代码移到循环外部
    # 计算总耗时
    total_elapsed_time = time.time() - total_start_time
    total_minutes = int(total_elapsed_time // 60)
    total_seconds = int(total_elapsed_time % 60)
    
    # 显示最终结果
    result_message = (
        f"批量处理完成！\n"
        f"成功：{success_count} 个\n"
        f"失败：{fail_count} 个\n"
        f"总耗时：{total_minutes}分{total_seconds}秒\n"
        f"输出目录：{output_file}"
    )
    
    # 使用 -1 作为默认的系统提示音
    winsound.MessageBeep(-1)
    root.attributes('-topmost', True)
    messagebox.showinfo("处理完成", result_message)
    root.destroy()
    sys.exit(0)
