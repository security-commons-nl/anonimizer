"""OpenAI-compatible LLM client — configurable via environment variables."""
import os
import json
import urllib.request
import urllib.error


API_BASE = os.getenv("AI_API_BASE", "https://api.mistral.ai/v1")
API_KEY = os.getenv("AI_API_KEY", "")
MODEL = os.getenv("AI_MODEL_NAME", "mistral-small-latest")


def chat(messages: list[dict], response_format: str = "text") -> str:
    """Send a chat request and return the response content."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.1,
    }
    if response_format == "json":
        payload["response_format"] = {"type": "json_object"}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/chat/completions", data=data, method="POST")
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM API error {e.code}: {body}") from e
