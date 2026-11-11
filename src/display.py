"""Rich terminal display rendering for KontextLoop with full-spectrum dialogues."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from rich import box
from rich.align import Align
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from src.llm import ScenarioDialogue

console = Console()

# Speaker color palette to give characters distinct, visually striking voices
SPEAKER_COLORS = ["cyan", "bright_green", "magenta", "yellow", "blue"]


def get_core_word(german: str) -> str:
    """Extract the main target word to highlight (ignoring articles like 'der', 'die', 'das', or 'zu')."""
    cleaned = german.strip()
    lower = cleaned.lower()
    for prefix in ("der ", "die ", "das ", "zu "):
        if lower.startswith(prefix):
            return cleaned[len(prefix):].strip()
    return cleaned


def highlight_target_word(text: str, target: str) -> str:
    """Highlight all occurrences and stem-related inflections of the target word in bold yellow."""
    core_word = get_core_word(target)
    if not core_word:
        return escape(text)

    # If it's a verb ending in 'en' (e.g. behalten -> behalt), also match inflected forms
    stem = core_word
    if len(core_word) > 4 and core_word.lower().endswith("en"):
        stem = core_word[:-2]

    # Pattern matches core word or stem + common German inflections (e, st, t, en, te, test, tet, ten)
    pattern = re.compile(
        rf"\b({re.escape(stem)}(?:[a-zäöüß]{{0,4}})?)\b",
        flags=re.IGNORECASE,
    )

    escaped_text = escape(text)
    highlighted = pattern.sub(r"[bold yellow]\1[/bold yellow]", escaped_text)
    return highlighted


def display_word_header(german: str, english: str) -> None:
    """Render the word header panel with rounded border, large bold cyan word, and dim italic translation."""
    spaced_word = " ".join(german)
    content = Text()
    content.append(f"{spaced_word}\n", style="bold cyan")
    content.append(f"{english}", style="dim italic")

    panel = Panel(
        Align.center(content),
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 4),
        expand=False,
    )
    console.print()
    console.print(Align.center(panel))
    console.print()


def display_scenario_dialogue(scenario: ScenarioDialogue, target_word: str) -> None:
    """Display the full-spectrum scenario dialogue with CEFR badge, highlighted word and English translation."""
    # 1. Thematic Scenario Banner
    scenario_info = Text()
    scenario_info.append("Domain: ", style="bold magenta")
    scenario_info.append(f"{scenario.domain}  ", style="white")
    
    # CEFR Level badge styling
    level_colors = {"A1": "green", "A2": "green", "B1": "yellow", "B2": "bright_yellow", "C1": "cyan", "C2": "bold magenta"}
    lvl_color = level_colors.get(scenario.level.upper(), "yellow")
    scenario_info.append(f"[{scenario.level.upper()}]\n", style=f"bold {lvl_color}")
    
    scenario_info.append("Scenario: ", style="bold cyan")
    scenario_info.append(f"{scenario.theme}", style="italic white")

    banner = Panel(
        scenario_info,
        box=box.ROUNDED,
        border_style="magenta",
        padding=(0, 2),
        expand=True,
    )
    console.print(banner)
    console.print()

    # Dynamic speaker color mapping
    speakers = list(dict.fromkeys(spk for spk, _ in scenario.german_paragraphs))
    speaker_color_map = {
        spk: SPEAKER_COLORS[i % len(SPEAKER_COLORS)] for i, spk in enumerate(speakers)
    }

    # 2. German Conversation
    console.print(Rule(title="[bold green]German Conversation[/bold green]", style="green"))
    console.print()

    for speaker, paragraph in scenario.german_paragraphs:
        color = speaker_color_map.get(speaker, "cyan")
        highlighted_p = highlight_target_word(paragraph, target_word)
        console.print(f"  [bold {color}]{speaker}:[/bold {color}] {highlighted_p}")
        console.print()

    # 3. English Translation
    if scenario.english_paragraphs:
        console.print(Rule(title="[dim]English Translation[/dim]", style="dim"))
        console.print()
        for speaker, paragraph in scenario.english_paragraphs:
            console.print(f"  [dim][bold]{speaker}:[/bold] {escape(paragraph)}[/dim]")
            console.print()


def display_navigation_prompt() -> None:
    """Display the session navigation prompt."""
    console.print("  [dim][Enter][/dim] next word   [dim][q][/dim] quit: ", end="")


def display_session_summary(words_seen: int, elapsed_seconds: float) -> None:
    """Display the session summary panel."""
    minutes = int(elapsed_seconds // 60)
    seconds = int(elapsed_seconds % 60)
    time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    summary_text = Text()
    summary_text.append("Session Summary\n\n", style="bold green")
    summary_text.append(f"• Words reviewed: ", style="white")
    summary_text.append(f"{words_seen}\n", style="bold cyan")
    summary_text.append(f"• Time elapsed: ", style="white")
    summary_text.append(f"{time_str}\n", style="bold cyan")

    panel = Panel(
        summary_text,
        box=box.ROUNDED,
        border_style="green",
        padding=(1, 3),
        expand=False,
    )
    console.print()
    console.print(panel)


def display_vocab_table(entries: list[dict[str, Any]]) -> None:
    """Display stored vocabulary entries in a formatted Rich table."""
    if not entries:
        console.print("[dim]No vocabulary stored yet. Add pairs using 'kloop add <file.txt>'[/dim]")
        return

    table = Table(
        title="Stored German Vocabulary",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("German", style="bold white", min_width=18)
    table.add_column("English", style="white", min_width=24)
    table.add_column("Type", style="cyan", width=8)
    table.add_column("Added", style="dim", width=12)

    for idx, item in enumerate(entries, start=1):
        meta = item.get("metadata", {})
        pos = meta.get("partOfSpeech", "word")
        added_at = meta.get("addedAt", "")[:10]
        table.add_row(
            str(idx),
            item.get("german", ""),
            item.get("english", ""),
            pos,
            added_at,
        )

    console.print()
    console.print(table)
    console.print(f"[dim]Total: {len(entries)} words[/dim]\n")


def display_error(message: str) -> None:
    """Display an error message in a styled panel."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def display_info(message: str) -> None:
    """Display an informational message."""
    console.print(f"[bold cyan]•[/bold cyan] {message}")


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[bold green]✔[/bold green] {message}")
