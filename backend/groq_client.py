"""
Shared Groq LLM client for the Agentic GraphRAG Olympic Benchmark.

Model: openai/gpt-oss-120b (via Groq API)
Features:
- Robust rate-limit (HTTP 429) handling with Retry-After header detection,
  JSON error message parsing, and bounded exponential backoff.
- Transient server error (HTTP 5xx) handling.
- Rich metadata extraction: prompt_tokens, completion_tokens, total_tokens, latency, model.
- Backward-compatible `groq_generate` API for existing callers.
"""

import os
import re
import time
import requests
from dotenv import load_dotenv

# Ensure environment is loaded
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = os.getenv("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")


def groq_generate_with_metadata(
    prompt,
    temperature=0,
    max_retries=4,
    initial_backoff=2.0,
    timeout=120,
):
    """
    Call Groq API with robust 429 rate-limit handling and exponential backoff.

    Returns:
        dict: {
            "content": str,
            "model": str,
            "prompt_tokens": int,
            "completion_tokens": int,
            "total_tokens": int,
            "latency": float,
            "success": bool,
            "error": str or None,
        }
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not found in .env")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": temperature,
    }

    last_error = None
    for attempt in range(max_retries + 1):
        start_time = time.time()
        try:
            response = requests.post(
                GROQ_URL,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            latency = time.time() - start_time

            # ----------------------------------------------------
            # 1. Rate Limit (HTTP 429) Handling
            # ----------------------------------------------------
            if response.status_code == 429:
                wait_sec = None

                # Strategy A: Check 'Retry-After' header
                retry_after_hdr = response.headers.get("retry-after") or response.headers.get("Retry-After")
                if retry_after_hdr:
                    try:
                        wait_sec = float(retry_after_hdr)
                    except ValueError:
                        pass

                # Strategy B: Parse JSON message for retry hint (e.g. 'try again in 3.5s')
                if wait_sec is None:
                    try:
                        err_json = response.json()
                        err_msg = err_json.get("error", {}).get("message", "")
                        match = re.search(r"try again in ([\d\.]+)s", err_msg)
                        if match:
                            wait_sec = float(match.group(1))
                    except Exception:
                        pass

                # Strategy C: Exponential backoff fallback
                if wait_sec is None:
                    wait_sec = min(initial_backoff * (2 ** attempt), 30.0)

                # Add 0.5s safety buffer, bounded between 1.0s and 60.0s
                wait_sec = min(max(wait_sec + 0.5, 1.0), 60.0)

                if attempt < max_retries:
                    print(
                        f"[Groq 429 Rate Limit] Backing off for {wait_sec:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(wait_sec)
                    continue
                else:
                    last_error = f"HTTP 429 Rate limit exceeded after {max_retries} retries"
                    break

            # ----------------------------------------------------
            # 2. Transient 5xx Server Error Handling
            # ----------------------------------------------------
            if response.status_code in (500, 502, 503, 504):
                if attempt < max_retries:
                    wait_sec = min(initial_backoff * (2 ** attempt), 20.0)
                    print(
                        f"[Groq {response.status_code} Error] Server error. "
                        f"Retrying in {wait_sec:.1f}s (attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(wait_sec)
                    continue

            # Check for any other HTTP errors (400, 401, 404, etc.)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"] or ""
            usage = data.get("usage", {})

            return {
                "content": content,
                "model": data.get("model", GROQ_MODEL),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "latency": latency,
                "success": True,
                "error": None,
            }

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt < max_retries:
                wait_sec = min(initial_backoff * (2 ** attempt), 20.0)
                print(
                    f"[Groq Network Exception] {e}. "
                    f"Retrying in {wait_sec:.1f}s (attempt {attempt + 1}/{max_retries})..."
                )
                time.sleep(wait_sec)
            else:
                break

    # If all retry attempts failed
    return {
        "content": "",
        "model": GROQ_MODEL,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "latency": 0.0,
        "success": False,
        "error": last_error,
    }


def groq_generate(prompt, temperature=0):
    """
    Drop-in replacement for existing groq_generate callers.
    Returns the string text content directly.
    """
    res = groq_generate_with_metadata(prompt, temperature=temperature)
    if not res["success"] and res["error"]:
        raise RuntimeError(f"Groq API call failed: {res['error']}")
    return res["content"]


if __name__ == "__main__":
    # Local verification without making an external API call
    print("groq_client configuration:")
    print("  GROQ_MODEL:", GROQ_MODEL)
    print("  GROQ_URL  :", GROQ_URL)
    print("  HAS_KEY   :", bool(GROQ_API_KEY))
    print("Verification OK.")