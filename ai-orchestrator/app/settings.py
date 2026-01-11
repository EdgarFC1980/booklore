from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # BookLore backend connection
    booklore_base_url: str = "http://booklore:8080"
    booklore_api_token: str | None = None

    # Models configuration
    models_config_path: str = "/config/models.yml"

    # LLM provider API keys (can also be set per-tier in models.yml)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


settings = Settings()
