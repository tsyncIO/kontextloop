"""Ingestion and normalization layer for parsing vocabulary input files."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Supported delimiters according to spec.txt: '-', '=', ';'
DELIMITER_REGEX = re.compile(r"\s*[-=;]\s*")


def normalize_entry(raw_german: str, raw_english: str) -> dict[str, Any]:
    """Normalize German and English terms and determine part of speech metadata.
    
    Rules according to spec.txt:
    - If German word starts with 'der ', 'die ', or 'das ' -> capitalize the main word, partOfSpeech: "noun".
    - If German word starts with 'zu ' -> partOfSpeech: "verb".
    - Otherwise -> partOfSpeech: "word".
    """
    german = raw_german.strip()
    english = raw_english.strip()

    german_lower = german.lower()
    
    # Check for noun articles: der, die, das
    articles = ("der ", "die ", "das ")
    article_match = None
    for art in articles:
        if german_lower.startswith(art):
            article_match = art
            break

    if article_match:
        pos = "noun"
        article = german[:len(article_match)].lower()
        remainder = german[len(article_match):].strip()
        
        # Capitalize the main word (noun)
        if remainder:
            remainder_words = remainder.split()
            # Capitalize the first noun word, preserve the rest
            remainder_words[0] = remainder_words[0].capitalize()
            normalized_german = f"{article}{' '.join(remainder_words)}"
        else:
            normalized_german = article.strip()
    elif german_lower.startswith("zu "):
        pos = "verb"
        normalized_german = german
    else:
        pos = "word"
        normalized_german = german

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "german": normalized_german,
        "english": english,
        "metadata": {
            "partOfSpeech": pos,
            "addedAt": now_iso,
            "streak": 0,
            "lastSeen": None,
        },
    }


def parse_vocab_line(line: str) -> dict[str, Any] | None:
    """Parse a single vocabulary line with delimiters ('-', '=', ';').
    
    Returns None if line is blank or does not contain a valid pair.
    """
    cleaned = line.strip()
    if not cleaned or cleaned.startswith("#"):
        return None

    # Split on first occurrence of supported delimiters
    parts = DELIMITER_REGEX.split(cleaned, maxsplit=1)
    if len(parts) != 2:
        return None

    german, english = parts[0].strip(), parts[1].strip()
    if not german or not english:
        return None

    return normalize_entry(german, english)


def parse_vocab_file(file_path: str | Path) -> list[dict[str, Any]]:
    """Parse a plain text file containing German-English vocabulary pairs."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Vocabulary file not found: {file_path}")

    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            entry = parse_vocab_line(line)
            if entry:
                entries.append(entry)

    return entries
