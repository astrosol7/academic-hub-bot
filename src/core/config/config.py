"""
Core configuration for Academic Hub — Orbit V1.0
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv


def initialize_env():
    """Find and load the .env file from the project root."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        env_path = current / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            return True
        if current.parent == current:
            break
        current = current.parent
    load_dotenv()
    return False


@dataclass
class BotConfig:
    """Bot configuration"""
    token: str = ""
    admin_ids: list[int] = field(default_factory=list)
    voyager_url: Optional[str] = None


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    name: str = "academic_hub"
    user: str = "postgres"
    password: str = ""


@dataclass
class AppConfig:
    """Application configuration — single source of truth for all services."""
    bot: BotConfig = field(default_factory=BotConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    debug: bool = False
    # API Limits
    api_default_limit: int = 20
    api_max_limit_public: int = 100
    api_max_limit_admin: int = 1000

    # Backend integration (bot → API bridge)
    backend_base_url: str = "http://127.0.0.1:8000"
    orbit_bot_api_key: str = ""
    institution_slug: str = "sit"
    institution_website: str = "sitedu.info"

    # Trust gate
    required_group_id: str = ""
    required_group_invite_link: str = ""

    # Admin
    admin_telegram_id: str = ""

    # External Auth
    google_client_id: str = ""

    # AI Helper
    groq_api_key: str = ""  # Comma-separated for multiple keys
    ai_helper_enabled: bool = True
    ai_daily_limit_regular: int = 50
    ai_daily_limit_verified: int = 200

    @property
    def voyager_url(self) -> Optional[str]:
        return self.bot.voyager_url


def load_config(require_token: bool = True) -> AppConfig:
    """Load configuration from environment variables."""
    initialize_env()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if require_token and not bot_token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN environment variable is required. "
            "Ensure your .env file exists in the project root."
        )

    admin_ids_str = os.getenv("BOT_ADMIN_IDS", "")
    admin_ids = []
    if admin_ids_str:
        try:
            admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",")]
        except ValueError:
            raise ValueError("BOT_ADMIN_IDS must be comma-separated integers")

    bot_config = BotConfig(
        token=bot_token,
        admin_ids=admin_ids,
        voyager_url=os.getenv("VOYAGER_URL"),
    )

    database_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        name=os.getenv("POSTGRES_DB", "academic_hub"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )

    return AppConfig(
        bot=bot_config,
        database=database_config,
        debug=os.getenv("DEBUG", "false").lower() == "true",
        api_default_limit=int(os.getenv("API_DEFAULT_LIMIT", "20")),
        api_max_limit_public=int(os.getenv("API_MAX_LIMIT_PUBLIC", "100")),
        api_max_limit_admin=int(os.getenv("API_MAX_LIMIT_ADMIN", "1000")),
        backend_base_url=os.getenv("ORBIT_BACKEND_BASE_URL", "http://127.0.0.1:8000"),
        orbit_bot_api_key=os.getenv("ORBIT_BOT_API_KEY", ""),
        institution_slug=os.getenv("INSTITUTION_SLUG", "sit"),
        institution_website=os.getenv("INSTITUTION_WEBSITE", "sitedu.info"),
        required_group_id=os.getenv("ORBIT_REQUIRED_GROUP_ID", ""),
        required_group_invite_link=os.getenv("ORBIT_REQUIRED_GROUP_INVITE_LINK", ""),
        admin_telegram_id=os.getenv("ORBIT_ADMIN_TELEGRAM_ID", ""),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        ai_helper_enabled=os.getenv("AI_HELPER_ENABLED", "true").lower() == "true",
        ai_daily_limit_regular=int(os.getenv("AI_DAILY_LIMIT_REGULAR", "50")),
        ai_daily_limit_verified=int(os.getenv("AI_DAILY_LIMIT_VERIFIED", "200")),
    )
