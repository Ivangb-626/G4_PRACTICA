import os
import httpx
import time
import json

def ai_complete(prompt: str) -> str:
    """Try Groq -> GitHub Models -> return empty string."""
    
    # 1. Try Groq
    if os.getenv("GROQ_API_KEY"):
        result = _groq_complete(prompt)
        if result:
            return result

    # 2. Try GitHub Models
    if os.getenv("GITHUB_TOKEN"):
        result = _github_complete(prompt)
        if result:
            return result

    # 3. All failed
    return ""

def _groq_complete(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=data, timeout=20.0)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq error: {e}")
        return ""

def _github_complete(prompt: str) -> str:
    url = "https://models.inference.ai.azure.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    # Retry logic: 3 attempts with exponential backoff
    for attempt in range(3):
        try:
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=data, timeout=20.0)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                print(f"GitHub Models final error: {e}")
        except Exception as e:
            print(f"GitHub Models unexpected error: {e}")
            break
    return ""
