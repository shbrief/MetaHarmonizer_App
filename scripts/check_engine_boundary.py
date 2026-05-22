#!/usr/bin/env python3
"""
Engine boundary check — fails if any file outside backend/app/engine_adapter/
imports the upstream `metaharmonizer` package or reaches into the vendored
engine via `from src.*` / `from engine.src.*`.

Wired up by `.pre-commit-config.yaml` and `.github/workflows/engine-compat.yml`.

Usage (manual):
    python scripts/check_engine_boundary.py path/to/file1.py path/to/file2.py
    python scripts/check_engine_boundary.py            # scans backend/app/

See: docs/engine-adapter-architecture.md §5.1
     backend/app/engine_adapter/README.md
"""
from __future__ import annotations

import pathlib
import re
import sys

# Anything outside this prefix must NOT touch engine internals.
ALLOWED_PREFIXES = (
    "backend/app/engine_adapter/",
    "backend/tests/",
    "scripts/",
)

FORBIDDEN = re.compile(
    r"^\s*(?:from|import)\s+(metaharmonizer|src\.|engine\.src\.)",
)


def iter_paths(argv: list[str]) -> list[pathlib.Path]:
    if argv:
        return [pathlib.Path(p) for p in argv if p.endswith(".py")]
    root = pathlib.Path("backend/app")
    return [p for p in root.rglob("*.py") if p.is_file()]


def is_allowed(path: pathlib.Path) -> bool:
    posix = path.as_posix()
    return any(posix.startswith(prefix) or prefix.rstrip("/") in posix for prefix in ALLOWED_PREFIXES)


def main(argv: list[str]) -> int:
    errors: list[str] = []
    for path in iter_paths(argv):
        if is_allowed(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if FORBIDDEN.match(line):
                errors.append(f"{path.as_posix()}:{i}: {line.strip()}")

    if errors:
        print("Engine boundary violation — these imports are only allowed inside")
        print("backend/app/engine_adapter/ (see docs/engine-adapter-architecture.md):")
        for e in errors:
            print("  " + e)
        return 1
    print("engine-boundary: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
