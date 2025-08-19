import json
import os
import logging
from SummaryExtract.api_call import chat
from SummaryExtract.format import extract_and_format_content
from tqdm import tqdm

def extract_all_files_content(dir_path):
    all_contents = []
    for filename in os.listdir(dir_path):
        if filename.endswith(".json"):
            file_path = os.path.join(dir_path, filename)
            content = extract_and_format_content(file_path)
            if content.strip():
                all_contents.append(content)  # 只加入内容，不加前缀
    return "\n".join(all_contents)


def restructure_outline_via_llm(dir_path):
    all_content = extract_all_files_content(dir_path)
    # 构造 prompt，明确要求重新组合标题，且说明来源，且禁止复用
    prompt = f"""
            以下是来自不同文档，相同一级标题下的多个二级和三级标题及其摘要信息，格式示例如下：

            请基于这些信息，重新组合形成一个新的大纲，包含新的二级标题和三级标题。  
            要求：
            1. 设计新的二级标题和三级标题。
            2. 明确指出每个新的二级标题和三级标题由哪些原有的二级或三级标题组合而来。
            3. 不要重复使用原有的二级和三级标题，每个标题只能用一次。
            4. 请以清晰的层级结构和合适的格式输出，方便阅读。

            提取内容：\n
            "{all_content}"
            请严格按照以下格式和结构输出：

            1. 用 Markdown 标题表示层级： 
            - 二级标题用 ## 
            - 三级标题用 ### 
            2. 在每个标题下，用括号标注由"标题1"、"标题2"..组合而来，标注需要完整且确保唯一且不重复例如“4. 智能制造支撑技术（由"3.5 智能物流与仓储优化"、"3.6 能源管理与优化"、"3.2 多模态知识表示与应用"组合）”。
            3. 三级标题后面用无序列表列出对应关键点，列表项每行以“- ”开头。
            4. 输出层级清晰，编号规范，方便后续自动化处理和人工阅读。

            请开始重新组合。
            """
    logging.info("完整提示词：\n%s", prompt)
    response = chat(prompt, "structuring")
    logging.info("回答结果：\n%s", response)
    return response


def write_response_to_txt(dir_path, content, filename="restructured_outline.txt"):
    """把response写入指定文件夹下的txt文件"""
    file_path = os.path.join(dir_path, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"写入文件成功：{file_path}")
    except Exception as e:
        logging.error(f"写入文件失败：{file_path}，错误：{e}")


def batch_process_folders(parent_dir):
    """
    批量处理 parent_dir 下的所有子文件夹，
    每个子文件夹调用 restructure_outline_via_llm，并写入txt文件。
    显示进度条。
    如果已存在 restructured_outline.txt 则跳过该子文件夹。
    """
    parent_dir = os.path.join(parent_dir, 'merging_files')
    subfolders = [entry for entry in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, entry))]
    
    for entry in tqdm(subfolders, desc="Processing folders"):
        folder_path = os.path.join(parent_dir, entry)
        output_path = os.path.join(folder_path, 'restructured_outline.txt')
        if os.path.exists(output_path):
            logging.info(f"{output_path} 已存在，跳过该文件夹。")
            continue

        logging.info(f"开始处理文件夹：{folder_path}")
        try:
            response = restructure_outline_via_llm(folder_path)
            write_response_to_txt(folder_path, response)
        except Exception as e:
            logging.error(f"处理文件夹失败：{folder_path}，错误：{e}")


