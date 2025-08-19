import re

def check_lines_and_prepend(text: str, num: int, mod_name: str) -> str:
    """
    逐行检查字符串中是否存在以数字.数字开头的行，
    如果没有，则在字符串开头插入 'num.1 mod_name\n'。

    参数：
        text (str): 多行字符串
        num (int): 插入的数字部分
        mod_name (str): 插入的名称部分

    返回：
        str: 处理后的字符串
    """
    pattern = r'^\s*\d+\.\d+'
    lines = text.splitlines()

    # 遍历所有行，检查是否有匹配的行
    for line in lines:
        if re.match(pattern, line):
            return text  # 找到符合条件的行，直接返回原字符串

    # 没有符合条件的行，插入字符串
    prefix = f"{num}.1 {mod_name}\n"
    return prefix + text