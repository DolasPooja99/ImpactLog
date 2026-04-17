import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from storage.db import get_all_standups

console = Console()


def _truncate(text: str, limit: int = 50) -> str:
    return text if len(text) <= limit else text[:limit - 1] + "…"


def show_history():
    standups = get_all_standups()

    if not standups:
        console.print(Panel("[yellow]No standups logged yet. Run option 1 to log your first one![/yellow]", expand=False))
        return

    console.print(f"\n[bold green]Standup History[/bold green] — {len(standups)} entries\n")

    while True:
        console.print("[1] View all  [2] Last 7 days  [3] Last 30 days  [4] Back")
        choice = Prompt.ask("Filter", choices=["1", "2", "3", "4"])

        if choice == "4":
            return

        if choice == "1":
            entries = standups
        elif choice == "2":
            entries = standups[:7]
        elif choice == "3":
            entries = standups[:30]

        _render_table(entries)
        break


def _render_table(entries: list):
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        row_styles=["", "dim"],
        expand=False,
    )

    table.add_column("Date", style="bold", width=12)
    table.add_column("Worked On", width=40)
    table.add_column("Wins", width=40)
    table.add_column("Tags", width=30)

    for s in entries:
        wins_raw = s.get("wins", "")
        tags_raw = s.get("tags", "")

        try:
            wins_list = json.loads(wins_raw) if wins_raw else []
            wins_text = " • ".join(wins_list) if wins_list else "—"
        except (json.JSONDecodeError, TypeError):
            wins_text = wins_raw or "—"

        try:
            tags_list = json.loads(tags_raw) if tags_raw else []
            tags_text = ", ".join(tags_list) if tags_list else "—"
        except (json.JSONDecodeError, TypeError):
            tags_text = tags_raw or "—"

        table.add_row(
            s.get("date", ""),
            _truncate(s.get("yesterday", "") or "—"),
            _truncate(wins_text, 60),
            _truncate(tags_text, 30),
        )

    console.print(table)
    console.print(f"\n[dim]{len(entries)} standup(s) shown.[/dim]\n")
