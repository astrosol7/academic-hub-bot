from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from aiogram.utils.token import validate_token
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    token: str
    institution_slug: str
    institution_name: str
    resources_root: Path
    manifests_root: Path
    log_level: str
    max_index_memory_mb: float
    backend_base_url: str
    orbit_bot_api_key: str
    required_group_id: str
    required_group_invite_link: str
    admin_telegram_id: int | None


def _float_env(name: str, default: str) -> float:
    raw = (os.environ.get(name) or default).strip()
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number, got {raw!r}.") from exc


def load_config(*, require_token: bool = True) -> AppConfig:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if require_token and not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN in .env.")
    if token and not validate_token(token):
        raise RuntimeError("TELEGRAM_BOT_TOKEN is invalid.")

    institution_slug = os.environ.get("HUB_INSTITUTION_SLUG", "sit").strip() or "sit"
    institution_name = (
        os.environ.get("HUB_INSTITUTION_NAME", "Shaggar Institute of Technology").strip()
        or "Shaggar Institute of Technology"
    )
    backend_base_url = (os.environ.get("ORBIT_BACKEND_BASE_URL") or "http://127.0.0.1:8000").strip()
    orbit_bot_api_key = (os.environ.get("ORBIT_BOT_API_KEY") or "").strip()
    required_group_id = (os.environ.get("ORBIT_REQUIRED_GROUP_ID") or "").strip()
    required_group_invite_link = (os.environ.get("ORBIT_REQUIRED_GROUP_INVITE_LINK") or "").strip()
    admin_telegram_id_raw = (os.environ.get("ORBIT_ADMIN_TELEGRAM_ID") or "").strip()
    admin_telegram_id = int(admin_telegram_id_raw) if admin_telegram_id_raw else None
    return AppConfig(
        base_dir=BASE_DIR,
        token=token,
        institution_slug=institution_slug,
        institution_name=institution_name,
        resources_root=BASE_DIR / "resources" / "institutions" / institution_slug,
        manifests_root=BASE_DIR / "academic_hub" / "manifests",
        log_level=(os.environ.get("ACADEMIC_HUB_LOG_LEVEL") or "INFO").upper(),
        max_index_memory_mb=_float_env("ACADEMIC_HUB_MAX_INDEX_MEMORY_MB", "32"),
        backend_base_url=backend_base_url,
        orbit_bot_api_key=orbit_bot_api_key,
        required_group_id=required_group_id,
        required_group_invite_link=required_group_invite_link,
        admin_telegram_id=admin_telegram_id,
    )
