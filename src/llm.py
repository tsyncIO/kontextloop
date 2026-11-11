"""Ollama HTTP client and prompt builder for KontextLoop."""

from __future__ import annotations

import re
from typing import Any

import httpx

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1:8b"
REQUEST_TIMEOUT = 30.0


class OllamaError(Exception):
    """Custom exception for Ollama communication errors with user-friendly messages."""


def build_prompt(german: str, english: str, pos: str) -> str:
    """Build the prompt for Ollama according to Section 7 of spec.txt."""
    return f"""You are a German language tutor helping a learner understand vocabulary in context.

Target word: {german} (English: {english}, Part of speech: {pos})

Generate exactly 7 short, natural German sentences from everyday life in Germany where this word is used in a different context each time. Keep each sentence under 15 words. Use simple A1–B1 vocabulary for surrounding words.

After each German sentence, write its English translation on the next line, prefixed with "EN: ".

Format:
1. [German sentence]
EN: [English translation]
2. [German sentence]
EN: [English translation]
...

Do not add any other text before or after."""


def parse_llm_response(text: str) -> list[tuple[str, str]]:
    """Parse the LLM numbered sentences and EN: translations into pairs.
    
    Returns:
        list of (german_sentence, english_translation)
    """
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    results: list[tuple[str, str]] = []

    current_german: str | None = None

    for line in lines:
        # Check if line starts with EN: translation prefix
        if line.lower().startswith("en:") or line.lower().startswith("en :"):
            en_text = re.sub(r"^en\s*:\s*", "", line, flags=re.IGNORECASE).strip()
            if current_german:
                results.append((current_german, en_text))
                current_german = None
        else:
            # Check for numbered sentence like "1. Ich...", "1) Ich...", or unnumbered sentence
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
            if cleaned:
                if current_german and not results:
                    # Previous German sentence had no EN translation yet
                    pass
                current_german = cleaned

    return results


def generate_sentences(
    german: str,
    english: str,
    pos: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
) -> list[tuple[str, str]]:
    """Call Ollama local LLM to generate context sentences.
    
    Fails gracefully with OllamaError if Ollama is unreachable or times out.
    """
    prompt = build_prompt(german, english, pos)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(base_url, json=payload)
            if response.status_code == 404:
                raise OllamaError(
                    f"Model '{model}' not found in Ollama.\n"
                    f"Please pull the model first using:\n\n"
                    f"  ollama pull {model}\n"
                )
            response.raise_for_status()
            data = response.json()
            raw_response = data.get("response", "")
            parsed = parse_llm_response(raw_response)
            if not parsed:
                raise OllamaError("Failed to parse sentences from LLM response. Please try again.")
            return parsed

    except httpx.ConnectError:
        raise OllamaError(
            "Ollama is not running or unreachable at http://localhost:11434.\n"
            "Please start Ollama in a separate terminal with:\n\n"
            "  ollama serve\n"
        )
    except httpx.TimeoutException:
        raise OllamaError(
            f"Ollama request timed out after {int(REQUEST_TIMEOUT)}s.\n"
            "The model may be loading or your system is under heavy load. Please try again."
        )
    except httpx.HTTPStatusError as e:
        raise OllamaError(f"Ollama HTTP error ({e.response.status_code}): {e.response.text}")
    except OllamaError:
        raise
    except Exception as e:
        raise OllamaError(f"Unexpected error communicating with Ollama: {e}")
