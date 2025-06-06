import os
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GPT_MODEL: str = os.getenv("GPT_MODEL", "gpt-4-turbo-preview")

    # Application settings
    PORT: int = int(os.getenv("PORT", 8001))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    class Config:
        env_file = ".env"


settings = Settings()
