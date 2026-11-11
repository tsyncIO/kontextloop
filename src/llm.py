"""Ollama HTTP client and full-spectrum real-world scenario generator for KontextLoop."""

from __future__ import annotations

import os
import random
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

DEFAULT_OLLAMA_BASE = "http://localhost:11434"
DEFAULT_OLLAMA_URL = f"{DEFAULT_OLLAMA_BASE}/api/generate"
DEFAULT_MODEL = "llama3.1:8b"
REQUEST_TIMEOUT = 120.0

# Tracks subprocess if spawned by this session
_SPAWNED_OLLAMA_PROC: subprocess.Popen[Any] | None = None

# Full-spectrum domains spanning the complete reality of human interaction
SPECTRUM_DOMAINS = [
    "Industrial Engineering, Heavy Trades & Infrastructure Logistics",
    "Empirical Sciences, Field Research & Technical Discovery",
    "High-Stakes Law, Civic Governance & Investigative Inquiries",
    "Medicine, Clinical Triage & Emergency Response",
    "Artistic Direction, Acoustic Engineering, Literature & Design",
    "Deep Interpersonal Realism, Family Heritage & Psychological Dynamics",
    "Subcultures, Urban Street Realism & Community Micro-Economies",
    "Agriculture, Environmental Ecology & Wilderness Management",
    "Academic Debates, Philosophy, Ethics & Archival Preservation",
    "Maritime Navigation, Aviation Dispatch & Long-Haul Transport",
]


class OllamaError(Exception):
    """Custom exception for Ollama communication errors with user-friendly messages."""


@dataclass
class ScenarioDialogue:
    """Represents a rich, full-spectrum dialogue scenario and its translation."""
    domain: str
    theme: str
    german_paragraphs: list[tuple[str, str]] = field(default_factory=list)  # (Speaker, Text)
    english_paragraphs: list[tuple[str, str]] = field(default_factory=list)  # (Speaker, Text)


def is_ollama_running(base_url: str = DEFAULT_OLLAMA_BASE) -> bool:
    """Check whether the Ollama server is responding."""
    try:
        with httpx.Client(timeout=1.5) as client:
            resp = client.get(base_url)
            return resp.status_code == 200
    except Exception:
        return False


