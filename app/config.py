from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings using Pydantic.
    Loads environment variables and provides them as typed attributes.
    """
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    
    # Database type selection
    DB_TYPE: str = "falkordb"  # "neo4j" or "falkordb"
    
    # Neo4j settings (if using Neo4j)
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    
    # FalkorDB settings (if using FalkorDB)
    FALKOR_HOST: str = "falkordb"
    FALKOR_PORT: int = 6379
    FALKOR_USER: str = ""
    FALKOR_PASSWORD: str = ""
    FALKOR_DATABASE: str = "graphiti"
    
    # Model settings
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_API_KEY: str

# Create a singleton instance of the settings
settings = Settings()