from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:////data/50c14l.db"  # Persistent disk in production, override for local dev
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "dev-secret-key-change-in-production"
    environment: str = "development"
    allowed_origins: str = "*"

    class Config:
        env_file = ".env"


settings = Settings()
