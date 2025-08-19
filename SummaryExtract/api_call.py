import json
from openai import OpenAI
from .system_set import get_config

def load_api_config(config_file="api_config.json"):
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config["api_key"], config["base_url"]

def chat_with_context():
    api_key, base_url = load_api_config()
    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = [{"role": "system", "content": "你是一个友好的AI助手。"}]

    print("和AI助手开始对话，输入 'quit' 来结束。")

    while True:
        user_input = input("用户：")
        if user_input.strip().lower() == "quit":
            print("对话结束。")
            break

        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )

        ai_reply = response.choices[0].message.content
        print(f"AI助手：{ai_reply}")

        messages.append({"role": "assistant", "content": ai_reply})

def chat_without_context(user_input):
    api_key, base_url = load_api_config()
    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = [
        {"role": "system", "content": "你是一个友好的AI助手。"},
        {"role": "user", "content": user_input}
    ]

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.7,
        max_tokens=4096,
        # stream=True  # 设置为True以启用流式响应
    )

    ai_reply = response.choices[0].message.content
    return ai_reply

def chat(user_input, task_type="default"):
    """"
    task_type: "summarization", "merging", "structuring" 或其他类型
    """
    config = get_config(task_type)
    api_key, base_url = load_api_config()
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    messages = [
        {"role": "system", "content": config.get("system_prompt", "你是一个智能文档助手。")},
        {"role": "user", "content": user_input}
    ]
    
    response = client.chat.completions.create(
        model=config.get("model", "deepseek-chat"),
        messages=messages,
        temperature=config.get("temperature", 0.7),
        max_tokens=config.get("max_tokens", 4096),
        stream=config.get("stream", False)
    )
    
    return response.choices[0].message.content
