from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings using Pydantic.
    Loads environment variables and provides them as typed attributes.
    """
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    # FalkorDB Settings
    FALKORDB_HOST: str = "falkordb"
    FALKORDB_PORT: int = 6379
    FALKORDB_PASSWORD: str = ""
    
    # LLM Settings
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_API_KEY: str
    
    # Embedding Settings
    EMBEDDING_DIM: int = 1536
    EMBEDDING_PROVIDER: str = "openai"

# Create a singleton instance of the settings
settings = Settings()