"""DailyForge backend configuration — loaded from environment / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "development"
    secret_key: str = "changeme-dev-secret-not-for-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Database
    database_url: str = "sqlite:///./dailyforge_dev.db"

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "https://dailyforge-backend-kwti.onrender.com/auth/github/callback"

    # Authorized user
    authorized_github_username: str = "geeky-rish"
    authorized_github_user_id: Optional[int] = None

    # GitHub write token
    github_write_token: str = ""
    github_readme_repo: str = "geeky-rish/geeky-rish"

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_email: str = ""
    smtp_app_password: str = ""
    email_from: str = ""
    email_to: str = ""
    recipient_email: str = ""
    smtp_tls: bool = True
    email_dry_run: bool = True  # safe default: do not send real email without explicit opt-in

    @property
    def sender_email(self) -> str:
        return self.email_from or self.smtp_email or self.smtp_user

    @property
    def sender_user(self) -> str:
        return self.smtp_user or self.smtp_email or self.email_from

    @property
    def sender_password(self) -> str:
        return self.smtp_app_password or self.smtp_password

    @property
    def recipient(self) -> str:
        return self.recipient_email or self.email_to

    # Frontend / CORS
    frontend_url: str = "http://localhost:5173"

    # Challenge
    challenge_start_date: str = "2024-01-01"
    timezone: str = "Asia/Kolkata"
    questions_per_day: int = 2

    # Server
    port: int = 8000


settings = Settings()
