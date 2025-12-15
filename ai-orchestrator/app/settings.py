from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    booklore_base_url: str = "http://booklore:8080"
    booklore_api_token: str | None = None
    models_config_path: str = "/config/models.yml"

settings = Settings()
