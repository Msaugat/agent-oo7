from colorama import Fore

SYSTEM_PROMPTS = {
    "default": "You are a helpful assistant.",
    "coder": "You are an expert programmer. Give code with explanations.",
    "teacher": "You are a teacher. Explain simply with examples.",
    "roast": "You are witty and sarcastic but helpful."
}

def handle_user_input(user_input, current_personality="default", conversation_history=None):
    if conversation_history is None:
        conversation_history = []

    if user_input.startswith("/"):
        command_parts = user_input[1:].split()
        command = command_parts[0]

        if command == "save":
            with open("chat_export.md", "w") as f:
                f.write("# Chat Export\n\n")
            print(Fore.GREEN + "Saved to chat_export.md!")
            return current_personality, conversation_history

        elif command == "mode":
            mode = command_parts[1] if len(command_parts) > 1 else "default"
            current_personality = mode if mode in SYSTEM_PROMPTS else "default"
            print(Fore.YELLOW + f"Mode changed to: {current_personality}")
            return current_personality, conversation_history

        elif command == "clear":
            conversation_history = []
            print(Fore.YELLOW + "History cleared!")
            return current_personality, conversation_history

        elif command == "help":
            print(Fore.CYAN + """
Commands:
  /save     - Export chat to markdown
  /mode X   - Change personality (coder/teacher/roast/default)
  /clear    - Clear conversation history
  /calc X   - Quick calculator
  exit      - Quit
            """)
            return current_personality, conversation_history
        
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[current_personality]},
        {"role": "user", "content": user_input}
    ]
    conversation_history.append(messages)
    
    return current_personality, conversation_history, messages

# Example usage:
current_personality = "default"
conversation_history = []

current_personality, conversation_history, messages = handle_user_input("Hello!", current_personality, conversation_history)
print(messages)