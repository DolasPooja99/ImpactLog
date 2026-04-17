import json
from datetime import date
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, USER_NAME
from storage.db import save_standup
from agent.github_fetcher import fetch_github_activity, is_github_configured

console = Console()
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _display_github_activity(activity: dict):
    commits = activity["commits"]
    prs = activity["prs"]

    if not commits and not prs:
        console.print("[dim]No GitHub activity found for today.[/dim]\n")
        return

    console.print("[bold cyan]Today's GitHub Activity:[/bold cyan]")

    if commits:
        table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 1))
        table.add_column("Repo", style="dim", no_wrap=True)
        table.add_column("Commit")
        for c in commits:
            table.add_row(c["repo"], c["message"])
        console.print(table)

    if prs:
        console.print()
        for pr in prs:
            state_color = "green" if pr["state"] == "open" else "yellow"
            console.print(f"  PR [{state_color}]{pr['state']}[/{state_color}] [{pr['repo']}] {pr['title']}")

    console.print()


def _build_github_context(activity: dict) -> str:
    lines = []
    for c in activity["commits"]:
        lines.append(f"- Commit in {c['repo']}: {c['message']}")
    for pr in activity["prs"]:
        lines.append(f"- PR ({pr['state']}) in {pr['repo']}: {pr['title']}")
    return "\n".join(lines) if lines else ""


def collect_standup_input(github_activity: dict) -> dict:
    console.print(Panel(f"[bold green]Daily Standup — {date.today()}[/bold green]", expand=False))
    console.print(f"\nHey [bold]{USER_NAME}[/bold]! Let's log today's standup.\n")

    _display_github_activity(github_activity)

    yesterday = Prompt.ask("[cyan]What did you work on yesterday?[/cyan]")
    today = Prompt.ask("[cyan]What are you working on today?[/cyan]")
    blockers = Prompt.ask("[cyan]Any blockers? (press Enter to skip)[/cyan]", default="None")

    return {"yesterday": yesterday, "today": today, "blockers": blockers}


def parse_with_claude(raw: dict, github_context: str) -> dict:
    github_section = f"\nGitHub activity today:\n{github_context}" if github_context else ""

    prompt = f"""
You are a career tracking assistant. A software professional just filled in their daily standup.

Standup:
- Yesterday: {raw['yesterday']}
- Today: {raw['today']}
- Blockers: {raw['blockers']}
{github_section}

Extract and return a JSON object with:
- "wins": a concise list of accomplishments from yesterday (list of strings). If GitHub commits are provided, incorporate them as evidence of real work done.
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
    github_activity = {"commits": [], "prs": []}

    if is_github_configured():
        console.print("[yellow]Fetching your GitHub activity...[/yellow]")
        github_activity = fetch_github_activity()
    else:
        console.print("[dim]GitHub not configured — skipping. Add GITHUB_TOKEN + GITHUB_USERNAME to .env to enable.[/dim]\n")

    raw = collect_standup_input(github_activity)
    github_context = _build_github_context(github_activity)

    console.print("\n[yellow]Analyzing your standup with Claude...[/yellow]")
    parsed = parse_with_claude(raw, github_context)

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
