# KontextLoop

> A context-driven synthesis engine and terminal runtime for accelerated immersive learning.

KontextLoop (`kloop`) is an offline Python terminal application designed for contextual German language acquisition. Instead of dry flashcards or generic textbook exercises, KontextLoop pairs a local LLM runtime (via Ollama) with a Rich terminal interface to immerse learners in **substantive, full-spectrum 2-person dialogues** across diverse real-world domains with **interactive CEFR level switching and target-word synonym progression**.

---

## Highlights

- **Target-Word Synonym Progression (A1 $\rightarrow$ C1):**
  - For any target word, discover its exact level-appropriate synonyms in authentic action!
  - Example for **`die Wohnung`**:
    - **A1:** *das Appartement • die Wohnungstube • der Wohnbereich • das Haus*
    - **B2:** *das Domizil • die Bleibe • der Wohnort • das Quartier*
  - Dedicated **Synonym Cluster Bar** displayed right on the scenario banner.
- **Interactive In-Session Level Switching:**
  - Dynamic navigation prompt:
    ```
    [Enter] next word  [1] A1  [2] B1  [3] B2  [4] C1  [q] quit
    ```
  - Seamlessly adapt the current scene and characters to a higher or lower synonym register with a single keypress!
- **Dual Visual Highlighting:**
  - **Bold Yellow**: Target word and its inflected forms.
  - **Bold Cyan**: Level-adapted synonyms actively used in the dialogue.
  - Distinct speaker badges with individual color palettes.
  - Complete, nuanced English translations displayed in **dim/gray** below the German conversation.
- **Full-Spectrum Real-World Scenarios:**
  - Moves far beyond cliché textbook tropes (*"im Supermarkt"*, *"am Bahnhof"*).
  - Dynamically steers dialogues across an expansive spectrum of human reality: heavy trades & industrial logistics, clinical emergency medicine, investigative legal disputes, deep-sea & empirical research, acoustic engineering, intimate family dynamics, archival preservation, and urban subcultures.
- **Embedded Lifecycle Management:**
  - **Auto-Serve:** Automatically launches `ollama serve` in the background if the service is not currently running.
  - **Zero RAM Leak:** Immediately unloads the model from memory upon session exit (`keep_alive: 0`) to free 100% of RAM/VRAM.
- **Smart Grammar Ingestion:** Automatically recognizes articles (`der`, `die`, `das`) for noun capitalization, infinitive verbs (`zu`), and flexible delimiters (`-`, `=`, `;`).
- **Fully Offline:** Runs locally via Ollama (`llama3.1:8b` by default, or `qwen2.5:3b`). Zero cloud API keys or external services required.

---

## Quick Start

### 1. Requirements

- Python `>=3.11`
- [uv](https://github.com/astral-sh/uv)
- [Ollama](https://ollama.com/)

### 2. Pull a Model

Pull your preferred model (one-time download):

```bash
# Recommended default model (best German nuance & coherence)
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
UV_PROJECT_ENVIRONMENT=/tmp/kontextloop-venv uv run kloop add vocab.txt
```

### 4. Run an Interactive Learning Session

```bash
# Start a default session (10 words with llama3.1:8b at B1 level)
UV_PROJECT_ENVIRONMENT=/tmp/kontextloop-venv uv run kloop session

# Start directly at a specific initial level (A1, B1, B2, C1)
UV_PROJECT_ENVIRONMENT=/tmp/kontextloop-venv uv run kloop session --level B2
```

During the session:
- Press **`Enter`** to advance to the next word scenario.
- Press **`1`** for **A1**, **`2`** for **B1**, **`3`** for **B2**, or **`4`** for **C1** to adapt the current scene's synonyms!
- Press **`q`** to quit anytime and view your session summary.

---

## CLI Reference

| Command | Description |
|---|---|
| `uv run kloop add <file.txt>` | Ingest German–English vocabulary pairs from a file |
| `uv run kloop session [--words N] [--level LEVEL] [--model MODEL]` | Start an interactive contextual learning session with instant level switching |
| `uv run kloop list` | Display all stored vocabulary in a formatted Rich table |
| `uv run kloop reset` | Clear all stored vocabulary from storage |

---

## Architecture & Layout

```
kontextloop/
├── pyproject.toml        # UV project configuration and kloop CLI entrypoint
├── uv.lock               # Pinned dependencies lockfile
├── README.md             # Project documentation & usage guide
├── spec.txt              # Specification
├── vocab.txt             # Sample vocabulary
└── src/
    ├── __init__.py       # Package marker
    ├── main.py           # CLI routing, interactive level switcher, and session controller
    ├── ingestion.py      # Delimiter parsing and grammar normalization
    ├── storage.py        # ~/.kontextloop/vocab.json persistence layer
    ├── llm.py            # Target-word synonym engine, full-spectrum prompt generator, Ollama client, auto-serve, and unload manager
    └── display.py        # Rich terminal panels, tables, synonym cluster bars, dual highlighting, and navigation prompt
```
