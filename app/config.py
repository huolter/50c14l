from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./50c14l.db"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "dev-secret-key-change-in-production"
    environment: str = "development"
    allowed_origins: str = "*"

    class Config:
        env_file = ".env"


settings = Settings()
