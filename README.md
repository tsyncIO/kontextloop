# KontextLoop

> A context-driven synthesis engine and terminal runtime for accelerated immersive learning.

KontextLoop (`kloop`) is an offline Python terminal application designed for contextual German vocabulary acquisition. It pairs local LLM generation (via Ollama) with a rich terminal interface to present target words in diverse, realistic everyday sentences with highlighting and English translations.

---

## Features

- **Context-First Learning:** Generates 6–8 natural everyday German sentences for each target word.
- **Rich Terminal UI:** Visual header panels, case-insensitive bold yellow target word highlighting, and dim/gray English sentence translations.
- **Local & Offline:** Communicates with a local Ollama instance (`llama3.1:8b` by default, or `qwen2.5:3b`). Zero cloud API keys or external dependencies required.
- **Smart Grammar Ingestion:** Automatically detects articles (`der`, `die`, `das`) for noun capitalization, infinitive verbs (`zu`), and flexible delimiters (`-`, `=`, `;`).
- **Graceful Error Handling:** Provides helpful guidance instead of raw tracebacks if Ollama is unreachable.

---

## Quick Start

### 1. Requirements

- Python `>=3.11`
- [uv](https://github.com/astral-sh/uv)
- [Ollama](https://ollama.com/)

### 2. Pull a Model

```bash
# Recommended default model
ollama pull llama3.1:8b

# Or lightweight model (for machines with <4 GB RAM)
ollama pull qwen2.5:3b
```

Ensure the Ollama server is running:
```bash
ollama serve
```

### 3. Add Vocabulary

Prepare a text file (`vocab.txt`) with German-English pairs:
```text
behalten - to keep / to retain
der Apfel = the apple
die Wohnung; the apartment
zu verstehen - to understand
```

Ingest into storage:
```bash
uv run kloop add vocab.txt
```

### 4. Start a Learning Session

```bash
# Start a default session (10 words with llama3.1:8b)
uv run kloop session

# Custom session length or model
uv run kloop session --words 5 --model qwen2.5:3b
```

In the session:
- Press **`Enter`** to advance to the next word.
- Press **`q`** to end the session early and view the session summary.

---

## CLI Reference

| Command | Description |
|---|---|
| `uv run kloop add <file.txt>` | Ingest German–English vocabulary pairs from a file |
| `uv run kloop session [--words N] [--model MODEL]` | Start an interactive context session |
| `uv run kloop list` | Display all stored vocabulary in a formatted table |
| `uv run kloop reset` | Clear all stored vocabulary |
