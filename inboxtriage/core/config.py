import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_settings() -> dict[str, str]:
    return {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./inboxtriage.db"),
        "gmail_credentials_path": os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json"),
        "gmail_token_path": os.getenv("GMAIL_TOKEN_PATH", "token.json"),
        "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
    }

