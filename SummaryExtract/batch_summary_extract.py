import os
import json
import logging
from .summary_extract import process_json_and_generate_summaries
from tqdm import tqdm

def batch_process_json_dir(base_dir: str):
    """
    基于以下目录结构批量处理JSON文件：
    base_dir/
        Title/
            子文件夹1/
                若干json文件
            子文件夹2/
                若干json文件
        处理结果保存到
        base_dir/Summary/
            子文件夹1/
                处理后的json文件
            子文件夹2/
                处理后的json文件

    Args:
        base_dir (str): 根目录路径，例如：
                        D:\python_workspace\LLM_apply\FileMerge\SummaryExtract\high_words

    Returns:
        None
    """
    title_dir = os.path.join(base_dir, "Title")
    summary_dir = os.path.join(base_dir, "Summary")

    if not os.path.exists(title_dir):
        logging.error(f"Title目录不存在: {title_dir}")
        return

    os.makedirs(summary_dir, exist_ok=True)

    subfolders = [f for f in os.listdir(title_dir) if os.path.isdir(os.path.join(title_dir, f))]

    # 遍历子文件夹，添加进度条
    for subfolder_name in tqdm(subfolders, desc="处理子文件夹"):
        subfolder_path = os.path.join(title_dir, subfolder_name)

        output_subfolder_path = os.path.join(summary_dir, subfolder_name)
        os.makedirs(output_subfolder_path, exist_ok=True)

        # 只保留json文件
        json_files = [f for f in os.listdir(subfolder_path) if f.endswith(".json")]

        # 遍历该子文件夹中的json文件，添加进度条
        for file_name in tqdm(json_files, desc=f"处理{subfolder_name}中的文件", leave=False):
            input_json_path = os.path.join(subfolder_path, file_name)
            output_json_path = os.path.join(output_subfolder_path, file_name)

            try:
                processed_json = process_json_and_generate_summaries(input_json_path)

                if processed_json:
                    with open(output_json_path, "w", encoding="utf-8") as f_out:
                        json.dump(processed_json, f_out, ensure_ascii=False, indent=2)
                    logging.info(f"已处理并保存: {output_json_path}")
                else:
                    logging.warning(f"处理结果为空，跳过保存: {input_json_path}")

            except Exception as e:
                logging.error(f"处理文件失败: {input_json_path}，异常: {e}")
