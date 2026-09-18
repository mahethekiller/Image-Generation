import os
from pathlib import Path
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "static" / "outputs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Load existing environment variables
load_dotenv(dotenv_path=ENV_FILE)

def get_env_var(key: str, default: str = "") -> str:
    # Refresh from file if needed
    load_dotenv(dotenv_path=ENV_FILE, override=True)
    return os.getenv(key, default)

def save_api_key(provider: str, api_key: str):
    """Saves or updates the API key in the .env file."""
    if not ENV_FILE.exists():
        ENV_FILE.touch()
    
    key_name = f"{provider.upper()}_API_KEY"
    set_key(str(ENV_FILE), key_name, api_key)
    os.environ[key_name] = api_key
    return key_name
