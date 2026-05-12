"""
Uygulama ayarları - .env dosyasından okur.
Tüm konfigürasyonlar tek bir yerden yönetilir.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Database
    DATABASE_URL: str = "postgresql://leadsuser:leadspass@localhost:5432/leadsdb"
    REDIS_URL: str = "redis://localhost:6379/0"

    # API Keys
    PDL_API_KEY: str = ""
    HUNTER_API_KEY: str = ""
    SENDGRID_API_KEY: str = ""
    DEEPL_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Email
    SENDER_EMAIL: str = "info@example.com"
    SENDER_NAME: str = "Your Company"
    COMPANY_WEBSITE: str = "https://example.com"

    # Tracking
    TRACKING_BASE_URL: str = "http://localhost:8000"
    WEBHOOK_SECRET: str = "change_me"

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "change_me_secret"
    DEBUG: bool = True


settings = Settings()
