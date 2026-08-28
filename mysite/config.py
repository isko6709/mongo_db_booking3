from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    mongodb_url: str
    mongodb_db_name: str = 'mongo_db'

    auth_service_url: str = 'http://127.0.0.1:8000'
    hotel_service_url: str = 'http://127.0.0.1:8001'

    model_config = SettingsConfigDict(
        env_file= BASE_DIR / '.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()