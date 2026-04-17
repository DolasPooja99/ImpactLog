import json
from datetime import date, timedelta
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, USER_NAME
from storage.db import get_standups_for_week, get_all_standups

console = Console()
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_week_range():
    today = date.today()
    start = today - timedelta(days=today.weekday())  # Monday
    end = start + timedelta(days=6)                  # Sunday
    return str(start), str(end)


def generate_weekly_digest():
    week_start, week_end = get_week_range()
    standups = get_standups_for_week(week_start, week_end)

    if not standups:
        console.print("[yellow]No standups logged this week yet.[/yellow]")
        return

    all_wins = []
    all_tags = []
    entries_text = ""

    for s in standups:
        wins = json.loads(s["wins"]) if s["wins"] else []
        tags = json.loads(s["tags"]) if s["tags"] else []
        all_wins.extend(wins)
        all_tags.extend(tags)
        entries_text += f"\nDate: {s['date']}\nYesterday: {s['yesterday']}\nToday: {s['today']}\nBlockers: {s['blockers']}\n"

    prompt = f"""
You are a career coach helping a software professional document their weekly accomplishments.

Here are their standup entries for the week of {week_start} to {week_end}:
{entries_text}

Generate a weekly digest with:
- "headline": one powerful sentence summarizing the week's impact
- "accomplishments": 3-5 bullet points of key achievements (quantify where possible)
- "skills_demonstrated": list of skills shown this week
- "next_week_focus": suggested focus areas based on blockers/patterns

Return only valid JSON, no extra text.
"""
    console.print("\n[yellow]Generating your weekly digest with Claude...[/yellow]")

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    digest = json.loads(response.content[0].text)

    _display_digest(digest, week_start, week_end, list(set(all_tags)))


def _display_digest(digest: dict, week_start: str, week_end: str, tags: list):
    console.print(Panel(
        f"[bold]{digest.get('headline', '')}[/bold]",
        title=f"[green]Weekly Digest — {week_start} to {week_end}[/green]",
        expand=False
    ))

    console.print("\n[bold cyan]Key Accomplishments:[/bold cyan]")
    for point in digest.get("accomplishments", []):
        console.print(f"  • {point}")

    console.print("\n[bold cyan]Skills Demonstrated:[/bold cyan]")
    console.print(f"  {', '.join(digest.get('skills_demonstrated', []))}")

    console.print("\n[bold cyan]Suggested Focus Next Week:[/bold cyan]")
    for point in digest.get("next_week_focus", []):
        console.print(f"  → {point}")

    console.print(f"\n[bold cyan]Tags This Week:[/bold cyan] {', '.join(tags)}")
