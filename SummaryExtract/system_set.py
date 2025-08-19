def get_config(task_type):
    if task_type == "summarization":
        return {
            "system_prompt": (
                "你是一个专业的文本摘要助手。"
                "请阅读用户提供的内容，提取核心信息，生成简洁明了的摘要。"
                "摘要应覆盖关键信息，避免添加无关内容，且语言要通顺自然。"
            ),
            "model": "deepseek-chat",
            "temperature": 0.3,
            "max_tokens": 1024,
            "stream": False
        }
    elif task_type == "merging":
        return {
            "system_prompt": (
                "你是一个专业的文本整合助手。"
                "请将用户提供的多段文本内容进行合并，"
                "尽量保留原文内容，保持原文表述风格，但需要去除重复信息，"
                "合并后的内容连贯、逻辑清晰、表达自然。"
            ),
            "model": "deepseek-chat",
            "temperature": 0.5,
            "max_tokens": 8192,
            "stream": False
        }
    elif task_type == "structuring":
        return {
            "system_prompt": (
                "你是一个专业的文本大纲重组助手。"
                "请根据用户提供的内容，分析现有标题及其摘要，"
                "以清晰的结构和层次对文本大纲进行重新组织，方便阅读和后续处理。"
                "结构化后的内容应逻辑严密，表达准确，格式规范。"
            ),
            "model": "deepseek-chat",
            "temperature": 0.2,
            "max_tokens": 8192,
            "stream": False
        }
    else:
        # 默认配置
        return {
            "system_prompt": "你是一个智能文档助手。",
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 4096,
            "stream": False
        }
