"""Institution root: resources/institutions/<slug>/Quarter_*/… — override slug via env for other schools."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv

    load_dotenv(PACKAGE_ROOT / ".env")
except ImportError:
    pass

INSTITUTION_SLUG = os.environ.get("HUB_INSTITUTION_SLUG", "sit").strip() or "sit"
INSTITUTION_DISPLAY_NAME = os.environ.get(
    "HUB_INSTITUTION_NAME", "Shaggar Institute of Technology"
).strip() or "Shaggar Institute of Technology"


def resources_root() -> Path:
    return PACKAGE_ROOT / "resources" / "institutions" / INSTITUTION_SLUG
