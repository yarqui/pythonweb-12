from typing import List
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # These are the default test constants to be used if they are not found in the environment or a .env file.
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "finalpassword"
    POSTGRES_DB: str = "contactapp-db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"

    # JWT Settings with Defaults
    JWT_SECRET_KEY: str = "insecure_default_secret_for_testing"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # CORS and IP Ban Settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    BANNED_IPS: List[str] = ["91.218.114.206", "46.17.46.213"]

    # Email Service Settings
    MAIL_USERNAME: str = "email@example.com"
    MAIL_PASSWORD: SecretStr = SecretStr("email_password")
    MAIL_FROM: str = "email@example.com"
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_FROM_NAME: str = "Awesome contact App"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    # Cloudinary settings
    CLOUDINARY_API_NAME: str = "pythonweb10"
    CLOUDINARY_API_KEY: str = "123456789"
    CLOUDINARY_API_SECRET: str = "cloudinary_secret"
    
    # Redis config
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Override the above default settings if .env is found
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
