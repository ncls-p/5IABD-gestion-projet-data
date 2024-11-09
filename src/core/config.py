from pydantic import BaseModel
from functools import lru_cache
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class Settings(BaseModel):
    # Database settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "postgres")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "mysecretpassword")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    # LLM settings
    LLM_API_URL: str = os.getenv(
        "LLM_API_URL", "https://api.openai.com/v1/chat/completions"
    )
    MODEL_ID: str = os.getenv("MODEL_ID", "gpt-3.5-turbo")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
