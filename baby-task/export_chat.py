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
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    
    history.append(entry)
    with open(CHAT_FILE, "w") as f:
        json.dump(history, f, indent=2)


def load_chat():
    try:
        with open(CHAT_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    history = []
    for entry in data:
        user = entry.get("user") or entry.get("user_message")
        ai = entry.get("ai") or entry.get("ai_response")
        if user:
            history.append({"role": "user", "content": user})
        if ai:
            history.append({"role": "assistant", "content": ai})
    return history