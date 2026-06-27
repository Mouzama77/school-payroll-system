from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    APP_NAME: str = "School Payroll Management System"
    APP_ENV: str = "development"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/school_payroll_db"
    SECRET_KEY: str  # No default — startup fails loudly if unset in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    FRONTEND_URL: str = "http://localhost:5173"
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60

    # Authentication / password policy
    MIN_PASSWORD_LENGTH: int = 8

    # Forgot password token lifetime must be 10–15 minutes per production requirement
    PASSWORD_RESET_EXPIRE_MINUTES_MIN: int = 10
    PASSWORD_RESET_EXPIRE_MINUTES_MAX: int = 15


    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True


settings = Settings()
