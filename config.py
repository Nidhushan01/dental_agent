from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:////tmp/dental.db"
    
    # OpenRouter (Hermes)
    OPENROUTER_API_KEY: str = ""
    # Choose a valid OpenRouter model ID for your account. Leave empty to require explicit config.
    # Examples (replace with a model available to your OpenRouter plan):
    # - gpt-4o-mini
    # - gpt-4o
    # - oasst-preview/13b (if available)
    OPENROUTER_MODEL: str = ""
    
    # Voice
    STT_MODEL: str = "base"  # Whisper model size
    TTS_LANGUAGE: str = "en"
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()