from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AI Resume Scanner"
    database_url: str = "sqlite:///./resume_scanner.db"
    cors_origins: str = "http://localhost:5173"
    upload_dir: str = "../data/uploads"
    max_upload_mb: int = 10
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
