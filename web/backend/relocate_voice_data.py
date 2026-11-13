"""Rewrite saved paths after unpacking the portable voice bundle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def relocate(value, target: Path):
    if isinstance(value, dict):
        return {key: relocate(item, target) for key, item in value.items()}
    if isinstance(value, list):
        return [relocate(item, target) for item in value]
    if not isinstance(value, str):
        return value
    normalized = value.replace("\\", "/")
    marker = "/.voice-data/"
    if marker not in normalized or "://" in normalized:
        return value
    suffix = normalized.split(marker, 1)[1]
    parts = Path(suffix).parts
    if not parts or any(part in ("..", ".") for part in parts):
        raise ValueError("Invalid saved path: " + value)
    return str(target.joinpath(*parts))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=Path, help="Copied .voice-data directory")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    data_dir = args.data_dir.resolve()
    store = data_dir / "characters.json"
    data = json.loads(store.read_text("utf-8"))
    converted = relocate(data, data_dir)
    missing = []

    def check(value):
        if isinstance(value, dict):
            for item in value.values():
                check(item)
        elif isinstance(value, list):
            for item in value:
                check(item)
        elif isinstance(value, str) and value.startswith(str(data_dir)) and not Path(value).is_file():
            missing.append(value)

    check(converted)
    if missing:
        raise SystemExit(f"{len(missing)} referenced files are missing; first: {missing[0]}")
    if not args.dry_run:
        backup = store.with_suffix(".json.bak")
        backup.write_bytes(store.read_bytes())
        temporary = store.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(converted, ensure_ascii=False, indent=2), "utf-8")
        temporary.replace(store)
    print("Voice data paths validated" + (" (dry run)" if args.dry_run else "; backup saved"))


if __name__ == "__main__":
    main()
