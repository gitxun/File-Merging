import logging
import os
from FilePreProcess.utils import load_module_titles


def check_module_files(parent_folder: str, config_path: str = "config.json") -> bool:
    """
    第一次检查：分割模块文件的完整性和正确性。
    检查parent_folder下每个子文件夹中是否包含全部模块对应的txt文件。
    
    1. 获取模块标题列表。
    2. 遍历每个子文件夹：
        - 检查txt文件数量是否和模块数相等。
        - 检查每个模块名是否包含在对应的txt文件名中。
        
    返回True表示所有子文件夹均检查通过，False表示有子文件夹不符合要求。
    """
    module_titles = load_module_titles(config_path)
    all_passed = True

    for entry in os.listdir(parent_folder):
        subfolder_path = os.path.join(parent_folder, entry)
        if os.path.isdir(subfolder_path):
            txt_files = [f for f in os.listdir(subfolder_path) if f.endswith('.txt')]
            
            if len(txt_files) != len(module_titles):
                logging.warning(f"子文件夹 '{entry}' 中txt文件数量 {len(txt_files)} 与模块数量 {len(module_titles)} 不匹配")
                all_passed = False
                continue
            
            for title in module_titles:
                matched_files = [f for f in txt_files if title in f]
                if not matched_files:
                    logging.warning(f"子文件夹 '{entry}' 中未找到包含模块名 '{title}' 的txt文件")
                    all_passed = False

    if all_passed:
        logging.info("所有子文件夹均包含完整且正确的模块txt文件")
    else:
        logging.error("存在子文件夹的模块txt文件不完整或不匹配")

    return all_passed