import json
import os
import re
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilenames
from tkinter import messagebox
import logging

# 在文件开头配置 logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def merge_json_files(json_files):
    if not json_files:
        print("❌ 未选择JSON文件")
        return None, "❌ 请先选择JSON文件"
    
    try:
        # 获取原始文件名（从第一个文件名中提取）
        first_file = os.path.basename(json_files[0])
        # 获取Part之后的部分
        base_name = re.sub(r'Part\d+_|\.json$', '', first_file)
        
        # 获取当前时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 构建新的输出文件名
        output_filename = f"{base_name}_all_{timestamp}.json"
        
        # 获取原始文件所在目录
        original_folder_path = os.path.dirname(json_files[0])
        
        # 构建输出路径
        output_path = os.path.join(original_folder_path, output_filename)
        
        # 修改排序逻辑,增加错误处理
        try:
            # 尝试按Part数字排序
            sorted_files = sorted(json_files, 
                key=lambda x: int(re.search(r'Part(\d+)', x).group(1))
            )
        except (AttributeError, ValueError):
            # 如果无法按Part数字排序,就按文件名字母顺序排序
            sorted_files = sorted(json_files)
        
        merged_data = {
            "total_time": 0,
            "part_times": [],
            "Appearances": []
        }
        
        # 遍历所有JSON文件
        for json_file in sorted_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 获取完整的文件名（不含扩展名）
                full_part_name = os.path.splitext(os.path.basename(json_file))[0]
                
                # 使用完整的键名获取时间
                time_key = f"{full_part_name}_time"
                part_time = int(data.get(time_key, 0))
                
                merged_data["part_times"].append({
                    "part": full_part_name,
                    "time": part_time
                })
                merged_data["total_time"] += part_time
                
                # 直接添加 Appearances 数据，无需时间转换
                for appearance in data.get("Appearances", []):
                    merged_data["Appearances"].append(appearance)
        
        # 保存合并后的文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
            
        return output_path, merged_data
        
    except Exception as e:
        print(f"❌ 合并失败: {str(e)}")
        return None, None

if __name__ == '__main__':
    # 隐藏主窗口
    Tk().withdraw()
    
    # 弹出文件选择对话框，允许多选
    json_files = askopenfilenames(
        title="选择要合并的JSON文件（可多选）", 
        filetypes=[("JSON文件", "*.json")]
    )
    
    if not json_files:
        print("未选择文件，程序退出")
        exit(1)

    print(f"选择了 {len(json_files)} 个文件")
    
    # 执行合并
    output_path, merged_data = merge_json_files(json_files)
    
    if output_path and merged_data:
        # 显示结果
        result_message = (
            f"JSON文件合并完成！\n"
            f"总时长：{merged_data['total_time']}秒\n"
            f"总片段数：{len(merged_data['Appearances'])}\n"
            f"输出文件：{output_path}"
        )

        logger.info("JSON文件合并完成！")
        logger.info(f"总时长：{merged_data['total_time']}秒")
        logger.info(f"总片段数：{len(merged_data['Appearances'])}")
        logger.info(f"输出文件：{output_path}")
        messagebox.showinfo("处理完成", result_message)
    else:
        messagebox.showerror("错误", "JSON合并失败，请查看控制台输出了解详细信息")
