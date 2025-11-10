"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Pinecone Configuration
    pinecone_api_key: str
    # Index names can be overridden via environment variables (USERS_INDEX_NAME, ITEMS_INDEX_NAME)
    # Pinecone index names must consist of lowercase alphanumeric characters or '-'
    users_index_name: str = "pinecone-scout-users-index"
    items_index_name: str = "pinecone-scout-items-index"
    
    # OpenAI Configuration
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()

