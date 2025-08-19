import json
import os
import shutil
import logging

def get_unique_file_path(folder, filename):
    """
    生成文件夹folder内唯一的文件路径，避免名称冲突。
    """
    base_name, ext = os.path.splitext(filename)
    candidate = filename
    count = 1
    while os.path.exists(os.path.join(folder, candidate)):
        candidate = f"{base_name}_{count}{ext}"
        count += 1
    return os.path.join(folder, candidate)

def merge_json_files_with_suffix(base_root):
    src_root = os.path.join(base_root, 'Summary')
    parent_dir = os.path.dirname(src_root.rstrip(os.sep))
    merging_dir = os.path.join(parent_dir, 'merging_files')

    # 新增部分：删除merging_files下的reformat_title和word_files文件夹
    for subfolder in ['reformat_title', 'word_files']:
        folder_to_delete = os.path.join(merging_dir, subfolder)
        if os.path.exists(folder_to_delete) and os.path.isdir(folder_to_delete):
            try:
                shutil.rmtree(folder_to_delete)
                logging.info(f"已删除旧文件夹：{folder_to_delete}")
            except Exception as e:
                logging.error(f"删除文件夹 {folder_to_delete} 失败：{e}")

    subfolders = [f for f in os.listdir(src_root) if os.path.isdir(os.path.join(src_root, f))]
    if not subfolders:
        logging.info("A下面没有子文件夹，程序退出")
        return

    first_folder_path = os.path.join(src_root, subfolders[0])
    json_filenames = [f for f in os.listdir(first_folder_path) if f.endswith('.json')]

    if not json_filenames:
        logging.info(f"第一个子文件夹 {subfolders[0]} 中没有json文件，程序退出")
        return

    # 新增：记录已经存在的目标文件夹，后续跳过
    existing_folders = set()
    for json_name in json_filenames:
        folder_name = os.path.splitext(json_name)[0]
        folder_path = os.path.join(merging_dir, folder_name)
        if os.path.exists(folder_path):
            logging.info(f"目标文件夹 {folder_path} 已存在，跳过该文件夹的复制。")
            existing_folders.add(folder_name)
            continue
        os.makedirs(folder_path, exist_ok=True)

    # 遍历所有子文件夹，将对应json文件复制到对应文件夹，避免同名覆盖
    for folder_name in subfolders:
        folder_path = os.path.join(src_root, folder_name)
        for json_name in json_filenames:
            folder_short_name = os.path.splitext(json_name)[0]
            if folder_short_name in existing_folders:
                # 如果已存在，则跳过
                continue
            src_json_path = os.path.join(folder_path, json_name)
            if os.path.exists(src_json_path):
                target_folder = os.path.join(merging_dir, folder_short_name)  # 目标文件夹
                unique_dst_path = get_unique_file_path(target_folder, json_name)  # 文件名带后缀
                shutil.copy2(src_json_path, unique_dst_path)
                logging.info(f"复制 {src_json_path} 到 {unique_dst_path}")
    
    # 对每个子文件夹执行重命名冲突处理
    rename_all_subfolders_in_merging(merging_dir)
    logging.info(f"所有文件已复制到 {merging_dir}，并处理了重命名冲突。")
    
