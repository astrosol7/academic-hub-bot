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
    return AppConfig(
        base_dir=BASE_DIR,
        token=token,
        institution_slug=institution_slug,
        institution_name=institution_name,
        resources_root=BASE_DIR / "resources" / "institutions" / institution_slug,
        manifests_root=BASE_DIR / "academic_hub" / "manifests",
        log_level=(os.environ.get("ACADEMIC_HUB_LOG_LEVEL") or "INFO").upper(),
        max_index_memory_mb=float(os.environ.get("ACADEMIC_HUB_MAX_INDEX_MEMORY_MB") or "32"),
    )
