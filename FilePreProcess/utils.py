# utils.py
import os
import logging
import json
import os
import time
from typing import List
from datetime import datetime

# 预设默认模块标题
DEFAULT_MODULE_TITLES = [
    "研究背景",
    "研究目的",
    "研究内容",
    "关键技术",
    "实施方案"
]

def get_log_file_path(base_dir="log"):
    """
    按照 log/YYYY/MM/DD/run_HHMMSS.log 格式，生成日志文件路径，
    并确保目录存在。
    返回完整日志文件路径字符串。
    """
    now = datetime.now()
    log_dir = os.path.join(base_dir, now.strftime("%Y"), now.strftime("%m"), now.strftime("%d"))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, now.strftime("run_%H_%M_%S.log"))
    return log_file

def setup_logger(log_file=None, console=True):
    """
    设置日志，默认打印到控制台。
    如果传入log_file，则同时保存日志到文件。
    可选参数console控制是否打印到控制台，默认为True。
    """
    handlers = []

    if console:
        handlers.append(logging.StreamHandler())  # 控制台输出

    if log_file:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        handlers.append(file_handler)

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d %(funcName)s()] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )



def clean_old_logs(log_root_dir, days_to_keep=None):
    """
    删除指定目录下的日志文件，并尝试删除空目录。

    :param log_root_dir: 日志根目录，建议传入日志最顶层目录，比如 "logs"
    :param days_to_keep: 保留多少天以内的日志，None表示删除所有日志
    """
    if not os.path.exists(log_root_dir):
        logging.warning(f"{log_root_dir} 不存在，跳过删除日志操作。")
        return

    now = time.time()
    keep_seconds = days_to_keep * 86400 if days_to_keep is not None else None

    deleted_files_count = 0
    for root, dirs, files in os.walk(log_root_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            if not filename.endswith(".log"):
                continue

            try:
                if keep_seconds is None:
                    os.remove(file_path)
                    deleted_files_count += 1
                    logging.debug(f"删除日志文件: {file_path}")
                else:
                    file_mtime = os.path.getmtime(file_path)
                    if (now - file_mtime) > keep_seconds:
                        os.remove(file_path)
                        deleted_files_count += 1
                        logging.debug(f"删除日志文件: {file_path}")
            except Exception as e:
                logging.error(f"删除日志文件失败 {file_path}，错误: {e}")

    logging.info(f"日志文件清理完成，删除文件数量：{deleted_files_count}")

    # 删除空目录，从底层开始删除
    deleted_dirs_count = 0
    for root, dirs, files in os.walk(log_root_dir, topdown=False):
        # 如果目录为空则删除
        if not dirs and not files:
            try:
                os.rmdir(root)
                deleted_dirs_count += 1
                logging.debug(f"删除空目录: {root}")
            except Exception as e:
                logging.warning(f"删除目录失败 {root}，错误: {e}")

    logging.info(f"空目录清理完成，删除目录数量：{deleted_dirs_count}")

def clean_folder_name(name: str) -> str:
    """
    清理文件夹名，去除非法字符，空字符时返回默认名。
    """
    invalid_chars = r'\/:*?"<>|#'
    for ch in invalid_chars:
        name = name.replace(ch, '')
    name = name.strip()
    if not name:
        name = "Unnamed_Project"
    return name


def load_module_titles(config_path: str = "config.json") -> List[str]:
    """
    尝试从指定配置文件加载模块标题列表，失败则返回默认值。
    """
    if not os.path.isfile(config_path):
        # 配置文件不存在，返回默认标题
        print(f"配置文件{config_path}不存在，使用默认模块标题")
        return DEFAULT_MODULE_TITLES

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            titles = config_data.get("module_titles")
            if isinstance(titles, list) and all(isinstance(t, str) for t in titles):
                return titles
            else:
                print(f"配置文件{config_path}中'module_titles'格式不正确，使用默认值")
                return DEFAULT_MODULE_TITLES
    except Exception as e:
        print(f"读取配置文件{config_path}时发生错误: {e}，使用默认值")
        return DEFAULT_MODULE_TITLES