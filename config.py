from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./dental.db"

    # -------------------------------------------------------------------------
    # Hermes Agent Framework (NousResearch/hermes-agent)
    # The AIAgent class is configured via these settings.
    # OPENROUTER_API_KEY is passed as api_key to AIAgent.
    # OPENROUTER_MODEL  is passed as model to AIAgent (e.g. "openai/gpt-4o-mini").
    # HERMES_BASE_URL   is the OpenAI-compatible endpoint (OpenRouter by default).
    # -------------------------------------------------------------------------
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"  # OpenRouter model identifier
    HERMES_BASE_URL: str = "https://openrouter.ai/api/v1"  # AIAgent base_url

    # Voice
    STT_MODEL: str = "base"  # Whisper model size
    TTS_LANGUAGE: str = "en"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()