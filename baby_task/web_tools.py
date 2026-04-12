from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse
import ollama

# Regex patterns for common data extraction
PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    'linkedin': r'linkedin\.com/in/[a-zA-Z0-9-]+',
    'twitter': r'twitter\.com/[a-zA-Z0-9_]+|x\.com/[a-zA-Z0-9_]+'
}

def should_search_web(user_input: str) -> bool:
    """Detect if query needs live data"""
    triggers = [
        "latest", "news", "today", "current", "recent", "2025", "2026",
        "price", "cost", "buy", "review", "vs", "comparison",
        "weather", "stock", "crypto", "exchange rate",
        "jobs", "hiring", "career", "salary", "job",
        "research", "study", "paper", "statistics",
        "how to", "tutorial", "guide", "steps",
        "who is", "what is", "when did", "where is", "why does",
        "contact", "email", "phone", "reach"
    ]
    user_lower = user_input.lower()
    return any(trigger in user_lower for trigger in triggers)

def discover_targets(query: str, model: str = "qwen2.5:1.5b") -> list:
    """
    Use AI to discover which websites to scrape based on query intent.
    Returns list of suggested sites with reasons.
    """
    prompt = f"""Given this user query: "{query}"

Analyze what type of information they need and suggest the TOP 3-5 best websites to scrape for this data.
For each site, provide: name, base URL, and what specific data to extract there.

Respond ONLY in this JSON format:
{{
    "targets": [
        {{
            "name": "Site Name",
            "url": "https://example.com",
            "search_url": "https://example.com/search?q={query.replace(' ', '+')}",
            "data_to_extract": ["job titles", "company names", "emails", etc],
            "reason": "why this site"
        }}
    ]
}}

Query: {query}"""

    try:
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        content = response['message']['content']
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get('targets', [])
        return []
    except Exception as e:
        print(f"⚠️ Target discovery failed: {e}")
        return []

def search_web(query: str, max_results: int = 5) -> list:
    """Search and return results"""
    try:
        with ddgs() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            return [
                {
                    "title": r.get("title", "No title"),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "No description"))
                }
                for r in results
            ]
    except Exception as e:
        print(f"⚠️ Search failed: {e}")
        return []

def scrape_url(url: str, max_chars: int = 2000) -> dict:
    """
    Enhanced scraping with metadata and structured extraction preparation.
    Returns dict with raw_html, text, and metadata.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
            tag.decompose()
        
        # Extract specific areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article|body'))
        
        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)
        
        # Clean text
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        
        # Extract all potential data points
        extracted = {
            'emails': list(set(re.findall(PATTERNS['email'], text))),
            'phones': list(set(re.findall(PATTERNS['phone'], text))),
            'linkedin': list(set(re.findall(PATTERNS['linkedin'], text))),
            'twitter': list(set(re.findall(PATTERNS['twitter'], text)))
        }
        
        return {
            'url': url,
            'domain': urlparse(url).netloc,
            'title': soup.find('title').get_text() if soup.find('title') else 'No title',
            'text': text[:max_chars] + ("..." if len(text) > max_chars else ""),
            'full_html': str(soup)[:5000],  # Keep some HTML for AI parsing
            'extracted': extracted,
            'status': 'success'
        }
    except Exception as e:
        return {
            'url': url,
            'domain': urlparse(url).netloc,
            'error': str(e),
            'status': 'failed'
        }

def ai_extract_structured(raw_data: dict, query: str, model: str = "qwen2.5:1.5b") -> dict:
    """
    Use AI to extract structured data from scraped content.
    Returns clean JSON with relevant fields only.
    """
    prompt = f"""Extract structured information from this web content based on the user query: "{query}"

Content from {raw_data['url']}:
Title: {raw_data['title']}
Text: {raw_data['text'][:1500]}

Already found: {json.dumps(raw_data['extracted'])}

Extract relevant information in this JSON format:
{{
    "relevance_score": 1-10,
    "entries": [
        {{
            "title": "job title/article title/etc",
            "company/organization": "name",
            "contact_email": "email if found",
            "contact_phone": "phone if found",
            "location": "location if relevant",
            "description": "brief summary",
            "source_url": "{raw_data['url']}"
        }}
    ],
    "summary": "brief summary of what was found"
}}

Return ONLY the JSON, no other text."""

    try:
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        content = response['message']['content']
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"entries": [], "error": "Failed to parse AI response"}
    except Exception as e:
        return {"entries": [], "error": str(e)}

def format_search_results(results: list, topic_hint: str = "") -> str:
    """Format for LLM context"""
    if not results:
        return "⚠️ No search results found."
    
    lines = [f"🔍 SEARCH RESULTS FOR: {topic_hint or 'User Query'}\n" + "="*60]
    for i, r in enumerate(results, 1):
        lines.append(f"\n#{i}. {r['title']}")
        lines.append(f"    URL: {r['url']}")
        lines.append(f"    {r['snippet']}")
        lines.append("-" * 60)
    return "\n".join(lines)