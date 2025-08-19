import os
import logging
from utils import setup_logger,get_log_file_path,clean_old_logs
from batch_runner import batch_process_word_files

def main():
    log_file = get_log_file_path("log")  # 生成符合年月日目录结构的日志文件路径
    setup_logger(log_file=log_file, console=False)  # 设置日志，保存到文件并控制是否打印到控制台
    # 先清理日志，示例保留最近7天的日志，删除更早的
    log_root_dir = "log"  # 日志根目录
    clean_old_logs(log_root_dir, days_to_keep=0)

    input_dir = r"D:\python_workspace\LLM_apply\projects_word_files"  # Windows路径用raw string
    output_root = "test_projects_txt_modules"
    os.makedirs(output_root, exist_ok=True)

    logging.info("开始批量处理Word文档...")
    batch_process_word_files(input_dir, output_root)
    logging.info("所有文档切分完成！")

if __name__ == "__main__":
    main()
