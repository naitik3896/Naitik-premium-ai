import os
import time
import requests
import telebot

TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "facebook/blenderbot-400M-distill")
HF_API = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

# Your 7 channels (public usernames with @)
CHANNELS = [
    "@naitikpromo",
    "@naitikpromo1",
    "@naitikpromo3",
    "@naitikpromo4",
    "@naitikpromo5",
    "@naitikpromo6",
    "@naitikpromo7"
]

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}  # Hugging Face header
bot = telebot.TeleBot(TOKEN, parse_mode=None)

def query_hf(text, timeout=30):
    try:
        payload = {"inputs": text}
        resp = requests.post(HF_API, headers=HEADERS, json=payload, timeout=timeout)
    except Exception as e:
        return f"⚠️ Network error: {e}"

    if resp.status_code == 200:
        try:
            data = resp.json()
        except Exception:
            return "⚠️ Server returned invalid JSON."

        # common response shapes
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]
        elif isinstance(data, list) and len(data) > 0:
            first = data[0]
            if isinstance(first, dict) and "generated_text" in first:
                return first["generated_text"]
            if isinstance(first, str):
                return first
            return str(first)
        else:
            return str(data)
    else:
        return f"⚠️ HF API error {resp.status_code}: {resp.text[:200]}"

def is_user_subscribed(user_id):
    # Check membership for every channel in CHANNELS
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            # get_chat_member may raise if bot not admin/member or channel incorrect
            print(f"Check failed for {channel}: {e}")
            return False
    return True

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    if not is_user_subscribed(msg.from_user.id):
        channels_list = "\n".join(CHANNELS)
        bot.reply_to(msg, f"⚠️ Access denied! Pehle in sabhi channels join karo:\n{channels_list}")
        return
    text = (
        "👋 Welcome! You unlocked *Naitik Premium AI* 🤖\n"
        "Ask me anything — main AI se jawab laake dunga."
    )
    bot.reply_to(msg, text)

@bot.message_handler(commands=['help'])
def cmd_help(msg):
    bot.reply_to(msg, "Bas message bhejo — main AI se reply laake dunga. Agar slow lage to thoda ruk jao (HF processing).")

@bot.message_handler(commands=['model'])
def cmd_model(msg):
    bot.reply_to(msg, f"Current HF model: {HF_MODEL}")

@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_all(msg):
    if not is_user_subscribed(msg.from_user.id):
        channels_list = "\n".join(CHANNELS)
        bot.reply_to(msg, f"⚠️ Pehle in sabhi channels join karo:\n{channels_list}")
        return

    user_text = msg.text.strip()
    if not user_text:
        bot.reply_to(msg, "Kuch likho pehle 😉")
        return

    bot.send_chat_action(msg.chat.id, 'typing')
    reply = query_hf(user_text)
    if len(reply) > 4000:
        reply = reply[:4000] + "\n\n[...truncated]"
    bot.reply_to(msg, reply)

if __name__ == "__main__":
    print("🤖 Naitik Premium AI with 7-channel Lock started...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Bot error:", e)
            time.sleep(5)
