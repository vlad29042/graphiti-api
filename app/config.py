from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings using Pydantic.
    Loads environment variables and provides them as typed attributes.
    """
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_API_KEY: str

# Create a singleton instance of the settings
settings = Settings()