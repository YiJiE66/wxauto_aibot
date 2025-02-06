import time
from wxauto import WeChat
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from queue import Queue

# API 配置
client = OpenAI(
    api_key="",
    base_url="https://api.siliconflow.cn/v1/"
)
# 硅基流动 API："" //优惠 余额13+
# 硅基流动 API URL：https://api.siliconflow.cn/v1/

# wcode API："" //付费 余额0.3+
# wcode API URL：https://wcode.net/api/gpt/v1/chat/completions

# DS官方API：""
# DS官方API URL：https://api.deepseek.com/v1

# 预设角色信息
file_path = "prompt.md"
with open(file_path, "r", encoding="utf-8") as file:
    SYSTEM_PROMPT = file.read()

conversation_history = {}

wx = WeChat()

executor = ThreadPoolExecutor(max_workers=20)

message_queue = Queue()

def get_deepseek_reply(sender, message):
    if sender not in conversation_history:
        conversation_history[sender] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # 将用户消息添加到对话历史
    conversation_history[sender].append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",  # 使用的模型
            messages=conversation_history[sender]
        )

        assistant_reply = response.choices[0].message.content.strip()

        conversation_history[sender].append({"role": "assistant", "content": assistant_reply})

        return assistant_reply
    except Exception as e:
        print(f"调用 API 错误：{e}")
        return "抱歉，异界有魔物波动(网络不好)，请使者稍后再来。"

def send_reply(sender, content):
    wx.SendMsg(content, sender)
    print(f"已发送消息：'{content}' 给 {sender}")

def reply_message(sender, message_content):
    reply_content = get_deepseek_reply(sender, message_content)
    send_reply(sender, reply_content)

def process_messages():
    while True:
        if not message_queue.empty():
            sender, message_content = message_queue.get()
            executor.submit(reply_message, sender, message_content)
        else:
            time.sleep(0.1)


if __name__ == "__main__":
    # 启动消息处理线程
    import threading
    message_processor = threading.Thread(target=process_messages, daemon=True)
    message_processor.start()

    while True:
        msgs = wx.GetAllNewMessage()
        if msgs:
            print("收到的新消息：", msgs)
            for sender, content_list in msgs.items():

                valid_messages = [content[1] for content in content_list if content[0] not in ("SYS", "Self")]
                if valid_messages:
                    message_content = " ".join(valid_messages)
                    message_queue.put((sender, message_content))

        time.sleep(0.6)