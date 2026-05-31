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
        "use_blender": os.getenv("USE_BLENDER", "true").lower() == "true",
        "blender_host": os.getenv("BLENDER_HOST", "localhost").strip(),
        "blender_port": int(os.getenv("BLENDER_PORT", "9876")),
    }

    return config

