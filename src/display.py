"""Rich terminal display rendering for KontextLoop."""

from __future__ import annotations

import re
from typing import Any

from rich import box
from rich.align import Align
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def get_core_word(german: str) -> str:
    """Extract the main target word to highlight (ignoring articles like 'der', 'die', 'das', or 'zu')."""
    cleaned = german.strip()
    lower = cleaned.lower()
    for prefix in ("der ", "die ", "das ", "zu "):
        if lower.startswith(prefix):
            return cleaned[len(prefix):].strip()
    return cleaned


def highlight_target_word(sentence: str, target: str) -> str:
    """Highlight all occurrences of target word in the sentence with bold yellow using Rich markup.
    
    Case-insensitive matching that preserves original casing in the sentence.
    """
    core_word = get_core_word(target)
    if not core_word:
        return escape(sentence)

    # Escape the core word for regex
    pattern = re.compile(rf"\b({re.escape(core_word)})\b", flags=re.IGNORECASE)

    # First escape any potential rich tags in the raw sentence
    escaped_sentence = escape(sentence)
    
    # Replace matched occurrences with bold yellow markup
    highlighted = pattern.sub(r"[bold yellow]\1[/bold yellow]", escaped_sentence)
    return highlighted


def display_word_header(german: str, english: str) -> None:
    """Render the word header panel with rounded border, large bold cyan word, and dim italic translation."""
    # Format word with slight spacing for aesthetic title presentation
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


def display_sentences(sentences: list[tuple[str, str]], target_word: str) -> None:
    """Display German sentences with highlighted target word and dim English translation below."""
    for idx, (de_sentence, en_sentence) in enumerate(sentences, start=1):
        highlighted_de = highlight_target_word(de_sentence, target_word)
        console.print(f"  [bold white]{idx}.[/bold white] {highlighted_de}")
        console.print(f"        [dim]{escape(en_sentence)}[/dim]")
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
        console.print("[dim]No vocabulary stored yet. Add pairs using 'vokabel add <file.txt>'[/dim]")
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
