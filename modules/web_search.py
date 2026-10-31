"""
Web Knowledge & Autonomous Research Module (Free, No API Key Required)
Allows J.A.R.V.I.S. to fetch live encyclopedia/web facts via Wikipedia & DuckDuckGo APIs
so it can answer general knowledge questions even before an LLM API key is configured,
and enriches Gemini/Claude prompts with grounded facts.
"""
import re
import requests


def search_web_knowledge(query: str) -> str:
    """Query DuckDuckGo Instant Answer API and Wikipedia REST API for factual grounding."""
    clean_q = re.sub(
        r"^(what is|who is|tell me about|explain|define|how does|search for|jarvis)\s+",
        "",
        query.strip(),
        flags=re.I,
    )
    clean_q = clean_q.rstrip("?.! ").strip()
    if not clean_q or len(clean_q) < 2:
        return ""

    snippets = []

    # 1. DuckDuckGo Instant Answer API (free, no key)
    try:
        ddg_resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": clean_q, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=5,
        )
        if ddg_resp.ok:
            ddg = ddg_resp.json()
            abstract = ddg.get("AbstractText") or ddg.get("Answer") or ""
            if abstract:
                snippets.append(f"[DuckDuckGo Instant Knowledge]: {abstract}")
    except Exception:
        pass

    # 2. Wikipedia Search + Summary API (free, no key)
    try:
        headers = {"User-Agent": "JarvisAIScreen/2.0 (Educational Project)"}
        search_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": clean_q,
                "format": "json",
                "srlimit": 1,
            },
            headers=headers,
            timeout=5,
        )
        if search_resp.ok:
            search_data = search_resp.json()
            hits = search_data.get("query", {}).get("search", [])
            if hits:
                title = hits[0]["title"]
                sum_resp = requests.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}",
                    headers=headers,
                    timeout=5,
                )
                if sum_resp.ok:
                    extract = sum_resp.json().get("extract", "")
                    if extract:
                        snippets.append(f"[Wikipedia — {title}]: {extract}")
    except Exception:
        pass

    return "\n\n".join(snippets)
