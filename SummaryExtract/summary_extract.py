import json
import re
from .api_call import chat
from tqdm import tqdm
import logging

def load_json_file(json_filepath: str):
    try:
        with open(json_filepath, "r", encoding="utf-8") as f_json:
            json_data = json.load(f_json)
        if not isinstance(json_data, dict):
            logging.warning(f"JSON文件格式异常，期望字典，实际类型为{type(json_data)}")
            return {}
        return json_data
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析失败：{e}")
        return {}
    except Exception as e:
        logging.error(f"读取JSON文件失败：{e}")
        return {}

def read_text_lines(filepath: str):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            logging.warning(f"文本文件{filepath}为空")
        return lines
    except Exception as e:
        logging.error(f"读取文本文件失败：{e}")
        return []

def extract_text_segment(lines, start_line, end_line):
    """
    根据起止行号提取文本（包含end_line行），行号从1开始
    """
    if not lines:
        return ""
    # 防止越界
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)
    return "".join(lines[start_idx:end_idx])

def build_prompt(section_title: str, content_text: str):
    prompt = f"""
                我将给你一段文本，文本中二级标题用“X.Y”编号格式，如“3.1”，三级标题用“X.Y.Z”编号格式，如“3.1.1”表示层级关系。
                请根据编号区分层级，提取：
                1. 二级标题（{section_title}）整体摘要，约150-200字；
                2. 每个三级标题对应的摘要，约100字。

                请按如下格式输出：

                二级标题摘要：
                <二级标题编号和标题>
                <摘要内容>

                三级标题摘要：
                <三级标题编号和标题>：
                <摘要内容>

                <三级标题编号和标题>：
                <摘要内容>

                ...

                以下是文本内容：
                {content_text}
                """
    return prompt.strip()

def build_simple_section_prompt(section_title: str, content_text: str):
    """
    针对无三级标题的二级标题，构建简易的摘要prompt，约150-200字摘要
    """
    prompt = f"""
    我将给你一段文本，文本内容来自二级标题“{section_title}”对应的章节。
    请根据文本内容生成该二级标题的摘要，长度约150-200字。
    请确保摘要内容准确且涵盖文本核心要点。

    以下是文本内容：
    {content_text}
    """
    return prompt.strip()


def parse_llm_output(output: str):
    result = {
        "section_title": "",
        "section_summary": "",
        "subsections_summary": {}
    }

    try:
        # 尝试提取二级标题摘要
        sec_match = re.search(r"二级标题摘要：\s*(\d+\.\d+ [^\n]+)\n([\s\S]+?)\n{2,}", output)
        if sec_match:
            result["section_title"] = sec_match.group(1).strip()
            result["section_summary"] = sec_match.group(2).strip()
        else:
            # 宽松模式只提取摘要内容
            sec_match2 = re.search(r"二级标题摘要：\s*([\s\S]+?)\n{2,}", output)
            if sec_match2:
                result["section_summary"] = sec_match2.group(1).strip()

        # 提取三级标题摘要（如果有）
        subsec_match = re.search(r"三级标题摘要：([\s\S]+)$", output)
        if subsec_match:
            subsec_text = subsec_match.group(1).strip()
            pattern = r"(\d+\.\d+\.\d+ [^\n：]+)：\s*([\s\S]+?)(?=\n\d+\.\d+\.\d+ [^\n：]+：|\n*$)"
            subs = re.findall(pattern, subsec_text)
            for title, summ in subs:
                result["subsections_summary"][title.strip()] = summ.strip()
    except Exception as e:
        logging.error(f"解析大模型输出失败: {e}")

    return result

def process_json_and_generate_summaries(json_filepath: str):
    json_data = load_json_file(json_filepath)
    if not json_data:
        logging.warning("JSON文件为空或格式错误，无法处理")
        return {}

    text_filepath = json_data.get("source_txt")
    if not text_filepath:
        raise ValueError("JSON中缺少source_txt字段，无法读取文本文件路径")

    text_lines = read_text_lines(text_filepath)
    if not text_lines:
        logging.warning(f"文本文件 {text_filepath} 为空或无法读取，无法生成摘要")
        return json_data

    # 过滤掉source_txt字段，只处理章节部分
    section_keys = [k for k in json_data.keys() if k != "source_txt"]
    if not section_keys:
        logging.warning("JSON中没有章节数据，无法生成摘要")
        return json_data

    for section_key in tqdm(section_keys, desc="处理章节摘要"):
        section_val = json_data[section_key]
        start_line = section_val.get("start_line")
        end_line = section_val.get("end_line")

        if not (isinstance(start_line, int) and isinstance(end_line, int) and start_line > 0 and end_line >= start_line):
            logging.warning(f"章节{section_key}有无效的起止行号：start_line={start_line}, end_line={end_line}")
            section_val["summary"] = ""
            subsections = section_val.get("subsections", {})
            if isinstance(subsections, dict):
                for sub_val in subsections.values():
                    sub_val["summary"] = ""
            continue

        content_text = extract_text_segment(text_lines, start_line, end_line).strip()
        if not content_text:
            logging.warning(f"章节{section_key}提取文本为空，跳过摘要生成")
            section_val["summary"] = ""
            subsections = section_val.get("subsections", {})
            if isinstance(subsections, dict):
                for sub_val in subsections.values():
                    sub_val["summary"] = ""
            continue

        subsections = section_val.get("subsections", {})
        if not subsections or (isinstance(subsections, dict) and len(subsections) == 0):
            # 无三级标题，使用简易prompt摘要整段文本
            prompt = build_simple_section_prompt(section_key, content_text)
            logging.info(f"章节{section_key}无三级标题，开始请求大模型生成整体摘要")
            llm_output = chat(prompt, "summarization")
            logging.info(f"大模型输出（{section_key}无三级标题）：\n{llm_output}")

            # 直接将输出作为summary
            section_val["summary"] = llm_output.strip()
        else:
            # 有三级标题，使用原逻辑
            prompt = build_prompt(section_key, content_text)
            logging.info(f"开始请求大模型处理章节：{section_key}")
            llm_output = chat(prompt, "summarization")
            logging.info(f"大模型输出（{section_key}）：\n{llm_output}")

            parsed = parse_llm_output(llm_output)

            section_val["summary"] = parsed.get("section_summary", "")

            for sub_key, sub_val in subsections.items():
                summary = parsed.get("subsections_summary", {}).get(sub_key, "")
                sub_val["summary"] = summary


    return json_data