import os
import json
import re
import logging

from tqdm import tqdm

def load_json_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
    

def extract_and_format_content(file_path):
    data = load_json_file(file_path)
    result_lines = []
    # 遍历二级标题
    for second_level_title, second_level_content in data.items():
        # 过滤确保second_level_content是字典
        if not isinstance(second_level_content, dict):
            # 不符合预期，跳过或打印警告，也可以continue
            continue

        second_summary = second_level_content.get("summary", "")
        line = f"##{second_level_title}：'{second_summary}'"
        result_lines.append(line)
        
        subsections = second_level_content.get("subsections", {})
        if isinstance(subsections, dict):
            for third_level_title, third_level_content in subsections.items():
                # 三级标题内容也应是dict
                if not isinstance(third_level_content, dict):
                    continue
                third_summary = third_level_content.get("summary", "")
                line = f"###{third_level_title}：'{third_summary}'"
                result_lines.append(line)
    
    return "\n".join(result_lines)

def clean_summary(text: str) -> str:
    """
    对文本做格式化处理：
    1. 去除开头直到第一个换行符（包含换行符）之前的内容。
    2. 去除开头的“摘要：”或“摘要”字样。
    """
    if not isinstance(text, str):
        return text
    parts = text.split('\n', 1)
    if len(parts) == 2:
        text = parts[1].lstrip()
    else:
        text = text.lstrip()
    text = re.sub(r'^(摘要：|摘要)', '', text).lstrip()
    return text

def process_json_file(file_path):
    try:
        data = load_json_file(file_path)
    except Exception as e:
        logging.error(f"读取JSON文件失败: {file_path}，错误: {e}")
        return

    changed = False

    for key, val in data.items():
        if isinstance(val, dict):
            # 处理summary字段
            if 'summary' in val and isinstance(val['summary'], str):
                original = val['summary']
                cleaned = clean_summary(original)
                if cleaned != original:
                    val['summary'] = cleaned
                    changed = True
            # 处理overall_summary字段
            if 'overall_summary' in val and isinstance(val['overall_summary'], str):
                original = val['overall_summary']
                cleaned = clean_summary(original)
                if cleaned != original:
                    val['overall_summary'] = cleaned
                    changed = True

    if changed:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"已处理并保存文件: {file_path}")
        except Exception as e:
            logging.error(f"保存JSON文件失败: {file_path}，错误: {e}")

def recursive_process_folder(folder_path):
    summary_folder = os.path.join(folder_path, 'Summary')
    json_files = []

    if not os.path.exists(summary_folder):
        print(f"路径不存在: {summary_folder}")
        return

    for root, dirs, files in os.walk(summary_folder):
        for file in files:
            if file.lower().endswith('.json'):
                full_path = os.path.join(root, file)
                json_files.append(full_path)

    for file_path in tqdm(json_files, desc="JSON文件格式化"):
        process_json_file(file_path)