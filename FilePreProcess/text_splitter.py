import re
from typing import Dict, List


def add_numbering_to_titles(module_titles: List[str]) -> List[str]:
    """
    给模块标题加编号，形式支持多种编号样式，这里默认用“数字.”格式。
    """
    numbered_titles = []
    for idx, title in enumerate(module_titles, start=1):
        numbered_title = f"{idx}. {title}"
        numbered_titles.append(numbered_title)
    return numbered_titles


def split_text_by_modules(text: str, module_titles: List[str]) -> Dict[str, str]:
    """
    按模块标题拆分文本，返回字典{模块标题:对应内容}。
    模块标题匹配更灵活：只要单独一行以模块名称结尾（前可有序号、括号等）即可。
    模块标题默认带编号（如 “1. 标题”），若无编号则调用add_numbering_to_titles自动编号。
    """

    if not text:
        return {}

    if not module_titles:
        return {"全文": text.strip()}

    if not re.match(r"^\s*\d+[\.\、\)]?\s+", module_titles[0]):
        module_titles = add_numbering_to_titles(module_titles)

    pattern_parts = []
    for title in module_titles:
        m = re.match(r"^(\d+)([\.\、\)]?)\s*(.+)$", title)
        if m:
            num, sep, mod_name = m.groups()
            # 这里改成匹配：行尾以模块名结尾，模块名前可以有任意字符（非换行）
            # (?:.*)表示任意字符（非换行）多次；\s*允许结尾空格
            # re.escape(mod_name)模块名称转义
            title_pattern = rf"^(?:.*){re.escape(mod_name)}\s*$"
        else:
            title_pattern = rf"^(?:.*){re.escape(title)}\s*$"
        pattern_parts.append(title_pattern)

    titles_pattern = "|".join(pattern_parts)

    lines = text.splitlines()

    module_positions = []

    for idx, line in enumerate(lines):
        if re.match(titles_pattern, line):
            for title in module_titles:
                m = re.match(r"^(\d+)[\.\、\)]?\s*(.+)$", title)
                if m:
                    _, mod_name = m.groups()
                    # 同理匹配结尾模块名
                    if re.match(rf"^(?:.*){re.escape(mod_name)}\s*$", line):
                        module_positions.append((idx, title))
                        break

    if not module_positions:
        return {"全文": text.strip()}

    modules_content = {}
    for i, (start_idx, title) in enumerate(module_positions):
        content_start = start_idx + 1
        content_end = module_positions[i+1][0] if i + 1 < len(module_positions) else len(lines)
        content_lines = lines[content_start:content_end]
        content = "\n".join(content_lines).strip()
        modules_content[title] = content

    return modules_content
