import json
from datetime import date
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, USER_NAME
from storage.db import save_standup

console = Console()
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def collect_standup_input() -> dict:
    console.print(Panel(f"[bold green]Daily Standup — {date.today()}[/bold green]", expand=False))
    console.print(f"\nHey [bold]{USER_NAME}[/bold]! Let's log today's standup.\n")

    yesterday = Prompt.ask("[cyan]What did you work on yesterday?[/cyan]")
    today = Prompt.ask("[cyan]What are you working on today?[/cyan]")
    blockers = Prompt.ask("[cyan]Any blockers? (press Enter to skip)[/cyan]", default="None")

    return {"yesterday": yesterday, "today": today, "blockers": blockers}


def parse_with_claude(raw: dict) -> dict:
    prompt = f"""
You are a career tracking assistant. A software professional just filled in their daily standup.

Standup:
- Yesterday: {raw['yesterday']}
- Today: {raw['today']}
- Blockers: {raw['blockers']}

Extract and return a JSON object with:
- "wins": a concise list of accomplishments from yesterday (list of strings)
- "tags": relevant skill/project tags (e.g. ["Python", "API", "bug-fix", "feature"]) (list of strings, max 5)
- "summary": one sentence summary of yesterday's work

Return only valid JSON, no extra text.
"""
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.content[0].text)


def run_standup():
    raw = collect_standup_input()

    console.print("\n[yellow]Analyzing your standup with Claude...[/yellow]")
    parsed = parse_with_claude(raw)

    wins = parsed.get("wins", [])
    tags = parsed.get("tags", [])
    summary = parsed.get("summary", "")

    save_standup(
        date=str(date.today()),
        yesterday=raw["yesterday"],
        today=raw["today"],
        blockers=raw["blockers"],
        wins=json.dumps(wins),
        tags=tags,
        raw_input=str(raw)
    )

    console.print(Panel(
        f"[bold]Summary:[/bold] {summary}\n\n"
        f"[bold]Wins:[/bold] {', '.join(wins) if wins else 'None logged'}\n"
        f"[bold]Tags:[/bold] {', '.join(tags)}",
        title="[green]Standup Logged[/green]",
        expand=False
    ))
