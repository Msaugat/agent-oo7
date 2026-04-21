import ollama
import re
import json
import os
from datetime import datetime
from colorama import init, Fore, Style
from export_chat import save_chat, load_chat
from commands_personality import handle_user_input, SYSTEM_PROMPTS
from web_tools import (
    search_web, should_search_web, format_search_results, 
    scrape_url, discover_targets, ai_extract_structured
)

init(autoreset=True)

MODEL = "qwen2.5:1.5b"
current_personality = "default"
conversation_history = load_chat()
warmed_up = False

def print_banner():
    print(f"{Fore.CYAN}╔════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║      AI Web Research Assistant       ║")
    print(f"{Fore.CYAN}╚════════════════════════════════════════╝")
    print(f"{Fore.GREEN} Model: {MODEL}")
    print(f"{Fore.YELLOW}💡 Commands: /exit, /save, /load, /personality")
    print(f"{Fore.CYAN}────────────────────────────────────────\n")

def select_mode():
    """Interactive mode selection"""
    print(f"\n{Fore.MAGENTA}📋 Select Mode:")
    print(f"{Fore.WHITE}  [1] 💬 Normal AI Chat (Quick answers)")
    print(f"{Fore.WHITE}  [2] 🔍 Deep Web Research (Scrape multiple sites)")
    print(f"{Fore.WHITE}  [3] 🕷️  Targeted Scraping (Specific sites for structured data)")
    print(f"{Fore.CYAN}────────────────────────────────────────")
    
    while True:
        choice = input(f"{Fore.YELLOW}Select (1-3): {Style.RESET_ALL}").strip()
        if choice in ["1", "2", "3"]:
            return int(choice)
        print(f"{Fore.RED}Invalid choice. Please enter 1, 2, or 3.")

