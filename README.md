# KontextLoop

> A context-driven synthesis engine and terminal runtime for accelerated immersive learning.

KontextLoop (`kloop`) is an offline Python terminal application designed for contextual German vocabulary acquisition. It pairs local LLM generation (via Ollama) with a rich terminal interface to present target words in diverse, realistic everyday sentences with highlighting and English translations.

---

## Highlights

- **Context-First Learning:** Synthesizes 6–8 natural everyday German sentences for each target word across realistic contexts.
- **Rich Terminal UI:** Visual header panels, case-insensitive bold yellow target word highlighting, and dim/gray English sentence translations.
- **Embedded Lifecycle Management:**
  - **Auto-Serve:** Automatically detects and launches `ollama serve` in the background if it is not already running.
  - **Zero RAM Leak:** Automatically unloads the model from RAM/VRAM immediately upon session completion (`keep_alive: 0`).
- **Smart Grammar Ingestion:** Automatically recognizes articles (`der`, `die`, `das`) for noun capitalization, infinitive verbs (`zu`), and flexible delimiters (`-`, `=`, `;`).
- **Fully Offline:** Works directly with your local Ollama runtime (`llama3.1:8b` by default, or `qwen2.5:3b`). Zero cloud API keys or external services required.

---

## Quick Start

### 1. Requirements

- Python `>=3.11`
- [uv](https://github.com/astral-sh/uv)
- [Ollama](https://ollama.com/)

### 2. Pull a Model

Pull your preferred model (one-time download):

```bash
# Recommended default model
ollama pull llama3.1:8b

# Or lightweight model (for machines with <4 GB RAM)
ollama pull qwen2.5:3b
```

*(Note: You do not need to manually run `ollama serve` — `kloop` starts it automatically if needed!)*

### 3. Ingest Vocabulary

Create a text file (`vocab.txt`) with German–English word pairs using flexible delimiters (`-`, `=`, `;`):

```text
behalten - to keep / to retain
der Apfel = the apple
die Wohnung; the apartment
zu verstehen - to understand
```

Import it into storage:

```bash
uv run kloop add vocab.txt
```

### 4. Run an Interactive Session

```bash
# Start a default session (10 words with llama3.1:8b)
uv run kloop session

# Custom session length or custom model
uv run kloop session --words 5 --model qwen2.5:3b
```

During the session:
- Press **`Enter`** to advance to the next word.
- Press **`q`** to quit anytime and view your session summary.

---

## CLI Reference

| Command | Description |
|---|---|
| `uv run kloop add <file.txt>` | Ingest German–English vocabulary pairs from a file |
| `uv run kloop session [--words N] [--model MODEL]` | Start an interactive contextual learning session |
| `uv run kloop list` | Display all stored vocabulary in a formatted Rich table |
| `uv run kloop reset` | Clear all stored vocabulary from storage |

---

## Architecture & Layout

```
kontextloop/
├── pyproject.toml        # UV project configuration and kloop CLI entrypoint
├── README.md             # Project documentation
├── spec.txt              # Specification
├── vocab.txt             # Sample vocabulary
└── src/
    ├── __init__.py       # Package marker
    ├── main.py           # CLI routing and session lifecycle controller
    ├── ingestion.py      # Delimiter parsing and grammar normalization
    ├── storage.py        # ~/.kontextloop/vocab.json persistence layer
    ├── llm.py            # Ollama client, auto-serve, and model unload manager
    └── display.py        # Rich terminal panels, tables, and sentence highlighting
```
