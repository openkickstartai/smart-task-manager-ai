from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "sqlite:///./taskmanager.db"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # ML Model settings
    model_update_frequency: int = 7  # days
    min_data_points: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()