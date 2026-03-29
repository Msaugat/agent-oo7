import json
from datetime import datetime

# Add at the top with your imports
CHAT_FILE = "chat_history.json"

def save_chat(user_msg, ai_response):
    """Save each conversation to a file"""
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user": user_msg,
        "ai": ai_response
    }
    try:
        with open(CHAT_FILE, "r") as f:
            history = json.load(f)
    except:
        history = []
    
    history.append(entry)
    with open(CHAT_FILE, "w") as f:
        json.dump(history, f, indent=2)


def load_chat():
    try:
        with open(CHAT_FILE, "r") as f:
            data = json.load(f)
    except:
        return []

    history = []
    for entry in data:
        if "user" in entry and "ai" in entry:
            user = entry["user"]
            ai = entry["ai"]

        elif "user_message" in entry and "ai_response" in entry:
            user = entry["user_message"]
            ai = entry["ai_response"]

        else:
            continue  # skip broken entries

        if user:
            history.append({"role": "user", "content": user})
        if ai:
            history.append({"role": "assistant", "content": ai})

    return history

    return history