def targeted_scrape_mode(query: str):
    """Mode 3: AI suggests sites, user confirms, deep scrape with JSON export"""
    print(f"\n{Fore.MAGENTA} TARGETED SCRAPING MODE")
    print(f"{Fore.BLUE} Analyzing query to discover best targets...")
    
    # Step 1: AI discovers targets
    targets = discover_targets(query, MODEL)
    
    if not targets:
        print(f"{Fore.RED} Could not determine targets. Falling back to search.")
        return False
    
    # Step 2: Show suggestions
    print(f"\n{Fore.GREEN} AI Recommends These Targets:")
    for i, t in enumerate(targets, 1):
        print(f"{Fore.CYAN}  {i}. {t['name']} ({t['url']})")
        print(f"{Fore.WHITE}     Purpose: {t['reason']}")
        print(f"{Fore.YELLOW}     Data to extract: {', '.join(t['data_to_extract'])}")
        print()
    
    # Step 3: User selection
    print(f"{Fore.YELLOW}Options:")
    print(f"  [A] Scrape ALL suggested sites")
    print(f"  [1-{len(targets)}] Select specific site number")
    print(f"  [C] Cancel")
    
    selection = input(f"{Fore.CYAN}Your choice: {Style.RESET_ALL}").strip().lower()
    
    if selection == 'c':
        return False
    elif selection == 'a':
        selected_targets = targets
    else:
        try:
            idx = int(selection) - 1
            selected_targets = [targets[idx]]
        except:
            print(f"{Fore.RED}Invalid selection")
            return False
    
    # Step 4: Scrape and extract
    all_data = []
    print(f"\n{Fore.GREEN} Starting targeted scraping...")
    
    for target in selected_targets:
        url = target.get('search_url') or target['url']
        print(f"\n{Fore.CYAN} Scraping {target['name']}...")
        print(f"{Fore.WHITE}   URL: {url}")
        
        # Scrape
        raw_data = scrape_url(url, max_chars=3000)
        
        if raw_data['status'] == 'failed':
            print(f"{Fore.RED}   ✗ Failed: {raw_data.get('error')}")
            continue
        
        print(f"{Fore.GREEN}    Downloaded {len(raw_data['text'])} chars")
        print(f"{Fore.YELLOW}    Found: {len(raw_data['extracted']['emails'])} emails, "
              f"{len(raw_data['extracted']['phones'])} phones")
        
        # AI extraction
        print(f"{Fore.BLUE}    Extracting structured data with AI...")
        structured = ai_extract_structured(raw_data, query, MODEL)
        
        if structured.get('entries'):
            all_data.extend(structured['entries'])
            print(f"{Fore.GREEN}   ✓ Extracted {len(structured['entries'])} entries")
        else:
            print(f"{Fore.YELLOW}    No structured data extracted")
    
    # Step 5: Export results
    if all_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_data_{timestamp}.json"
        
        output = {
            "query": query,
            "timestamp": timestamp,
            "total_entries": len(all_data),
            "data": all_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n{Fore.GREEN} SUCCESS! Exported {len(all_data)} entries to: {filename}")
        print(f"{Fore.CYAN} Preview of extracted data:")
        for i, entry in enumerate(all_data[:3], 1):
            print(f"{Fore.WHITE}  {i}. {entry.get('title', 'N/A')} | "
                  f"{entry.get('contact_email', 'no email')} | "
                  f"{entry.get('company/organization', 'no company')}")
        
        if len(all_data) > 3:
            print(f"{Fore.WHITE}     ... and {len(all_data) - 3} more entries")
    else:
        print(f"\n{Fore.RED}❌ No data extracted from any site")
    
    return True

def deep_research_mode(query: str):
    """Mode 2: Search, find top results, scrape all, summarize"""
    print(f"\n{Fore.MAGENTA}🔍 DEEP RESEARCH MODE")
    print(f"{Fore.BLUE}🌐 Searching web for: {query}")
    
    results = search_web(query, max_results=5)
    if not results:
        print(f"{Fore.RED}❌ No search results found")
        return False
    
    print(f"{Fore.GREEN}✓ Found {len(results)} sources. Deep scraping...")
    
    all_content = []
    for i, r in enumerate(results, 1):
        print(f"{Fore.YELLOW}  [{i}/{len(results)}] Scraping: {r['url'][:50]}...", end="", flush=True)
        data = scrape_url(r['url'], max_chars=2000)
        
        if data['status'] == 'success':
            print(f"{Fore.GREEN} ✓")
            all_content.append({
                "source": r['title'],
                "url": r['url'],
                "content": data['text']
            })
        else:
            print(f"{Fore.RED} ✗")
    
    if not all_content:
        print(f"{Fore.RED}❌ Could not scrape any sources")
        return False
    
    # Compile for AI
    context = "\n\n".join([f"Source: {c['source']}\n{c['content']}" for c in all_content])
    
    prompt = f"""Based on the following web sources, provide a comprehensive answer to: "{query}"

Sources:
{context[:4000]}

Provide a detailed summary citing sources [Source 1], [Source 2], etc."""
    
    conversation_history.append({"role": "user", "content": prompt})
    return True

def normal_chat_mode(query: str):
    """Mode 1: Standard chat with optional web search"""
    needs_search = should_search_web(query)
    
    if needs_search:
        print(f"\n{Fore.BLUE}🌐 Quick web search enabled...")
        results = search_web(query, max_results=3)
        if results:
            context = format_search_results(results, query)
            query = f"Based on these search results:\n{context}\n\nUser question: {query}"
    
    conversation_history.append({"role": "user", "content": query})
    return True

def generate_response():
    """Generate and stream AI response"""
    global warmed_up
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[current_personality] + 
         "\n\nAlways wrap step-by-step reasoning inside <think> tags."},
        *conversation_history[-15:]
    ]
    
    if not warmed_up:
        print(f"{Fore.YELLOW}  Warming up...")
        try:
            ollama.chat(model=MODEL, messages=[{"role": "user", "content": "hi"}])
            warmed_up = True
        except:
            pass
    
    print(f"\n{Fore.RED}🤖 Thinking...\n")
    
    try:
        stream = ollama.chat(
            model=MODEL,
            messages=messages,
            stream=True,
            options={"num_ctx": 4096, "temperature": 0.7}
        )
        
        full_response = ""
        in_thinking = False
        
        for chunk in stream:
            content = chunk['message']['content']
            if not content:
                continue
            
            if "<think>" in content.lower() and not in_thinking:
                print(Fore.YELLOW + "\n┌─ 🧠 Reasoning ───────────────────────")
                in_thinking = True
                content = content.split("<think>", 1)[1]
                
            if in_thinking:
                if "</think>" in content.lower():
                    parts = content.split("</think>", 1)
                    print(Fore.CYAN + parts[0], end="", flush=True)
                    print(Fore.YELLOW + "\n└──────────────────────────────────────")
                    print(Fore.GREEN + "\n✨ Answer:\n")
                    in_thinking = False
                    content = parts[1] if len(parts) > 1 else ""
                else:
                    print(Fore.CYAN + content, end="", flush=True)
            else:
                print(Fore.WHITE + content, end="", flush=True)
            
            full_response += content
        
        clean = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
        conversation_history.append({"role": "assistant", "content": clean})
        save_chat("", clean)  # Save last exchange
        
    except Exception as e:
        print(f"{Fore.RED}\n Error: {e}")

# ═══════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════
print_banner()

while True:
    try:
        print(f"\n{Fore.CYAN}════════════════════════════════════════")
        user_input = input(f"{Fore.GREEN}💬 Your Query: {Style.RESET_ALL}").strip()
    except (EOFError, KeyboardInterrupt):
        break

    if not user_input:
        continue
        
    if user_input.lower() in ("exit", "quit", "q", "/exit"):
        print(f"{Fore.GREEN}👋 Goodbye!")
        break

    if user_input.startswith("/"):
        current_personality, conversation_history = handle_user_input(
            user_input, current_personality, conversation_history
        )
        continue
    
    # Select mode
    mode = select_mode()
    
    success = False
    if mode == 1:
        success = normal_chat_mode(user_input)
        if success:
            generate_response()
    elif mode == 2:
        success = deep_research_mode(user_input)
        if success:
            generate_response()
    elif mode == 3:
        targeted_scrape_mode(user_input)
        # Mode 3 handles its own output (JSON export)