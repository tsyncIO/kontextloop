"""Rich terminal display rendering for KontextLoop with target-word and synonym highlighting."""

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

# Speaker color palette
SPEAKER_COLORS = ["cyan", "bright_green", "magenta", "yellow", "blue"]


def get_core_word(german: str) -> str:
    """Extract the main target word to highlight (ignoring articles like 'der', 'die', 'das', or 'zu')."""
    cleaned = german.strip()
    lower = cleaned.lower()
    for prefix in ("der ", "die ", "das ", "zu "):
        if lower.startswith(prefix):
            return cleaned[len(prefix):].strip()
    return cleaned


def highlight_word_and_synonyms(text: str, target: str, synonyms: list[str]) -> str:
    """Highlight target word in bold yellow and its level synonyms in bold cyan."""
    escaped_text = escape(text)

    # 1. Highlight level-adapted synonyms in bold cyan
    for syn in synonyms:
        core_syn = get_core_word(syn)
        if len(core_syn) > 2:
            stem = core_syn[:-2] if len(core_syn) > 4 and core_syn.lower().endswith("en") else core_syn
            syn_pattern = re.compile(rf"\b({re.escape(stem)}(?:[a-zäöüß]{{0,4}})?)\b", flags=re.IGNORECASE)
            escaped_text = syn_pattern.sub(r"[bold cyan]\1[/bold cyan]", escaped_text)

    # 2. Highlight target word in bold yellow (takes precedence)
    core_word = get_core_word(target)
    if core_word:
        stem = core_word[:-2] if len(core_word) > 4 and core_word.lower().endswith("en") else core_word
        target_pattern = re.compile(rf"\b({re.escape(stem)}(?:[a-zäöüß]{{0,4}})?)\b", flags=re.IGNORECASE)
        # Avoid replacing tags themselves
        escaped_text = target_pattern.sub(r"[bold yellow]\1[/bold yellow]", escaped_text)

    return escaped_text


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
    """Display the full-spectrum scenario dialogue with CEFR badge, synonym cluster, highlighted dialogue, and English translation."""
    # 1. Thematic Scenario & Synonym Banner
    scenario_info = Text()
    scenario_info.append("Domain: ", style="bold magenta")
    scenario_info.append(f"{scenario.domain}   ", style="white")

    level_colors = {"A1": "green", "A2": "green", "B1": "yellow", "B2": "bright_yellow", "C1": "cyan", "C2": "bold magenta"}
    lvl_color = level_colors.get(scenario.level.upper(), "yellow")
    scenario_info.append(f"CEFR Level: [{scenario.level.upper()}]\n", style=f"bold {lvl_color}")

    # Active level-calibrated synonyms
    if scenario.synonyms:
        scenario_info.append(f"Level {scenario.level.upper()} Synonyms: ", style="bold cyan")
        scenario_info.append(" • ".join(scenario.synonyms) + "\n", style="bold white")

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
    console.print("[dim]Legend: [bold yellow]Target Word[/bold yellow]  |  [bold cyan]Level Synonyms[/bold cyan][/dim]\n")

    for speaker, paragraph in scenario.german_paragraphs:
        color = speaker_color_map.get(speaker, "cyan")
        highlighted_p = highlight_word_and_synonyms(paragraph, target_word, scenario.synonyms)
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
    """Display the interactive navigation prompt with level adaptation options."""
    console.print("  [dim][Enter][/dim] next word  [dim][1][/dim] A1  [dim][2][/dim] B1  [dim][3][/dim] B2  [dim][4][/dim] C1  [dim][q][/dim] quit: ", end="")


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
