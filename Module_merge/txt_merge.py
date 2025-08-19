import os
import re

def merge_merged_txts(root_dir):
    # 获取所有一级子文件夹
    root_dir = os.path.join(root_dir, 'merging_files')
    subfolders = [f for f in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, f))]
    
    # 用正则提取数字和标题
    pattern = re.compile(r'^(\d+)_([\u4e00-\u9fa5_a-zA-Z0-9\s]+)$')
    
    # 过滤出符合命名规则的文件夹，且提取数字和标题
    folders_info = []
    for folder in subfolders:
        match = pattern.match(folder)
        if match:
            index = int(match.group(1))
            title = match.group(2)
            folders_info.append((index, title, folder))
    
    # 按数字排序
    folders_info.sort(key=lambda x: x[0])

    # 输出文件完整路径，文件名固定为merged_all.txt
    output_file_path = os.path.join(root_dir, "merged_all.txt")
    
    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        for index, title, folder in folders_info:
            merged_file_path = os.path.join(root_dir, folder, 'merged.txt')
            if os.path.exists(merged_file_path):
                # 写标题行
                outfile.write(f"#{index} {title}\n")
                # 读取内容并写入
                with open(merged_file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    outfile.write('\n')  # 分隔每个文件内容
    
    print(f"合并完成，输出文件：{output_file_path}")

def merge_all_txts_in_folder(folder_path):
    """
    合并指定文件夹下所有txt文件，按文件名排序合并，输出文件固定为 folder_path/merged_all.txt
    标题格式为 #研究背景，去除数字前缀和扩展名
    """
    txt_files = [f for f in os.listdir(folder_path)
                 if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith('.txt')]
    txt_files.sort()
    output_file_path = os.path.join(folder_path, "merged_all.txt")

    def get_title(filename):
        # 去掉扩展名
        name = os.path.splitext(filename)[0]
        # 去掉开头的数字和下划线，例如 "1_研究背景" → "研究背景"
        # 正则匹配开头数字和下划线
        cleaned = re.sub(r'^\d+[_\-]*', '', name)
        return cleaned

    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        for filename in txt_files:
            if filename == 'merged_all.txt':
                continue
            title = get_title(filename)
            outfile.write(f"#{title}\n")
            filepath = os.path.join(folder_path, filename)
            with open(filepath, 'r', encoding='utf-8') as infile:
                content = infile.read()
                outfile.write(content)
                outfile.write('\n\n')

    print(f"合并完成，输出文件：{output_file_path}")

if __name__ == "__main__":
    root_directory = r"D:\python_workspace\LLM_apply\FileMerge\FilePreProcess\high_words\基于知识图谱的传统机械行业多模态应用项目申请书"  # 请替换为您的文件夹根目录路径
    merge_all_txts_in_folder(root_directory)
