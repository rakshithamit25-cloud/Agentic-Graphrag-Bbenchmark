"""
Shared Gemini client for the Agentic GraphRAG project.

Uses the official google-genai SDK (v2+).
The client is lazy-initialised once and reused across all calls.
The API key is read from the environment (loaded from .env by config.py).
"""

import os
from dotenv import load_dotenv

# Ensure .env is loaded before reading environment variables.
# config.py also calls load_dotenv(), but this makes gemini_client.py
# safe to import stand-alone.
load_dotenv()

from google import genai

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

GEMINI_MODEL = "gemini-3.8-flash"

# Module-level singleton - created once on first call to generate_text()
_client = None


def _get_client():
    """Return the shared Gemini client, initialising it if needed."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file and try again."
            )
        _client = genai.Client(api_key=api_key)
    return _client


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def generate_text(prompt, model=GEMINI_MODEL):
    """
    Send prompt to Gemini and return the response text.

    Args:
        prompt: The full prompt string to send.
        model:  Gemini model name. Defaults to GEMINI_MODEL.

    Returns:
        The model's text response as a plain string.

    Raises:
        EnvironmentError: If GEMINI_API_KEY is missing.
        google.genai.errors.APIError: On API-level failures.
    """
    client = _get_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text or ""


# ------------------------------------------------------------------
# Stand-alone smoke test (import check only - no API call)
# ------------------------------------------------------------------

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")

    key = os.environ.get("GEMINI_API_KEY")
    if key:
        masked = "*" * 8 + key[-4:]
        print("GEMINI_API_KEY present:", masked)
        print("Default model         :", GEMINI_MODEL)
        print("Client initialised    :", _get_client())
        print("Import OK. Call generate_text(prompt) to use.")
    else:
        print("ERROR: GEMINI_API_KEY not found in environment.")
