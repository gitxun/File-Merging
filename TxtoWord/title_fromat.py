import logging
import os
import pypandoc
from tqdm import tqdm
import re

# Description: 处理标题格式化和转换为Word文档

def reformat_titles(file_path, title_str, output_md_path):
    """
    1. 删除txt文件中所有以```开头的行。
    2. 文件中所有以#开头的行前面再加一个#。
    3. 在文件开头插入一行内容，如 "# 1 研究背景"，然后添加一个空行。
    4. 基于传入字符串开头的数字，对标题进行重新编号（遍历全文）。
    5. 结果输出到指定的md文件。

    :param file_path: 要处理的文件路径
    :param title_str: 类似 "1_研究背景"，数字和标题用下划线或空格分隔
    :param output_md_path: 输出的md文件路径，必须指定
    """

    # 解析传入字符串
    match = re.match(r"(\d+)[_ ](.+)", title_str)
    if not match:
        raise ValueError("title_str格式错误，应为类似 '1_研究背景' 或 '1 研究背景'")
    root_num = match.group(1)
    root_title = match.group(2)

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 删除以```开头的行（去除前后空白判断）
    lines = [line for line in lines if not line.lstrip().startswith('```')]

    # 为所有以#开头的行前加一个#
    def add_extra_hash(line):
        if line.lstrip().startswith('#'):
            prefix_ws = re.match(r'^\s*', line).group(0)
            hashes = re.match(r'^\s*(#+)', line).group(1)
            rest = line.lstrip()[len(hashes):]
            new_hashes = '#' + hashes
            return prefix_ws + new_hashes + rest
        else:
            return line

    lines = [add_extra_hash(line) for line in lines]

    # 在开头插入 "# {root_num} {root_title}" 和一个空行
    insert_title_line = f"# {root_num} {root_title}\n"
    lines.insert(0, insert_title_line)
    lines.insert(1, "\n")

    numbering = [int(root_num)]
    last_level = 1

    def clean_title_text(text):
    # 数字+点，如 1.2.3.
        text = re.sub(r'^\s*(\d+(\.\d+)*\.)\s*', '', text)

        # 括号包数字，如 (1) 、（1）
        text = re.sub(r'^\s*[\(\（](\d+)[\)\）]\s*', '', text)

        # 数字加右括号，如 1) 1）
        text = re.sub(r'^\s*(\d+)[\)\）]\s*', '', text)

        # 纯数字加空格，如 "1 "
        text = re.sub(r'^\s*\d+\s+', '', text)

        return text.lstrip()


    new_lines = []

    for line in lines:
        match = re.match(r'^(\s*)(#+)(\s*)(.*)', line)
        if match:
            prefix_ws, hashes, space_after_hashes, content = match.groups()
            level = len(hashes)

            if level == 1:
                # 一级标题保持传入的编号和标题
                if line.strip() == insert_title_line.strip():
                    new_lines.append(line)
                    numbering = [int(root_num)]
                    last_level = level
                    continue
                else:
                    numbering = [int(root_num)]
                    last_level = level
                    title_text = clean_title_text(content)
                    new_line = f"{prefix_ws}# {root_num} {title_text}\n"
                    new_lines.append(new_line)
                    continue

            if level > last_level:
                for _ in range(level - last_level):
                    numbering.append(1)
            elif level == last_level:
                numbering[-1] += 1
            else:
                for _ in range(last_level - level):
                    numbering.pop()
                numbering[-1] += 1

            last_level = level

            title_text = clean_title_text(content)
            numbering_str = '.'.join(str(num) for num in numbering)

            new_line = f"{prefix_ws}{hashes} {numbering_str} {title_text}\n"
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def md_to_docx(input_md_path, output_docx_path):
    """
    使用pypandoc将Markdown格式的文件转换为Word文档

    :param input_md_path: 输入Markdown文件路径（txt格式，内容为Markdown）
    :param output_docx_path: 输出Word文件路径
    """
    try:
        output = pypandoc.convert_file(input_md_path, 'docx', outputfile=output_docx_path)
        logging.info(f"转换成功，输出文件：{output_docx_path}")
    except Exception as e:
        logging.info(f"转换失败，错误信息：{e}")

def batch_reformat_titles(base_folder):
    """
    只处理以数字开头的子文件夹，进行 reformat_titles 和 md 转 docx
    :param base_folder: 包含merging_files文件夹的基础路径
    """
    merging_path = os.path.join(base_folder, 'merging_files')
    output_md_folder = os.path.join(merging_path, 'reformat_tilte')
    output_docx_folder = os.path.join(merging_path, 'word_files')

    os.makedirs(output_md_folder, exist_ok=True)
    os.makedirs(output_docx_folder, exist_ok=True)

    # 先过滤出所有需要处理的文件夹
    folder_list = [
        name for name in os.listdir(merging_path)
        if os.path.isdir(os.path.join(merging_path, name))
        and name not in ('reformat_tilte', 'word_files')
        and name[0].isdigit()
    ]

    for folder_name in tqdm(folder_list, desc="markdown格式化处理"):
        folder_path = os.path.join(merging_path, folder_name)

        title_str = folder_name
        input_file = os.path.join(folder_path, 'merged.txt')
        if not os.path.isfile(input_file):
            logging.info(f"缺少文件：{input_file}，跳过")
            continue

        output_md_path = os.path.join(output_md_folder, f"{title_str}.md")
        output_docx_path = os.path.join(output_docx_folder, f"{title_str}.docx")

        try:
            # 先执行标题重格式化
            reformat_titles(input_file, title_str, output_md_path)
            logging.info(f"已生成MD文件: {output_md_path}")

            # 再转换为docx
            md_to_docx(output_md_path, output_docx_path)
        except Exception as e:
            logging.info(f"处理文件夹 {folder_name} 时出错：{e}")





if __name__ == "__main__":
    #示例调用：
    batch_reformat_titles('D:\python_workspace\LLM_apply\FileMerge\projects_txt_modules')
    # md_to_docx(r"D:\python_workspace\LLM_apply\FileMerge\TxtoWord\output.md", "test2.docx")