def rename_duplicate_titles_in_folder(folder):
    """
    对folder下所有json文件，检查一级和二级标题重复情况，给重复标题加编号区分。
    
    修改原文件。
    """

    # 读取所有json数据，存储结构： {filename: json_data}
    json_datas = {}
    for fname in os.listdir(folder):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(folder, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception as e:
                logging.error(f"读取JSON失败 {fpath}: {e}")
                continue
            json_datas[fname] = data

    # --- 统计一级标题出现情况 ---
    # 结构: {一级标题: [ (文件名, 原始标题) ]}
    level1_titles_map = {}
    for fname, data in json_datas.items():
        for key in data.keys():
            if key == "source_txt":
                continue
            level1_titles_map.setdefault(key, []).append(fname)

    # 找出重复的一级标题
    duplicate_level1_titles = {title: files for title, files in level1_titles_map.items() if len(files) > 1}

    # --- 给重复的一级标题加编号 ---
    # 记录每个文件中一级标题的重命名映射，方便二级标题处理
    # {fname: {old_level1_title: new_level1_title}}
    level1_rename_map = {fname: {} for fname in json_datas.keys()}

    for title, files in duplicate_level1_titles.items():
        # 对重复标题编号
        for idx, fname in enumerate(files, start=1):
            new_title = f"{title}({idx})"
            level1_rename_map[fname][title] = new_title

    # --- 统计二级标题重复 ---
    # 结构: {一级标题: {二级标题: [ (文件名) ] } }
    level2_titles_map = {}
    # 用于存储所有文件中二级标题归属（要考虑一级标题是否重命名过）
    for fname, data in json_datas.items():
        rename_map = level1_rename_map.get(fname, {})
        for level1_key, content in data.items():
            if level1_key == "source_txt":
                continue
            # 一级标题可能已重命名
            level1_key_renamed = rename_map.get(level1_key, level1_key)

            subsections = content.get("subsections", {})
            if not subsections:
                continue

            if level1_key_renamed not in level2_titles_map:
                level2_titles_map[level1_key_renamed] = {}

            for level2_key in subsections.keys():
                level2_titles_map[level1_key_renamed].setdefault(level2_key, []).append(fname)

    # 找重复的二级标题
    duplicate_level2_titles = {}
    for level1_key, sub_dict in level2_titles_map.items():
        for level2_key, file_list in sub_dict.items():
            if len(file_list) > 1:
                duplicate_level2_titles.setdefault(level1_key, {})[level2_key] = file_list

    # --- 给重复的二级标题编号 ---
    # 记录每个文件中一级标题下二级标题的重命名映射
    # {fname: {level1_title: {old_level2_title: new_level2_title}}}
    level2_rename_map = {fname: {} for fname in json_datas.keys()}

    for level1_key, duplicates in duplicate_level2_titles.items():
        for level2_title, files in duplicates.items():
            for idx, fname in enumerate(files, start=1):
                if fname not in level2_rename_map:
                    level2_rename_map[fname] = {}
                if level1_key not in level2_rename_map[fname]:
                    level2_rename_map[fname][level1_key] = {}
                new_level2_title = f"{level2_title}({idx})"
                level2_rename_map[fname][level1_key][level2_title] = new_level2_title

    # --- 生成新的json数据，并写回文件 ---
    for fname, data in json_datas.items():
        rename_l1 = level1_rename_map.get(fname, {})
        rename_l2 = level2_rename_map.get(fname, {})

        new_data = {}
        for level1_key, content in data.items():
            if level1_key == "source_txt":
                new_data[level1_key] = content
                continue

            # 一级标题重命名
            new_level1_key = rename_l1.get(level1_key, level1_key)

            # 复制内容
            new_content = content.copy()

            # 处理二级标题重命名
            subsections = content.get("subsections", {})
            if subsections:
                new_subsections = {}
                rename_dict = rename_l2.get(new_level1_key, {})
                for level2_key, level2_val in subsections.items():
                    new_level2_key = rename_dict.get(level2_key, level2_key)
                    new_subsections[new_level2_key] = level2_val
                new_content["subsections"] = new_subsections

            new_data[new_level1_key] = new_content

        # 保存回文件
        fpath = os.path.join(folder, fname)
        try:
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            logging.info(f"已更新文件标题: {fpath}")
        except Exception as e:
            logging.error(f"写文件失败 {fpath}: {e}")

def rename_all_subfolders_in_merging(merging_dir):
    """
    遍历merging_files目录下所有子文件夹，执行重命名冲突处理。
    """
    for subfolder in os.listdir(merging_dir):
        subfolder_path = os.path.join(merging_dir, subfolder)
        if os.path.isdir(subfolder_path):
            logging.info(f"处理子文件夹: {subfolder_path}")
            rename_duplicate_titles_in_folder(subfolder_path)