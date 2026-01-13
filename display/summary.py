"""
Summary display functions for Worklog CLI.
"""

from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def display_summary(date: datetime, events: list, searches: list, commits: list):
    """Display a formatted summary of the day's activities."""
    date_str = date.strftime("%A, %B %d, %Y")

    console.print()
    console.print(Panel(f"[bold cyan]Work Summary for {date_str}[/bold cyan]", box=box.DOUBLE))
    console.print()

    # Calendar Events
    console.print("[bold magenta]📅 Calendar Events[/bold magenta]")
    if events:
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Time", style="cyan", width=20)
        table.add_column("Event", style="white")
        table.add_column("Duration", style="green", width=12)

        for event in events:
            table.add_row(event["time"], event["summary"], event["duration"])
        console.print(table)
    else:
        console.print("  [dim]No calendar events found[/dim]")
    console.print()

    # Chrome Search History
    console.print("[bold blue]🔍 Search History[/bold blue]")
    if searches:
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Time", style="cyan", width=12)
        table.add_column("Search Query / Page Title", style="white")
        table.add_column("URL", style="dim", max_width=50, overflow="ellipsis")

        # Group and deduplicate, show top 20
        seen = set()
        count = 0
        for search in searches:
            key = search["title"].lower()
            if key not in seen and count < 20:
                seen.add(key)
                table.add_row(search["time"], search["title"], search["url"])
                count += 1
        console.print(table)
        if len(searches) > 20:
            console.print(f"  [dim]... and {len(searches) - 20} more entries[/dim]")
    else:
        console.print("  [dim]No search history found[/dim]")
    console.print()

    # GitHub Commits
    console.print("[bold green]💻 GitHub Commits[/bold green]")
    if commits:
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Time", style="cyan", width=12)
        table.add_column("Repository", style="yellow", width=25)
        table.add_column("Commit Message", style="white")
        table.add_column("Changes", style="green", width=15)

        for commit in commits:
            table.add_row(
                commit["time"],
                commit["repo"],
                commit["message"][:60] + ("..." if len(commit["message"]) > 60 else ""),
                commit["changes"]
            )
        console.print(table)
    else:
        console.print("  [dim]No GitHub commits found[/dim]")
    console.print()

    # Summary Stats
    _display_stats(events, searches, commits)


def display_range_summary(title: str, start: datetime, end: datetime, events: list, searches: list, commits: list):
    """Display a formatted summary for a date range."""
    console.print()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", box=box.DOUBLE))
    console.print(f"[dim]{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}[/dim]")
    console.print()

    # Calendar Events
    console.print("[bold magenta]📅 Calendar Events[/bold magenta]")
    if events:
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Time", style="cyan", width=15)
        table.add_column("Event", style="white")
        table.add_column("Duration", style="green", width=12)

        for event in events:
            table.add_row(event.get("date", ""), event["time"], event["summary"], event["duration"])
        console.print(table)
    else:
        console.print("  [dim]No calendar events found[/dim]")
    console.print()

    # Chrome Search History
    console.print("[bold blue]🔍 Search History[/bold blue]")
    if searches:
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Time", style="cyan", width=8)
        table.add_column("Search Query / Page Title", style="white")
        table.add_column("URL", style="dim", max_width=40, overflow="ellipsis")

        seen = set()
        count = 0
        for search in searches:
            key = search["title"].lower()
            if key not in seen and count < 30:
                seen.add(key)
                date_str = search.get("datetime", datetime.now()).strftime("%Y-%m-%d") if search.get("datetime") else ""
                table.add_row(date_str, search["time"], search["title"], search["url"])
                count += 1
        console.print(table)
        if len(searches) > 30:
            console.print(f"  [dim]... and {len(searches) - 30} more entries[/dim]")
    else:
        console.print("  [dim]No search history found[/dim]")
    console.print()

    # GitHub Commits
    console.print("[bold green]💻 GitHub Commits[/bold green]")
    if commits:
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Time", style="cyan", width=8)
        table.add_column("Repository", style="yellow", width=25)
        table.add_column("Commit Message", style="white")
        table.add_column("Changes", style="green", width=12)

        for commit in commits:
            table.add_row(
                commit.get("date", ""),
                commit["time"],
                commit["repo"],
                commit["message"][:50] + ("..." if len(commit["message"]) > 50 else ""),
                commit["changes"]
            )
        console.print(table)
    else:
        console.print("  [dim]No GitHub commits found[/dim]")
    console.print()

    # Summary Stats
    _display_stats(events, searches, commits)


def _display_stats(events: list, searches: list, commits: list):
    """Display summary statistics."""
    console.print("[bold yellow]📊 Summary[/bold yellow]")
    stats_table = Table(show_header=False, box=box.SIMPLE)
    stats_table.add_column("Metric", style="bold")
    stats_table.add_column("Value", style="cyan")
    stats_table.add_row("Calendar events", str(len(events)))
    stats_table.add_row("Searches/pages visited", str(len(searches)))
    stats_table.add_row("Commits", str(len(commits)))

    total_commit_additions = sum(c.get("additions", 0) for c in commits)
    total_commit_deletions = sum(c.get("deletions", 0) for c in commits)
    if commits:
        stats_table.add_row("Lines added", f"+{total_commit_additions}")
        stats_table.add_row("Lines deleted", f"-{total_commit_deletions}")

    console.print(stats_table)
    console.print()
