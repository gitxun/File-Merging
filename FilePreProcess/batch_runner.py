import os
import logging
from tqdm import tqdm
from .file_processor import process_word_file

def batch_process_word_files(input_dir: str, output_root: str, module_config_file: str):
    if not os.path.isdir(input_dir):
        logging.error(f"输入目录不存在: {input_dir}")
        return

    files = [f for f in os.listdir(input_dir) if f.lower().endswith('.docx')]
    logging.info(f"检测到的Word文件数量: {len(files)}, 文件列表: {files}")

    for file in tqdm(files, desc="预处理文件", unit="个"):
        word_path = os.path.join(input_dir, file)
        logging.info(f"准备处理文件: {word_path}")
        try:
            process_word_file(word_path, output_root, module_config_file)
        except Exception as e:
            logging.error(f"处理文件出错: {word_path}，错误: {e}")

