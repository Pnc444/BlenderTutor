from dotenv import load_dotenv
import os

def load_config():
    load_dotenv()

    config = {
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "use_local": os.getenv("USE_LOCAL", "false").lower() == "true",
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.2-vision").strip(),
        "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5").strip(),
        "monitor": int(os.getenv("MONITOR", "1")),
    }

    return config

