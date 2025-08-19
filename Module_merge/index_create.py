import json
import os
import logging

class SourceFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = {}
        self.source_txt = None
        self.load()

    def load(self):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.source_txt = self.data.pop('source_txt', None)

def build_source_index(source_files):
    index = {}
    for sf in source_files:
        data = sf.data
        for key, val in data.items():
            index[key] = (val, sf)
            subsections = val.get("subsections", {})
            for sub_key, sub_val in subsections.items():
                index[sub_key] = (sub_val, sf)
    return index

def find_source_info_from_index(source_str, index):
    if source_str in index:
        item, sf = index[source_str]
        return {
            "source_name": source_str,
            "start_line": item.get("start_line"),
            "end_line": item.get("end_line"),
            "summary": item.get("summary"),
            "source_txt": sf.source_txt
        }
    else:
        return {
            "source_name": source_str,
            "start_line": None,
            "end_line": None,
            "summary": None,
            "source_txt": None
        }

def enrich_node_source_info(node, index):
    if "source" in node and isinstance(node["source"], list):
        info_list = []
        for src in node["source"]:
            info = find_source_info_from_index(src, index)
            info_list.append(info)
        node["source_info"] = info_list

def traverse_and_enrich(data, index):
    for key, val in data.items():
        if isinstance(val, dict):
            enrich_node_source_info(val, index)
            if "sub_sections" in val:
                for sub_key, sub_val in val["sub_sections"].items():
                    enrich_node_source_info(sub_val, index)

def load_all_source_files(folder_path, exclude_file=None):
    source_files = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.json') and filename != exclude_file:
            fullpath = os.path.join(folder_path, filename)
            sf = SourceFile(fullpath)
            source_files.append(sf)
    return source_files

def enrich_one_folder(folder_path):
    main_json_name = 'restructured_outline.json'
    main_json_path = os.path.join(folder_path, main_json_name)
    if not os.path.isfile(main_json_path):
        logging.warning(f"{main_json_name} not found in {folder_path}, skipping.")
        return

    with open(main_json_path, 'r', encoding='utf-8') as f:
        main_data = json.load(f)

    source_files = load_all_source_files(folder_path, exclude_file=main_json_name)
    index = build_source_index(source_files)
    traverse_and_enrich(main_data, index)

    output_path = os.path.join(folder_path, 'main_enriched.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(main_data, f, ensure_ascii=False, indent=2)
    logging.info(f"Processed folder {folder_path}, output saved to main_enriched.json")

def enrich_all_subfolders(root_folder):
    root_folder = os.path.join(root_folder, 'merging_files')
    for entry in os.listdir(root_folder):
        subfolder = os.path.join(root_folder, entry)
        if os.path.isdir(subfolder):
            enrich_one_folder(subfolder)

if __name__ == "__main__":
    root_folder = 'your_root_folder_path_here'  # 请替换成实际的根目录路径
    enrich_all_subfolders(root_folder)
