from colorama import Fore

SYSTEM_PROMPTS = {
    "default": "You are a helpful assistant.",
    "coder": "You are an expert programmer. Give code with explanations.",
    "teacher": "You are a teacher. Explain simply with examples.",
    "roast": "You are witty and sarcastic but helpful."
}

def handle_user_input(user_input, current_personality, conversation_history):
    if not user_input.startswith("/"):
        return current_personality, conversation_history

    parts = user_input[1:].strip().split()
    cmd = parts[0].lower()

    if cmd == "save":
        with open("chat_export.md", "w") as f:
            f.write("#Chat Export\n\n")
            for msg in conversation_history:
                role = msg["role"].upper()
                f.write(f"**{role}:** {msg['content']}\n\n")
        print(Fore.GREEN + "Saved full chat to chat_export.md!")
    elif cmd == "mode":
        mode = parts[1] if len(parts) > 1 else "default"
        current_personality = mode if mode in SYSTEM_PROMPTS else "default"
        print(Fore.YELLOW + f" Mode changed to: {current_personality}")
    elif cmd == "clear":
        conversation_history.clear()
        print(Fore.YELLOW + "🗑️ History cleared!")
    elif cmd == "help":
        print(Fore.CYAN + """
Commands:
/save     - Export chat to markdown
/mode X   - Change personality (coder/teacher/roast/default)
/clear    - Clear conversation history
exit      - Quit
""")
    return current_personality, conversation_history 