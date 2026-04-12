import ollama
from colorama import init, Fore, Style
from export_chat import save_chat, load_chat
from commands_personality import handle_user_input, SYSTEM_PROMPTS

init(autoreset=True)

MODEL = "qwen2.5:1.5b" 
current_personality = "default"
conversation_history = load_chat()
warmed_up = False

print(f" Model ready: {MODEL}\n")

while True:
    try:
        user_input = input(f"{Fore.CYAN}You: {Style.RESET_ALL}").strip()
    except (EOFError, KeyboardInterrupt):
        break

    if not user_input:
        continue
    if user_input.lower() in ("exit", "quit", "e", "q"):
        print("👋 Goodbye!")
        break

    # Handle slash commands
    if user_input.startswith("/"):
        current_personality, conversation_history = handle_user_input(
            user_input, current_personality, conversation_history
        )
        continue

    # Build context (limit history to save RAM)
    messages = [{"role": "system", "content": SYSTEM_PROMPTS[current_personality]}]
    messages.extend(conversation_history[-12:])
    messages.append({"role": "user", "content": user_input})

    # Warm-up
    if not warmed_up:
        print(Fore.YELLOW + "Warming up model...")
        try:
            ollama.chat(model=MODEL, messages=[{"role": "user", "content": "hi"}])
            warmed_up = True
        except Exception:
            pass

    print(Fore.RED + "\n AI is processing...\n")
    try:
        stream = ollama.chat(
            model=MODEL,
            messages=messages,
            stream=True,
            options={"num_ctx": 4096}
        )

        full_response = ""
        in_thinking = False

        #  REAL-TIME THINKING PARSER
        for chunk in stream:
            content = chunk.message.content
            if not content:
                continue

            # Print live based on state
            if in_thinking:
                print(Fore.CYAN + content, end="", flush=True)
            else:
                print(Fore.WHITE + content, end="", flush=True)

            full_response += content

        print(Style.RESET_ALL + "\n")

        # Save clean response
        clean_response = full_response.replace("<think>", "").replace("</think>", "")
        conversation_history.append({"role": "assistant", "content": clean_response})
        conversation_history = conversation_history[-20:]
        save_chat(user_input, clean_response)

    except Exception as e:
        print(Fore.RED + f"\n Generation failed: {e}")