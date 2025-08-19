import logging
import json
import os
import re
from SummaryExtract.api_call import chat
from tqdm import tqdm

def extract_main_title(title):
    return re.sub(r'（.*?）', '', title).strip()

def find_first_level_key(source_name, json_dict):
    source_main = extract_main_title(source_name)
    for key in json_dict.keys():
        key_main = extract_main_title(key)
        if key_main == source_main:
            return key
    for key in json_dict.keys():
        key_main = extract_main_title(key)
        if source_main in key_main or key_main in source_main:
            return key
    return None

def read_text_segment(file_path, start_line, end_line):
    lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for current_line_num, line in enumerate(f, start=1):
            if current_line_num > end_line:
                break
            if current_line_num >= start_line:
                lines.append(line.rstrip('\n'))
    return '\n'.join(lines)

def generate_merge_prompt(title, source_text):
    prompt = (
        f"请根据以下标题和相关原文内容，重新组合成一段符合标题的文本，文本要有多级标题，请尽量保留原文内容和保持原文表述风格。\n\n"
        f"标题：'{title}'\n\n"
        "原文内容：\n'" + source_text + "'\n\n"
    )
    prompt += "\n请将上述内容融合, 不要添加任何额外的内容或解释且按照markdown格式输出"
    return prompt

def process_section(section_key, section_data):
    title = section_data['title']
    source_infos = section_data.get('source_info', [])

    all_source_texts = []
    for src in source_infos:
        txt_path = src.get('source_txt')
        start = src.get('start_line')
        end = src.get('end_line')
        if not txt_path:
            logging.warning(f"source_txt 字段为空，source_info: {src}")
            continue
        segment_text = read_text_segment(txt_path, start, end)
        all_source_texts.append(segment_text)

    full_source_text = "\n".join(all_source_texts)
    prompt = generate_merge_prompt(title, full_source_text)
    logging.info(f"生成的prompt内容（section_key={section_key}，title={title}）：\n{prompt}")

    merged_result = chat(prompt, "merging")
    return merged_result

def process_first_level_section(first_level_key, first_level_val):
    title = first_level_val.get('title', '无标题')
    source_infos = first_level_val.get('source_info', [])

    if not source_infos:
        logging.warning(f"一级标题 {title} 下无可用source_info，跳过处理。")
        return ""

    all_source_texts = []
    for src in source_infos:
        txt_path = src.get('source_txt')
        start = src.get('start_line')
        end = src.get('end_line')
        if not txt_path:
            logging.warning(f"source_txt 字段为空，source_info: {src}")
            continue
        segment_text = read_text_segment(txt_path, start, end)
        all_source_texts.append(segment_text)

    full_source_text = "\n".join(all_source_texts)
    prompt = generate_merge_prompt(title, full_source_text)
    logging.info(f"生成的prompt内容（一级标题Key={first_level_key}，title={title}）：\n{prompt}")

    merged_result = chat(prompt, "merging")
    return merged_result

def merge_by_folder(root_folder):
    json_paths = []
    root_folder = os.path.join(root_folder, 'merging_files')
    for dirpath, _, filenames in os.walk(root_folder):
        if 'main_enriched.json' in filenames:
            json_paths.append(os.path.join(dirpath, 'main_enriched.json'))

    if not json_paths:
        logging.warning(f"在路径 {root_folder} 下未发现任何 main_enriched.json 文件。")
        return

    for json_file_path in tqdm(json_paths, desc="模块文件合并", unit="个"):
        dirpath = os.path.dirname(json_file_path)
        output_path = os.path.join(dirpath, 'merged.txt')  # 先确定输出路径

        # 跳过已合并的模块
        if os.path.exists(output_path):
            logging.info(f"已存在合并文件 {output_path}，跳过该模块。")
            continue

        logging.info(f"处理文件: {json_file_path}")

        with open(json_file_path, 'r', encoding='utf-8') as f_json:
            json_data = json.load(f_json)

        merged_texts = []

        for first_level_key, first_level_val in json_data.items():
            sub_sections = first_level_val.get('sub_sections', {})
            all_sub_empty = True
            for second_level_key, second_level_val in sub_sections.items():
                source_infos = second_level_val.get('source_info', [])
                if source_infos:
                    all_sub_empty = False
                    break

            if all_sub_empty:
                merged_result = process_first_level_section(first_level_key, first_level_val)
                if merged_result:
                    merged_texts.append(merged_result)
            else:
                for second_level_key, second_level_val in sub_sections.items():
                    if second_level_val.get('source_info'):
                        merged_result = process_section(second_level_key, second_level_val)
                        merged_texts.append(merged_result)
                    else:
                        logging.info(f"跳过二级标题 {second_level_key} 因为 source_info 为空。")

        final_merged_text = "\n\n".join(merged_texts)

        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(final_merged_text)
        logging.info(f"合并内容: {final_merged_text}")

        logging.info(f"已生成合并文件：{output_path}")

