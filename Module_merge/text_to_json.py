import json
import os
import re
import logging

def read_txt_to_string(filepath):
    """
    读取txt文件内容，返回字符串
    :param filepath: 文件路径
    :return: 文件内容字符串
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


def filter_lines(text):
    """
    过滤字符串，只保留以#或-开头的行，其他行剔除
    :param text: 输入字符串
    :return: 过滤后的字符串
    """
    lines = text.splitlines()
    filtered_lines = [line for line in lines if line.startswith('#') or line.startswith('-')]
    return '\n'.join(filtered_lines)

def clean_text(input_text):
    lines = input_text.splitlines()
    cleaned_lines = []
    for line in lines:
        # 去除行首的#和-符号及其后的空格
        cleaned_line = line.lstrip(' #\-')
        cleaned_lines.append(cleaned_line)
    return '\n'.join(cleaned_lines)

def parse_content(text):
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    
    pattern_level1 = re.compile(r'^(\d+)\.\s+([^(（]+)(?:[（(]由(.+?)组合[)）])?')
    pattern_level2 = re.compile(r'^(\d+\.\d+)\s+([^(（]+)(?:[（(]由(.+?)组合[)）])?')
    
    data = {}
    current_l1 = None
    current_l2 = None
    
    for line in lines:
        m1 = pattern_level1.match(line)
        if m1:
            lvl1_idx = m1.group(1)
            lvl1_title = m1.group(2).strip()
            source_str = m1.group(3)
            sources = []
            if source_str:
                sources = re.findall(r'"([^"]+)"', source_str)
            data[lvl1_idx] = {
                "title": lvl1_title,
                "source": sources,
                "sub_sections": {}
            }
            current_l1 = lvl1_idx
            current_l2 = None
            continue
        
        m2 = pattern_level2.match(line)
        if m2:
            lvl2_idx = m2.group(1)
            lvl2_title = m2.group(2).strip()
            source_str = m2.group(3)
            sources = []
            if source_str:
                sources = re.findall(r'"([^"]+)"', source_str)
            if current_l1 is not None:
                data[current_l1]["sub_sections"][lvl2_idx] = {
                    "title": lvl2_title,
                    "source": sources,
                    "content": []
                }
                current_l2 = lvl2_idx
            continue
        
        if current_l1 is not None and current_l2 is not None:
            data[current_l1]["sub_sections"][current_l2]["content"].append(line)
    
    return data

def write_json(data, filename):
    """
    将Python字典写入JSON文件，保持中文正常显示，格式化缩进。
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"数据成功写入文件: {filename}")

def process_text_to_json(input_filepath: str):
    """
    从输入文本文件读取内容，经过过滤、清洗和解析后，写入与输入文件同名的JSON文件。
    """
    content = read_txt_to_string(input_filepath)
    filtered_content = filter_lines(content)
    cleaned_content = clean_text(filtered_content)
    parsed_content = parse_content(cleaned_content)
    
    base, _ = os.path.splitext(input_filepath)
    output_filepath = base + '.json'
    
    write_json(parsed_content, output_filepath)

def batch_process_txt_json(folder_path: str):
    """
    递归遍历文件夹，处理所有 .txt 文件，调用 process_text_to_json。
    """
    folder_path = os.path.join(folder_path, 'merging_files')
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if filename == 'restructured_outline.txt':
                txt_path = os.path.join(root, filename)
                logging.info(f"Processing file: {txt_path}")
                try:
                    process_text_to_json(txt_path)
                except Exception as e:
                    logging.error(f"处理文件 {txt_path} 时出错: {e}", exc_info=True)

if __name__ == '__main__':
    folder_to_process = r'D:\python_workspace\LLM_apply\FileMerge\Module_merge'
    batch_process_txt_json(folder_to_process)
