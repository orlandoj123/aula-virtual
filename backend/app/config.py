from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://aula_user:aula_password@localhost/aula_db")
    secret_key: str = os.getenv("SECRET_KEY", "tu-clave-secreta-cambiar")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    google_service_account_file: str = "/home/blacklotus/aula-virtual/service_account.json"
    env: str = os.getenv("ENV", "development")
    max_file_size_bytes: int = 50 * 1024 * 1024
    allowed_file_extensions: list = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "jpg", "jpeg", "png", "gif", "zip"]
    
    class Config:
        env_file = ".env"

settings = Settings()
