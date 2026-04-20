"""
Summarize PDF counts under resources/institutions/<slug>/ for release checks.

  python tools/validate_resources.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from academic_hub.config import load_config

def main() -> None:
    config = load_config(require_token=False)
    root = config.resources_root
    
    if not root.is_dir():
        print(f"No tree yet: {root}")
        return
        
    print(f"Institution: {config.institution_slug}\nRoot: {root}\n")
    total = 0
    for q in sorted(root.glob("Quarter_*")):
        if not q.is_dir():
            continue
        print(q.name)
        for course in sorted(q.iterdir()):
            if not course.is_dir():
                continue
            n = sum(1 for p in course.rglob("*.pdf") if p.is_file())
            if n == 0:
                continue
            total += n
            cats: dict[str, int] = {}
            for p in course.rglob("*.pdf"):
                rel = p.relative_to(course)
                cat = rel.parts[0] if rel.parts else "."
                cats[cat] = cats.get(cat, 0) + 1
            cat_s = ", ".join(f"{k}:{v}" for k, v in sorted(cats.items()))
            print(f"  {course.name}: {n} PDFs  ({cat_s})")
            
    print(f"\nTotal PDFs: {total}")

if __name__ == "__main__":
    main()
