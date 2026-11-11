"""Ollama HTTP client and full-spectrum CEFR-adapted scenario generator for KontextLoop."""

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

# CEFR synonym tiers: sentence length and conversational pacing stay constant,
# but lexical density, synonym sophistication, and register adapt strictly to the level.
CEFR_SYNONYM_PROFILES: dict[str, dict[str, str]] = {
    "A1": {
        "register": "Elementary & Direct",
        "synonym_rule": (
            "Use only the most basic, high-frequency German everyday words (A1 tier). "
            "Use simple core synonyms (e.g., 'gut', 'schlecht', 'machen', 'sagen', 'wichtig', 'brauchen'). "
            "Keep sentence lengths balanced and clear without abstract jargon."
        ),
    },
    "A2": {
        "register": "Routine Practical",
        "synonym_rule": (
            "Use common everyday practical synonyms (A2 tier) like 'aufpassen', 'notwendig', 'erklären', 'helfen'. "
            "Maintain the same conversational length but avoid specialized academic or literary terms."
        ),
    },
    "B1": {
        "register": "Conversational Intermediate",
        "synonym_rule": (
            "Use standard versatile intermediate synonyms (B1 tier) like 'aufbewahren', 'unterstützen', 'wesentlich', 'sich verhalten', 'begründen'. "
            "Natural, expressive colloquial German with realistic pacing."
        ),
    },
    "B2": {
        "register": "Advanced Nuanced & Professional",
        "synonym_rule": (
            "Elevate the vocabulary using advanced professional and idiomatic synonyms (B2 tier) "
            "like 'beibehalten', 'gewährleisten', 'plädieren', 'gravierend', 'berücksichtigen', 'konstatieren'. "
            "Retain the exact conversational sentence length, but replace generic terms with precise, sophisticated synonyms."
        ),
    },
    "C1": {
        "register": "Elevated Academic & Idiomatic",
        "synonym_rule": (
            "Use formal, highly distinguished, and specialized synonyms (C1 tier) "
            "like 'konservieren', 'wahren', 'unumgänglich', 'tangieren', 'insinuieren', 'revidieren'. "
            "Keep the dialogue turns normalized to the same length, but maximize lexical density and domain precision."
        ),
    },
    "C2": {
        "register": "Literary & Rhetorical Mastery",
        "synonym_rule": (
            "Employ literary, philosophically precise, and rare German synonyms (C2 tier) "
            "such as 'perpetuieren', 'obliegen', 'diffizil', 'manifestieren', 'unstrittig', 'immanent'. "
            "Keep sentence rhythm and length normalized, while achieving absolute native eloquence and stylistic elegance."
        ),
    },
}


class OllamaError(Exception):
    """Custom exception for Ollama communication errors with user-friendly messages."""


@dataclass
class ScenarioDialogue:
    """Represents a rich, full-spectrum dialogue scenario and its translation."""
    domain: str
    theme: str
    level: str
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


def build_scenario_prompt(german: str, english: str, pos: str, level: str = "B1") -> tuple[str, str]:
    """Build a prompt dynamically steered by a full-spectrum domain category and normalized CEFR synonym level.
    
    Returns:
        tuple[prompt, selected_domain]
    """
    selected_domain = random.choice(SPECTRUM_DOMAINS)
    norm_level = level.upper() if level.upper() in CEFR_SYNONYM_PROFILES else "B1"
    profile = CEFR_SYNONYM_PROFILES[norm_level]

    prompt = f"""You are a master German linguistic stylist and dramatist creating realistic dialogues across human reality.

Domain focus: {selected_domain}
Target word: {german} (English meaning: {english}, Part of speech: {pos})
Target CEFR Difficulty Level: {norm_level} ({profile['register']})

LEXICAL & SYNONYM LEVEL REQUIREMENT:
{profile['synonym_rule']}
Crucial constraint: Keep conversational paragraph lengths and sentence structures natural and normalized (consistent length across all levels), but strictly calibrate the chosen words, synonyms, and lexical register to the {norm_level} standard.

TASK:
Write an authentic, immersive 2-person German conversation between 2 characters with differing perspectives within this domain.

REQUIREMENTS:
1. THEME: 1-sentence description of the specific scenario and what is at stake.
2. CONVERSATION: A substantive back-and-forth dialogue between the 2 characters (8 distinct conversational turns).
   - Naturally weave the target word '{german}' (or its correct conjugated/inflected German forms) into the dialogue across multiple turns (at least 3 times).
   - Calibrate all surrounding nouns, verbs, and descriptive adjectives to the {norm_level} synonym tier while maintaining normalized sentence length.
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


def parse_scenario_response(text: str, domain: str, level: str) -> ScenarioDialogue:
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
        level=level,
        german_paragraphs=german_paragraphs,
        english_paragraphs=english_paragraphs,
    )


def generate_scenario(
    german: str,
    english: str,
    pos: str,
    level: str = "B1",
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
) -> ScenarioDialogue:
    """Call Ollama local LLM to synthesize a full-spectrum dialogue scenario calibrated to a CEFR synonym level."""
    prompt, domain = build_scenario_prompt(german, english, pos, level=level)
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
            parsed = parse_scenario_response(raw_response, domain, level)
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
