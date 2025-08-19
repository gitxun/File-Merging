import re
import json
import os
import logging
from tqdm import tqdm

def extract_title_index_with_lines(txt_filepath, json_filepath=None):
    """
    从txt文件中提取二级和三级标题及对应内容的起止行号，
    生成json文件，json文件名同txt文件名，txt后缀替换为_json.json。

    标题格式示例：
    二级标题：3.1 智能设计与仿真优化
    三级标题：3.1.1 基于生成式对抗网络的智能设计方法

    Args:
        txt_filepath (str): 待解析的txt文件路径

    Returns:
        str: 生成的json文件路径
    """
    # 正则匹配二级和三级标题
    pattern_level2 = re.compile(r'^(\d+\.\d+)\s+(.+)$')
    pattern_level3 = re.compile(r'^(\d+\.\d+\.\d+)\s+(.+)$')

    result = {}
    current_level2 = None
    current_level3 = None

    with open(txt_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        line_num = idx + 1
        line_strip = line.strip()

        # 匹配三级标题优先
        m3 = pattern_level3.match(line_strip)
        if m3:
            title = line_strip
            # 关闭上一三级标题区间
            if current_level3 and current_level2:
                result[current_level2]['subsections'][current_level3]['end_line'] = line_num - 1
            current_level3 = title
            if current_level2 is None:
                # 三级标题前未出现二级标题，容错处理，新建一个默认二级标题
                current_level2 = "Uncategorized"
                if current_level2 not in result:
                    result[current_level2] = {'start_line': 1, 'end_line': None, 'subsections': {}}
            result[current_level2]['subsections'][current_level3] = {'start_line': line_num, 'end_line': None}
            continue

        # 匹配二级标题
        m2 = pattern_level2.match(line_strip)
        if m2:
            title = line_strip
            # 关闭上一三级标题区间
            if current_level3 and current_level2:
                result[current_level2]['subsections'][current_level3]['end_line'] = line_num - 1
                current_level3 = None
            # 关闭上一二级标题区间
            if current_level2:
                result[current_level2]['end_line'] = line_num - 1
            current_level2 = title
            result[current_level2] = {'start_line': line_num, 'end_line': None, 'subsections': {}}
            continue

    # 关闭最后三级和二级标题区间
    total_lines = len(lines)
    if current_level3 and current_level2:
        result[current_level2]['subsections'][current_level3]['end_line'] = total_lines
    if current_level2:
        result[current_level2]['end_line'] = total_lines

    # 在生成json文件名之前，先把txt的绝对路径写入结果
    result["source_txt"] = os.path.abspath(txt_filepath)

    # 生成json文件名，替换后缀
    if json_filepath is None:
        base_name = os.path.splitext(os.path.basename(txt_filepath))[0]
        json_filename = f"{base_name}.json"
        json_filepath = os.path.join(os.path.dirname(txt_filepath), json_filename)

    # 保存json文件
    with open(json_filepath, 'w', encoding='utf-8') as jf:
        json.dump(result, jf, indent=2, ensure_ascii=False)

    logging.info(f"已生成标题索引json文件：{json_filepath}")
    return json_filepath

def batch_process_txt_files(root_dir):
    """
    批量处理root_dir下所有txt文件，
    json放在 root_dir/output/一级子目录/ 目录下，
    不重建更深层目录结构。

    Args:
        root_dir (str): 根目录路径

    Returns:
        None
    """
    root_dir = os.path.abspath(root_dir)
    output_dir = os.path.join(root_dir, 'Title')
    os.makedirs(output_dir, exist_ok=True)
    
    logging.info(f"根目录：{root_dir}")
    logging.info(f"输出目录：{output_dir}")

    # 先收集所有txt文件路径及其所在目录
    txt_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        # 跳过output目录，避免递归处理
        if os.path.abspath(dirpath).startswith(os.path.abspath(output_dir)):
            continue

        for filename in filenames:
            if filename.lower().endswith('.txt'):
                txt_files.append( (dirpath, filename) )

    # 使用tqdm显示进度条
    for dirpath, filename in tqdm(txt_files, desc="多级标题提取", unit="文件"):
        txt_path = os.path.join(dirpath, filename)

        # 计算相对于root_dir的相对路径
        rel_path = os.path.relpath(dirpath, root_dir)
        # 获取一级子目录名
        first_level_folder = rel_path.split(os.sep)[0] if rel_path != '.' else ''

        if first_level_folder == '':
            # 如果txt文件直接放在root_dir目录下，直接放output下根目录
            target_dir = output_dir
        else:
            # json统一放到 output/一级子目录/
            target_dir = os.path.join(output_dir, first_level_folder)

        os.makedirs(target_dir, exist_ok=True)

        base_name = os.path.splitext(filename)[0]
        json_filename = base_name + '.json'
        json_path = os.path.join(target_dir, json_filename)

        # 调用处理函数，传入json输出路径
        extract_title_index_with_lines(txt_path, json_path)

    logging.info("批量处理完成。")