"""One place for every AI call. To swap the model, edit the 3 settings below."""
import os
import time
import getpass

PROVIDER = os.environ.get("LLM_PROVIDER", "groq")
MODEL_NAME = os.environ.get("LLM_MODEL", "openai/gpt-oss-20b")
SLEEP_BETWEEN_CALLS = 1       # seconds, keeps us under free-tier rate limits
MAX_RETRIES = 5

# counters used later for the cost / scale part of your doc
STATS = {"calls": 0, "input_tokens": 0, "output_tokens": 0}
_client = None


def _get_client():
    """Create the API client once. Key comes from an environment variable, else a hidden prompt."""
    global _client
    if _client is None:
        key = (os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY")
               or os.environ.get("GROQ_API_KEY") or getpass.getpass("Paste your API key: "))
        if PROVIDER == "gemini":
            from google import genai
            _client = genai.Client(api_key=key)
        elif PROVIDER == "groq":
            from groq import Groq
            _client = Groq(api_key=key)
        else:
            raise ValueError(f"Unknown PROVIDER: {PROVIDER}")
    return _client


def call_llm(prompt, temperature=0.2):
    """Send a prompt, return the reply text. Every AI call in the project goes through here."""
    client = _get_client()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if PROVIDER == "gemini":
                from google.genai import types
                resp = client.models.generate_content(
                    model=MODEL_NAME, contents=prompt,
                    config=types.GenerateContentConfig(temperature=temperature))
                text = resp.text or ""
                usage = getattr(resp, "usage_metadata", None)
                if usage:
                    STATS["input_tokens"] += getattr(usage, "prompt_token_count", 0) or 0
                    STATS["output_tokens"] += getattr(usage, "candidates_token_count", 0) or 0
            else:
                # pass reasoning_effort for openai/gpt-oss models; retry without it if SDK rejects it
                kw = {"reasoning_effort": "low"} if MODEL_NAME.startswith("openai/gpt-oss") else {}
                try:
                    resp = client.chat.completions.create(
                        model=MODEL_NAME, temperature=temperature,
                        messages=[{"role": "user", "content": prompt}], **kw)
                except TypeError:
                    resp = client.chat.completions.create(
                        model=MODEL_NAME, temperature=temperature,
                        messages=[{"role": "user", "content": prompt}])
                text = resp.choices[0].message.content or ""
                if getattr(resp, "usage", None):
                    STATS["input_tokens"] += resp.usage.prompt_tokens or 0
                    STATS["output_tokens"] += resp.usage.completion_tokens or 0
            STATS["calls"] += 1
            time.sleep(SLEEP_BETWEEN_CALLS)
            return text
        except Exception as e:  # network error, rate limit, bad model name ...
            print(f"[llm] attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(4 * attempt)


if __name__ == "__main__":
    print(call_llm("Say hello in exactly three words."))
