from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_name: str = "codessa-memory"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"

    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60

    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    openai_api_key: str = ""
    openai_base_url: str = ""

    storage_backend: str = "local"
    local_data_dir: str = ".data"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    postgres_dsn: str = ""

    default_chunk_size: int = 900
    default_chunk_overlap: int = 120
    top_k: int = 5


settings = Settings()
