"""Storage layer for KontextLoop managing ~/.kontextloop/vocab.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STORAGE_DIR = Path.home() / ".kontextloop"
VOCAB_FILE = STORAGE_DIR / "vocab.json"


def _ensure_storage_dir() -> None:
    """Ensure the ~/.kontextloop directory exists."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def load_vocab() -> list[dict[str, Any]]:
    """Load vocab list from ~/.kontextloop/vocab.json.
    
    Returns an empty list if the file does not exist or is invalid.
    """
    if not VOCAB_FILE.exists():
        return []
    try:
        with VOCAB_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def save_vocab(entries: list[dict[str, Any]]) -> None:
    """Save vocab list to ~/.kontextloop/vocab.json."""
    _ensure_storage_dir()
    with VOCAB_FILE.open("w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def add_vocab_entries(new_entries: list[dict[str, Any]]) -> tuple[int, int]:
    """Add or update vocab entries by matching the German word (case-insensitive).
    
    Returns:
        tuple[int, int]: (added_count, updated_count)
    """
    existing = load_vocab()
    lookup = {item.get("german", "").strip().lower(): idx for idx, item in enumerate(existing)}
    
    added = 0
    updated = 0
    
    for entry in new_entries:
        key = entry.get("german", "").strip().lower()
        if not key:
            continue
        if key in lookup:
            idx = lookup[key]
            # Preserve streak and lastSeen if existing
            old_meta = existing[idx].get("metadata", {})
            entry_meta = entry.get("metadata", {})
            entry_meta["streak"] = old_meta.get("streak", 0)
            entry_meta["lastSeen"] = old_meta.get("lastSeen", None)
            existing[idx] = entry
            updated += 1
        else:
            existing.append(entry)
            lookup[key] = len(existing) - 1
            added += 1

    save_vocab(existing)
    return added, updated


def reset_vocab() -> None:
    """Clear all stored vocab entries."""
    _ensure_storage_dir()
    save_vocab([])
