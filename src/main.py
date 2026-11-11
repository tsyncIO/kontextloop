"""CLI entry point and command router for KontextLoop."""

from __future__ import annotations

import argparse
import random
import sys
import time
from datetime import datetime, timezone

from src.display import (
    console,
    display_error,
    display_info,
    display_navigation_prompt,
    display_sentences,
    display_session_summary,
    display_success,
    display_vocab_table,
    display_word_header,
)
from src.ingestion import parse_vocab_file
from src.llm import DEFAULT_MODEL, OllamaError, ensure_ollama_running, generate_sentences, unload_model
from src.storage import add_vocab_entries, load_vocab, reset_vocab, save_vocab


def handle_add(file_path: str) -> None:
    """Handle 'kloop add <file.txt>' command."""
    try:
        entries = parse_vocab_file(file_path)
    except FileNotFoundError as e:
        display_error(str(e))
        sys.exit(1)
    except Exception as e:
        display_error(f"Failed to read vocabulary file: {e}")
        sys.exit(1)

    if not entries:
        display_info(f"No valid vocabulary pairs found in '{file_path}'.")
        return

    added, updated = add_vocab_entries(entries)
    msg = f"Imported vocabulary from {file_path}: {added} added"
    if updated > 0:
        msg += f", {updated} updated"
    display_success(msg)


def handle_list() -> None:
    """Handle 'kloop list' command."""
    entries = load_vocab()
    display_vocab_table(entries)


def handle_reset() -> None:
    """Handle 'kloop reset' command."""
    entries = load_vocab()
    if not entries:
        display_info("Vocabulary storage is already empty.")
        return

    reset_vocab()
    display_success("All stored vocabulary has been cleared.")


def handle_session(words_count: int = 10, model: str = DEFAULT_MODEL) -> None:
    """Handle 'kloop session [--words N] [--model MODEL]' command."""
    all_vocab = load_vocab()
    if not all_vocab:
        display_error("No vocabulary stored yet. Add pairs first using:\n\n  kloop add <vocab.txt>\n")
        return

    sample_size = min(words_count, len(all_vocab))
    session_words = random.sample(all_vocab, sample_size)

    display_info(f"Starting session with {sample_size} words using model '{model}'...")
    
    # Ensure Ollama service is running, auto-spawning it if needed
    try:
        ensure_ollama_running()
    except OllamaError as err:
        display_error(str(err))
        return

    start_time = time.time()
    words_seen = 0

    try:
        for idx, entry in enumerate(session_words, start=1):
            german = entry.get("german", "")
            english = entry.get("english", "")
            meta = entry.get("metadata", {})
            pos = meta.get("partOfSpeech", "word")

            with console.status(f"[bold cyan]Generating context for '{german}'...[/bold cyan]"):
                try:
                    sentences = generate_sentences(german, english, pos, model=model)
                except OllamaError as err:
                    display_error(str(err))
                    return

            display_word_header(german, english)
            display_sentences(sentences, german)

            # Update word metadata
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            meta["lastSeen"] = now_iso
            meta["streak"] = meta.get("streak", 0) + 1
            words_seen += 1

            # Save progress incrementally
            save_vocab(all_vocab)

            # Navigation prompt
            if idx < sample_size:
                display_navigation_prompt()
                try:
                    choice = input().strip().lower()
                    if choice == "q":
                        display_info("Session ended early by user.")
                        break
                except (KeyboardInterrupt, EOFError):
                    console.print()
                    display_info("Session interrupted.")
                    break
            else:
                display_info("All words in this session completed!")

    finally:
        # Immediately unload model from memory to free RAM
        unload_model(model=model)
        elapsed = time.time() - start_time
        if words_seen > 0:
            display_session_summary(words_seen, elapsed)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for kloop."""
    parser = argparse.ArgumentParser(
        prog="kloop",
        description="KontextLoop — Contextual German vocabulary learning via local LLM.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # kloop add <file.txt>
    add_parser = subparsers.add_parser("add", help="Ingest vocab pairs from a plain text file")
    add_parser.add_argument("file", help="Path to vocabulary file (.txt)")

    # kloop session [--words N] [--model MODEL]
    session_parser = subparsers.add_parser("session", help="Start an interactive learning session")
    session_parser.add_argument(
        "--words",
        type=int,
        default=10,
        help="Number of words in this session (default: 10)",
    )
    session_parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Ollama model to use (default: {DEFAULT_MODEL})",
    )

    # kloop list
    subparsers.add_parser("list", help="Show all stored vocabulary")

    # kloop reset
    subparsers.add_parser("reset", help="Clear all stored vocabulary")

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "add":
        handle_add(args.file)
    elif args.command == "session":
        handle_session(words_count=args.words, model=args.model)
    elif args.command == "list":
        handle_list()
    elif args.command == "reset":
        handle_reset()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
