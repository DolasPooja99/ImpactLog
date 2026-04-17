import json
from datetime import date
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, USER_NAME
from storage.db import save_standup
from agent.github_fetcher import (
    fetch_yesterday_activity, fetch_today_activity,
    activity_to_text, is_github_configured
)

console = Console()
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _display_activity(activity: dict, label: str):
    commits = activity["commits"]
    prs = activity["prs"]

    if not commits and not prs:
        console.print(f"[dim]No GitHub activity found for {activity['date']}.[/dim]")
        return

    console.print(f"\n[bold cyan]{label}[/bold cyan]")
    if commits:
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("", style="dim", no_wrap=True)
        table.add_column("")
        for c in commits:
            table.add_row(c["repo"], c["message"])
        console.print(table)
    if prs:
        for pr in prs:
            state_color = "green" if pr["state"] == "open" else "yellow"
            console.print(f"  PR [{state_color}]{pr['state']}[/{state_color}] [{pr['repo']}] {pr['title']}")


def collect_standup_input() -> dict:
    console.print(Panel(f"[bold green]Daily Standup — {date.today()}[/bold green]", expand=False))
    console.print(f"\nHey [bold]{USER_NAME}[/bold]! Let's log today's standup.\n")

    yesterday_github = {"commits": [], "prs": []}
    today_github = {"commits": [], "prs": []}

    if is_github_configured():
        console.print("[yellow]Fetching your GitHub activity...[/yellow]")
        yesterday_github = fetch_yesterday_activity()
        today_github = fetch_today_activity()

        _display_activity(yesterday_github, f"Yesterday's GitHub activity ({yesterday_github['date']})")
        _display_activity(today_github, f"Today's GitHub activity so far ({today_github['date']})")
        console.print()
    else:
        console.print("[dim]GitHub not configured — add GITHUB_TOKEN + GITHUB_USERNAME to .env to auto-fill.[/dim]\n")

    # Only ask for things GitHub can't know
    extra = Prompt.ask(
        "\n[cyan]Anything to add that GitHub missed? (meetings, reviews, discussions)[/cyan]\n[dim]Press Enter to skip[/dim]",
        default=""
    )
    today_plan = Prompt.ask("\n[cyan]What are you planning to work on today?[/cyan]")
    blockers = Prompt.ask("\n[cyan]Any blockers?[/cyan]\n[dim]Press Enter to skip[/dim]", default="None")

    return {
        "yesterday_github": activity_to_text(yesterday_github),
        "today_github": activity_to_text(today_github),
        "extra": extra,
        "today_plan": today_plan,
        "blockers": blockers,
    }


def parse_with_claude(raw: dict) -> dict:
    github_yesterday = f"\nGitHub commits/PRs yesterday:\n{raw['yesterday_github']}" if raw["yesterday_github"] else ""
    github_today = f"\nGitHub commits/PRs today so far:\n{raw['today_github']}" if raw["today_github"] else ""
    extra = f"\nAdditional context (meetings/discussions): {raw['extra']}" if raw["extra"] else ""

    prompt = f"""
You are a career tracking assistant helping a software engineer document their daily work.

Data:
{github_yesterday}
{github_today}
{extra}
- Today's plan: {raw['today_plan']}
- Blockers: {raw['blockers']}

Extract and return a JSON object with:
- "wins": list of concrete accomplishments from yesterday's GitHub activity + any extra context (list of strings). Make them impactful — use action verbs, mention repos/features where relevant.
- "yesterday_summary": one sentence summarizing what was accomplished yesterday
- "tags": relevant skill/project tags inferred from the work (list of strings, max 5)

Return only valid JSON, no extra text.
"""
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)


def run_standup():
    raw = collect_standup_input()

    console.print("\n[yellow]Analyzing with Claude...[/yellow]")
    parsed = parse_with_claude(raw)

    wins = parsed.get("wins", [])
    tags = parsed.get("tags", [])
    summary = parsed.get("yesterday_summary", "")

    save_standup(
        date=str(date.today()),
        yesterday=raw["yesterday_github"] or raw["extra"] or "No GitHub activity",
        today=raw["today_plan"],
        blockers=raw["blockers"],
        wins=json.dumps(wins),
        tags=tags,
        raw_input=str(raw)
    )

    console.print(Panel(
        f"[bold]Yesterday:[/bold] {summary}\n\n"
        f"[bold]Wins:[/bold]\n" + "\n".join(f"  • {w}" for w in wins) + "\n\n"
        f"[bold]Tags:[/bold] {', '.join(tags)}",
        title="[green]Standup Logged[/green]",
        expand=False
    ))
