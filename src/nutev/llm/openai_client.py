import os

def is_openai_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))
