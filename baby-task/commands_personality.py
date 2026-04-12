from colorama import Fore

SYSTEM_PROMPTS = {
    "default": "You are a helpful assistant. Always wrap your step-by-step reasoning inside <think> and </think> tags.",
    "coder": "You are an expert programmer. Think through the logic in <think> tags, then provide clean code.",
    "teacher": "You are a teacher. Explain simply with examples using <think> tags for your breakdown.",
    "roast": "You are witty and sarcastic. Plan your response in <think> tags, then deliver it."
}

def handle_user_input(user_input, current_personality="default", conversation_history=None):
    if conversation_history is None:
        conversation_history = []
        
    if not user_input.startswith("/"):
        return current_personality, conversation_history

    command_parts = user_input[1:].strip().split()
    command = command_parts[0].lower()

    if command == "save":
        with open("chat_export.md", "w") as f:
            f.write("#  Chat Export\n\n")
            for msg in conversation_history:
                f.write(f"**{msg['role'].upper()}:** {msg['content']}\n\n")
        print(Fore.GREEN + " Saved to chat_export.md!")
    elif command == "mode":
        mode = command_parts[1] if len(command_parts) > 1 else "default"
        current_personality = mode if mode in SYSTEM_PROMPTS else "default"
        print(Fore.YELLOW + f" Mode changed to: {current_personality}")
    elif command == "clear":
        conversation_history.clear()
        print(Fore.YELLOW + "🗑️ History cleared!")
    elif command == "help":
        print(Fore.CYAN + """
Commands:
/save     - Export chat to markdown
/mode X   - Change personality
/clear    - Clear conversation history
exit      - Quit
""")
    return current_personality, conversation_history