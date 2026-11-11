"""Ollama HTTP client and target-word synonym spectrum engine for KontextLoop."""

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

# CEFR synonym tiers for the target word itself:
CEFR_SYNONYM_PROFILES: dict[str, dict[str, str]] = {
    "A1": {
        "register": "Elementary & Basic Synonyms",
        "synonym_rule": (
            "Identify 2-3 most basic, everyday synonyms or replacement phrases for the target word '{german}' "
            "(e.g. simple high-frequency verbs/nouns that an A1/A2 learner uses in basic communication). "
            "In the dialogue, use '{german}' and actively use these basic synonyms."
        ),
    },
    "B1": {
        "register": "Standard Intermediate Synonyms",
        "synonym_rule": (
            "Identify 3-4 natural intermediate German synonyms for the target word '{german}' "
            "(solid everyday communicative synonyms used by native speakers in general conversation). "
            "In the dialogue, use '{german}' and actively employ these intermediate synonyms across the turns."
        ),
    },
    "B2": {
        "register": "Advanced Nuanced & Professional Synonyms",
        "synonym_rule": (
            "Identify 3-4 advanced, professional, and precise synonyms for the target word '{german}' "
            "(idiomatic, formal, and specialized terms used in sophisticated workplace or intellectual discussions). "
            "In the dialogue, showcase '{german}' and actively demonstrate how these B2 synonyms replace and enrich the target concept."
        ),
    },
    "C1": {
        "register": "Elevated Academic & Stylistic Synonyms",
        "synonym_rule": (
            "Identify 3-4 elevated, formal, academic, or literary synonyms for the target word '{german}' "
            "(distinguished, rhetorically precise, and nuanced German terms). "
            "In the dialogue, feature '{german}' and weave these elevated C1 synonyms into the characters' speech."
        ),
    },
}


class OllamaError(Exception):
    """Custom exception for Ollama communication errors with user-friendly messages."""


@dataclass
class ScenarioDialogue:
    """Represents a rich, full-spectrum dialogue scenario with target word and synonyms."""
    domain: str
    theme: str
    level: str
    synonyms: list[str] = field(default_factory=list)  # Active synonyms of target word
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


def build_scenario_prompt(
    german: str,
    english: str,
    pos: str,
    level: str = "B1",
    fixed_domain: str | None = None,
    fixed_theme: str | None = None,
) -> tuple[str, str, str | None]:
    """Build a prompt generating a dialogue specifically showcasing target word synonyms at CEFR level.
    
    Returns:
        tuple[prompt, selected_domain, fixed_theme]
    """
    selected_domain = fixed_domain or random.choice(SPECTRUM_DOMAINS)
    norm_level = level.upper() if level.upper() in CEFR_SYNONYM_PROFILES else "B1"
    profile = CEFR_SYNONYM_PROFILES[norm_level]

    scenario_instruction = (
        f"Maintain the exact premise/characters: '{fixed_theme}', but adapt the conversation to CEFR {norm_level} level."
        if fixed_theme
        else f"Create an authentic scenario within: {selected_domain}."
    )

    prompt = f"""You are an elite German lexicographer and dramatic scriptwriter helping learners master synonyms in context.

Target Word: {german} (English meaning: {english}, Part of speech: {pos})
Target CEFR Difficulty Level: {norm_level} ({profile['register']})
Domain Focus: {selected_domain}

PRIMARY GOAL:
Teach the learner how the target concept '{german}' is expressed at the {norm_level} level using level-appropriate synonyms.

REQUIREMENTS:
1. SYNONYMS: Provide 3-4 German synonyms or exact equivalent phrases for '{german}' that belong to the {norm_level} tier.
2. THEME: 1-sentence description of the scenario ({scenario_instruction}).
3. GERMAN CONVERSATION: Write a 6-to-8 turn dialogue between 2 characters.
   - The speakers must use the target word '{german}' AND actively use the 3-4 identified {norm_level} synonyms in natural context.
   - Keep overall dialogue turn lengths natural, realistic, and normalized.
4. ENGLISH TRANSLATION: Provide the complete matching English translation preserving the subtle distinctions of each synonym.

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:
SYNONYMS: <synonym1>, <synonym2>, <synonym3>
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

    return prompt, selected_domain, fixed_theme


def parse_scenario_response(text: str, domain: str, level: str) -> ScenarioDialogue:
    """Parse the raw LLM output into theme, synonyms, German dialogue paragraphs, and English translations."""
    theme = f"Real-World Context ({domain})"
    synonyms: list[str] = []
    german_paragraphs: list[tuple[str, str]] = []
    english_paragraphs: list[tuple[str, str]] = []

    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    current_section = "preamble"

    for line in lines:
        upper = line.upper()
        if upper.startswith("SYNONYMS:"):
            raw_syns = line.split(":", 1)[1].strip()
            synonyms = [s.strip().replace("*", "") for s in re.split(r"[,;•]", raw_syns) if s.strip()]
            continue
        elif upper.startswith("THEME:"):
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
        synonyms=synonyms,
        german_paragraphs=german_paragraphs,
        english_paragraphs=english_paragraphs,
    )


def generate_scenario(
    german: str,
    english: str,
    pos: str,
    level: str = "B1",
    fixed_domain: str | None = None,
    fixed_theme: str | None = None,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
) -> ScenarioDialogue:
    """Call Ollama local LLM to synthesize a full-spectrum dialogue showcasing level-adapted synonyms."""
    prompt, domain, _ = build_scenario_prompt(
        german, english, pos, level=level, fixed_domain=fixed_domain, fixed_theme=fixed_theme
    )
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
            "Generating the scenario took too long. Please try again."
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
