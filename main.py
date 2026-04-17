from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from storage.db import init_db
from agent.standup import run_standup
from agent.digest import generate_weekly_digest

console = Console()


def show_menu():
    console.print(Panel(
        "[bold green]ImpactLog[/bold green] — Track your wins. Own your career.\n\n"
        "[1] Log today's standup\n"
        "[2] View weekly digest\n"
        "[3] Exit",
        title="Main Menu",
        expand=False
    ))
    return Prompt.ask("\nChoose", choices=["1", "2", "3"])


def main():
    init_db()  # create DB tables if they don't exist yet

    console.print("\n[bold green]Welcome to ImpactLog[/bold green]\n")

    while True:
        choice = show_menu()

        if choice == "1":
            run_standup()
        elif choice == "2":
            generate_weekly_digest()
        elif choice == "3":
            console.print("\n[green]Keep shipping! See you tomorrow.[/green]\n")
            break


if __name__ == "__main__":
    main()