def ensure_ollama_running(base_url: str = DEFAULT_OLLAMA_BASE) -> bool:
    """Ensure Ollama is running, automatically starting it in the background if installed."""
    global _SPAWNED_OLLAMA_PROC

    if is_ollama_running(base_url):
        return True

    ollama_path = shutil.which("ollama")
    if not ollama_path:
        raise OllamaError(
            "Ollama binary not found on your system.\n"
            "Please install Ollama first from https://ollama.com or your package manager."
        )

    try:
        _SPAWNED_OLLAMA_PROC = subprocess.Popen(
            [ollama_path, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as e:
        raise OllamaError(f"Failed to automatically start 'ollama serve': {e}")

    start_time = time.time()
    while time.time() - start_time < 8.0:
        if is_ollama_running(base_url):
            return True
        time.sleep(0.5)

    if not is_ollama_running(base_url):
        raise OllamaError(
            "Started 'ollama serve' but could not establish a connection at http://localhost:11434.\n"
            "Please try running 'ollama serve' manually in another terminal."
        )

    return True


def build_scenario_prompt(german: str, english: str, pos: str) -> tuple[str, str]:
    """Build a prompt dynamically steered by a full-spectrum domain category.
    
    Returns:
        tuple[prompt, selected_domain]
    """
    selected_domain = random.choice(SPECTRUM_DOMAINS)

    prompt = f"""You are a master storyteller and linguistic dramatist crafting realistic dialogues across the entire spectrum of human experience.

Domain focus: {selected_domain}
Target word: {german} (English meaning: {english}, Part of speech: {pos})

TASK:
Write an authentic, highly detailed 2-person German conversation situated squarely within this domain. Avoid clichéd beginner language textbook tropes. Instead, capture the exact texture of real human conversation in this world — specific jargon, natural colloquial cadence, conflicting viewpoints, unsaid subtext, and genuine emotional or intellectual weight.

REQUIREMENTS:
1. THEME: Write a 1-sentence description of the specific scenario, the two characters, and what is at stake.
2. CONVERSATION: A substantive back-and-forth dialogue between the 2 characters (at least 8 distinct conversational turns).
   - Naturally weave the target word '{german}' (or its correct conjugated/inflected German forms) into the dialogue across multiple turns (at least 3 times).
   - Each turn should be a natural, rich conversational paragraph, not just one brief sentence.
3. TRANSLATION: A complete, faithful English translation of the entire dialogue with the exact same speaker names.

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:
THEME: <1-sentence specific scenario and characters>

GERMAN CONVERSATION:
Speaker1: <German dialogue turn>
Speaker2: <German dialogue turn>
...

ENGLISH TRANSLATION:
Speaker1: <English translation>
Speaker2: <English translation>
...

Do not output any introductory or concluding meta-commentary."""

    return prompt, selected_domain


def parse_scenario_response(text: str, domain: str) -> ScenarioDialogue:
    """Parse the raw LLM output into theme, German dialogue paragraphs, and English translations."""
    theme = f"Real-World Context ({domain})"
    german_paragraphs: list[tuple[str, str]] = []
    english_paragraphs: list[tuple[str, str]] = []

    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    current_section = "preamble"

    for line in lines:
        upper = line.upper()
        if upper.startswith("THEME:"):
            theme = line.split(":", 1)[1].strip()
            continue
        elif "GERMAN CONVERSATION:" in upper or "GERMAN DIALOGUE:" in upper:
            current_section = "german"
            continue
        elif "ENGLISH TRANSLATION:" in upper or "ENGLISH:" in upper:
            current_section = "english"
            continue

        if ":" in line:
            parts = line.split(":", 1)
            speaker = parts[0].strip().replace("*", "")
            content = parts[1].strip()
            if speaker and content:
                if current_section == "german":
                    german_paragraphs.append((speaker, content))
                elif current_section == "english":
                    english_paragraphs.append((speaker, content))
        else:
            if current_section == "german" and german_paragraphs:
                prev_spk, prev_txt = german_paragraphs[-1]
                german_paragraphs[-1] = (prev_spk, f"{prev_txt} {line}")
            elif current_section == "english" and english_paragraphs:
                prev_spk, prev_txt = english_paragraphs[-1]
                english_paragraphs[-1] = (prev_spk, f"{prev_txt} {line}")

    if not german_paragraphs and lines:
        for line in lines:
            if ":" in line:
                spk, txt = line.split(":", 1)
                german_paragraphs.append((spk.strip(), txt.strip()))

    return ScenarioDialogue(
        domain=domain,
        theme=theme,
        german_paragraphs=german_paragraphs,
        english_paragraphs=english_paragraphs,
    )


def generate_scenario(
    german: str,
    english: str,
    pos: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
) -> ScenarioDialogue:
    """Call Ollama local LLM to synthesize a full-spectrum dialogue scenario."""
    prompt, domain = build_scenario_prompt(german, english, pos)
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
            parsed = parse_scenario_response(raw_response, domain)
            if not parsed.german_paragraphs:
                raise OllamaError("Failed to parse scenario dialogue from LLM response. Please try again.")
            return parsed

    except httpx.ConnectError:
        raise OllamaError(
            "Ollama is not running or unreachable at http://localhost:11434.\n"
            "Please start Ollama with 'ollama serve'."
        )
    except httpx.TimeoutException:
        raise OllamaError(
            f"Ollama request timed out after {int(REQUEST_TIMEOUT)}s.\n"
            "Generating a deep multi-paragraph scenario takes time. Please try again or use a faster model."
        )
    except httpx.HTTPStatusError as e:
        raise OllamaError(f"Ollama HTTP error ({e.response.status_code}): {e.response.text}")
    except OllamaError:
        raise
    except Exception as e:
        raise OllamaError(f"Unexpected error communicating with Ollama: {e}")


def unload_model(model: str = DEFAULT_MODEL, base_url: str = DEFAULT_OLLAMA_URL) -> None:
    """Instruct Ollama to immediately unload the model from memory upon session end.
    
    If kloop spawned the background 'ollama serve' process, terminate it cleanly.
    """
    global _SPAWNED_OLLAMA_PROC
    payload = {
        "model": model,
        "keep_alive": 0,
    }
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(base_url, json=payload)
    except Exception:
        pass

    if _SPAWNED_OLLAMA_PROC is not None:
        try:
            _SPAWNED_OLLAMA_PROC.terminate()
            _SPAWNED_OLLAMA_PROC.wait(timeout=2.0)
        except Exception:
            try:
                _SPAWNED_OLLAMA_PROC.kill()
            except Exception:
                pass
        finally:
            _SPAWNED_OLLAMA_PROC = None
