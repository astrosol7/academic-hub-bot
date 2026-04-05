"""
One-time: move resources/Quarter_* into resources/institutions/<slug>/Quarter_*
if they still live at the old flat path. Does not overwrite.

  python tools/migrate_resources_layout.py --dry-run
  python tools/migrate_resources_layout.py
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from hub_institution import resources_root


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    base = ROOT_DIR / "resources"
    target = resources_root()
    target.mkdir(parents=True, exist_ok=True)
    moved = 0
    for qdir in sorted(base.glob("Quarter_*")):
        if not qdir.is_dir():
            continue
        if "institutions" in qdir.parts:
            continue
        dest = target / qdir.name
        if dest.exists():
            print(f"skip (exists): {dest}")
            continue
        if args.dry_run:
            print(f"would move: {qdir} -> {dest}")
        else:
            shutil.move(str(qdir), str(dest))
            print(f"moved: {qdir.name} -> {dest}")
        moved += 1
    print(f"Done. moved={moved}")


if __name__ == "__main__":
    main()
