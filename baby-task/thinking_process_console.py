import ollama
from colorama import init, Fore, Style

init(autoreset=True)

model = "qwen3.5"

def thinking_process(query):
    try:
        return str(eval(query))
    except:
        return "Error in calculation"

# Warm-up
print(Fore.YELLOW + "Loading model...")
_ = ollama.chat(model=model, messages=[{"role": "user", "content": "Hello"}])
print("Model loaded and ready!\n")

while True:
    user_input = input("Ask me: ")
    if user_input.lower() in ["exit", "quit", "e", "q"]:
        print("Goodbye!")
        break

    # Calculator detection
    if any(op in user_input for op in ["+", "-", "*", "/"]):
        result = thinking_process(user_input)
        print("Answer:", result)
        continue

    print(Fore.RED + "\nAI is processing...\n")

    # Stream the response to show thinking in real-time
    stream = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": user_input}],
        stream=True,
        think= True,
        options={"num_ctx": 32768}  # Qwen 3.5 supports up to 262K context
    )

    full_response = ""
    thinking_content = ""
    answer_content = ""
    in_thinking = False
    thinking_started = False
    answer_started = False


    # Process the stream
    for chunk in stream:
        if hasattr(chunk.message, 'thinking') and chunk.message.thinking:
            if not in_thinking:
                print(Fore.YELLOW + "_______ Thinking Process:________\n")
                in_thinking = True
            print(Fore.CYAN + chunk.message.thinking, end="", flush=True)
        elif hasattr(chunk.message, 'content') and chunk.message.content:
            if in_thinking:
                print("\n" + "-"*50 + "\n")
                print(Fore.GREEN + "Final Answer:\n")
                in_thinking = False
            print(chunk.message.content, end="", flush=True)

    print("\n")