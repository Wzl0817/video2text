"""Configuration module."""

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()


class Settings:
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_PAGE_ID: str = os.getenv("NOTION_PAGE_ID", "")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    BROWSER: str = os.getenv("BROWSER", "")
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    OUTPUT_DIR: Path = BASE_DIR / "output"
    UPLOADS_DIR: Path = BASE_DIR / "uploads"


settings = Settings()
