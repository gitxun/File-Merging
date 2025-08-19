import logging
import os
import time

from TxtoWord.format_check import correct_and_convert_numbered_paragraphs
from TxtoWord.txt_to_word import process_and_merge_all_files
from TxtoWord.title_fromat import batch_reformat_titles
from check_format import check_module_files
from Module_merge.txt_merge import merge_merged_txts
from Module_merge.index_create import enrich_all_subfolders
from Module_merge.text_to_json import batch_process_txt_json
from Module_merge.merge_prepare import merge_json_files_with_suffix
from Module_merge.merge import merge_by_folder
from Module_merge.classifier import batch_process_folders
from SummaryExtract.batch_summary_extract import batch_process_json_dir
from SummaryExtract.title_extract import batch_process_txt_files
from SummaryExtract.format import recursive_process_folder
from FilePreProcess.utils import setup_logger, get_log_file_path, clean_old_logs
from FilePreProcess.batch_runner import batch_process_word_files


def process_word_documents(input_dir, output_root, log_root_dir="log", days_to_keep=1,
                           module_config_file="module_config.json", progress_callback=None):
    """
    批量处理Word文档，完成切分、索引提取、摘要、格式化、合并及最终输出Word的全流程。

    :param input_dir: 输入Word文件目录
    :param output_root: 输出的txt及中间文件根目录
    :param log_root_dir: 日志根目录，默认 "log"
    :param days_to_keep: 保留日志天数，默认1天
    :param module_config_file: 模块配置文件路径，默认 "module_config.json"
    """
    total_steps = 12
    current_step = 0
    history = []  # 保存历史步骤耗时
    
    def step_start(step_name):
        # 新增：步骤开始时调用
        if progress_callback:
            progress_callback(
                percent=current_step / total_steps * 100,  # 还没做这个步骤
                current_step_name=step_name,
                current_step_elapsed=0,
                history=history.copy()
            )

    def step_done(step_name, elapsed):
        nonlocal current_step
        current_step += 1
        percent = current_step / total_steps * 100
        logging.info(f"{step_name} 完成，耗时 {elapsed:.2f} 秒，进度 {percent:.1f}%")
        history.append({'name': step_name, 'time': elapsed})

        if progress_callback:
            progress_callback(
                percent=percent,
                current_step_name=step_name,
                current_step_elapsed=elapsed,
                history=history.copy()  # 传副本避免外部修改
            )

    # 设置日志路径并初始化日志
    log_file = get_log_file_path(log_root_dir)
    setup_logger(log_file=log_file, console=False)

    # 清理旧日志
    clean_old_logs(log_root_dir, days_to_keep=days_to_keep)

    # 创建输出目录（如果不存在）
    os.makedirs(output_root, exist_ok=True)

    logging.info("开始批量处理Word文档...")

    # 1. Word文档切分成txt文件
    step_start("文档切分")
    start = time.time()
    batch_process_word_files(input_dir, output_root, module_config_file)
    elapsed = time.time() - start
    step_done("文档切分", elapsed)

    # 2. 检查模块文件完整性
    step_start("检查模块文件")
    start = time.time()
    check_module_files(output_root, module_config_file)
    elapsed = time.time() - start
    step_done("检查模块文件", elapsed)

    # 3. 从txt文档中提取多级标题和对应内容索引
    step_start("提取多级标题")
    start = time.time()
    batch_process_txt_files(output_root)
    elapsed = time.time() - start
    step_done("提取多级标题", elapsed)

    # 4. 对应的json文件中提取摘要
    step_start("提取摘要")
    start = time.time()
    # batch_process_json_dir(output_root)
    elapsed = time.time() - start
    step_done("提取摘要", elapsed)

    # 5. json文件内容格式化
    step_start("格式化JSON文件")
    start = time.time()
    recursive_process_folder(output_root)
    elapsed = time.time() - start
    step_done("格式化JSON文件", elapsed)

    # 6. 准备合并文件预处理
    step_start("合并文件预处理")
    start = time.time()
    merge_json_files_with_suffix(output_root)
    elapsed = time.time() - start
    step_done("合并文件预处理", elapsed)

    # 7. 重新组合标题
    step_start("重组标题")
    start = time.time()
    # batch_process_folders(output_root)
    elapsed = time.time() - start
    step_done("重组标题", elapsed)

    # 8. 重组结果格式化为json
    step_start("结果格式化为JSON")
    start = time.time()
    batch_process_txt_json(output_root)
    elapsed = time.time() - start
    step_done("结果格式化为JSON", elapsed)

    # 9. 生成索引
    step_start("生成索引")
    start = time.time()
    enrich_all_subfolders(output_root)
    elapsed = time.time() - start
    step_done("生成索引", elapsed)

    # 10. 合并json文件
    step_start("合并章节文件")
    start = time.time()
    merge_by_folder(output_root)
    elapsed = time.time() - start
    step_done("合并章节文件", elapsed)

    # 11. 合并所有的merged.txt文件
    step_start("合并所有文件")
    start = time.time()
    # merge_merged_txts(output_root)
    elapsed = time.time() - start
    step_done("合并所有文件", elapsed)

    # 12. 生成最终的合并结果Word文档
    step_start("生成最终Word文档")
    start = time.time()
    # 批量对标题进行格式化，并转换为Word文档
    batch_reformat_titles(output_root)
    # 生成最终的Word文档
    process_and_merge_all_files(output_root)
    result_path = correct_and_convert_numbered_paragraphs(output_root)
    elapsed = time.time() - start
    step_done("生成最终Word文档", elapsed)

    logging.info("批量处理完成！")

    return result_path  # 返回最终文件路径