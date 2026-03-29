import json
from datetime import datetime

# Add at the top with your imports
CHAT_FILE = "chat_history.json"

def save_chat(user_msg, ai_response):
    """Save each conversation to a file"""
    print("ai response ------------->",ai_response)
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