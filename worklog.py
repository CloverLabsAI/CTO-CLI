#!/usr/bin/env python3
"""
Worklog CLI - A daily work breakdown tool that aggregates data from:
- Google Calendar events
- Chrome search history
- GitHub commits
"""

import argparse
import calendar as cal
import sys
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

from gcalendar import get_calendar_events
from chrome import get_chrome_history
from github import get_github_commits
from config import load_config, setup_config, is_configured, is_ai_configured


console = Console()


def parse_date(date_str: str) -> datetime:
    """Parse a date string in various formats."""
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {date_str}")


def get_date_range(date: datetime) -> tuple[datetime, datetime]:
    """Get start and end of day for a given date."""
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def get_week_range(date: datetime) -> tuple[datetime, datetime]:
    """Get start (Monday) and end (Sunday) of the week containing the given date."""
    start = date - timedelta(days=date.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=6)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def get_month_range(year: int, month: int) -> tuple[datetime, datetime]:
    """Get start and end of a given month."""
    start = datetime(year, month, 1, 0, 0, 0, 0)
    last_day = cal.monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59, 999999)
    return start, end


def parse_week(week_str: str) -> tuple[int, int]:
    """Parse a week string like '2024-W03' or just '3' for current year."""
    if '-W' in week_str.upper():
        parts = week_str.upper().split('-W')
        return int(parts[0]), int(parts[1])
    else:
        return datetime.now().year, int(week_str)


def parse_month(month_str: str) -> tuple[int, int]:
    """Parse a month string like '2024-01', 'January', or just '1' for current year."""
    month_names = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }

    if '-' in month_str:
        parts = month_str.split('-')
        return int(parts[0]), int(parts[1])
    elif month_str.lower() in month_names:
        return datetime.now().year, month_names[month_str.lower()]
    else:
        return datetime.now().year, int(month_str)


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


def cmd_summary(args):
    """Show work summary for a specific date."""
    if not is_configured():
        console.print("[red]Error: Worklog is not configured. Run 'worklog setup' first.[/red]")
        sys.exit(1)
    
    config = load_config()
    
    # Determine the date
    if args.date:
        try:
            date = parse_date(args.date)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    elif args.yesterday:
        date = datetime.now() - timedelta(days=1)
    else:
        date = datetime.now()
    
    start, end = get_date_range(date)
    
    console.print(f"[dim]Fetching data for {date.strftime('%Y-%m-%d')}...[/dim]")
    
    # Fetch from all sources
    events = []
    searches = []
    commits = []
    
    with console.status("[bold green]Fetching calendar events..."):
        try:
            events = get_calendar_events(config, start, end)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not fetch calendar events: {e}[/yellow]")
    
    with console.status("[bold blue]Reading Chrome history..."):
        try:
            searches = get_chrome_history(start, end, chrome_profile=config.get("chrome_profile"))
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read Chrome history: {e}[/yellow]")
    
    with console.status("[bold green]Fetching GitHub commits..."):
        try:
            commits = get_github_commits(config, start, end)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not fetch GitHub commits: {e}[/yellow]")
    
    display_summary(date, events, searches, commits)


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


def fetch_data_for_range(config: dict, start: datetime, end: datetime) -> tuple[list, list, list]:
    """Fetch all data sources for a date range."""
    events = []
    searches = []
    commits = []

    with console.status("[bold green]Fetching calendar events..."):
        try:
            events = get_calendar_events(config, start, end)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not fetch calendar events: {e}[/yellow]")

    with console.status("[bold blue]Reading Chrome history..."):
        try:
            searches = get_chrome_history(start, end, chrome_profile=config.get("chrome_profile"))
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read Chrome history: {e}[/yellow]")

    with console.status("[bold green]Fetching GitHub commits..."):
        try:
            commits = get_github_commits(config, start, end)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not fetch GitHub commits: {e}[/yellow]")

    return events, searches, commits


def cmd_setup(args):
    """Run interactive setup."""
    setup_config()


def cmd_day(args):
    """Show work summary for a specific day."""
    if not is_configured():
        console.print("[red]Error: Worklog is not configured. Run 'worklog setup' first.[/red]")
        sys.exit(1)

    config = load_config()

    if args.date:
        try:
            date = parse_date(args.date)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    else:
        date = datetime.now()

    start, end = get_date_range(date)
    console.print(f"[dim]Fetching data for {date.strftime('%Y-%m-%d')}...[/dim]")

    events, searches, commits = fetch_data_for_range(config, start, end)
    display_summary(date, events, searches, commits)


def cmd_week(args):
    """Show work summary for a specific week."""
    if not is_configured():
        console.print("[red]Error: Worklog is not configured. Run 'worklog setup' first.[/red]")
        sys.exit(1)

    config = load_config()

    if args.week:
        try:
            year, week_num = parse_week(args.week)
            # Get the Monday of the specified week
            start = datetime.strptime(f'{year}-W{week_num:02d}-1', '%G-W%V-%u')
        except ValueError as e:
            console.print(f"[red]Error: Invalid week format. Use 'YYYY-Wnn' or just the week number: {e}[/red]")
            sys.exit(1)
    else:
        start = datetime.now()

    start, end = get_week_range(start)
    week_num = start.isocalendar()[1]
    title = f"Work Summary for Week {week_num}, {start.year}"

    console.print(f"[dim]Fetching data for week {week_num}...[/dim]")
    events, searches, commits = fetch_data_for_range(config, start, end)
    display_range_summary(title, start, end, events, searches, commits)


def cmd_month(args):
    """Show work summary for a specific month."""
    if not is_configured():
        console.print("[red]Error: Worklog is not configured. Run 'worklog setup' first.[/red]")
        sys.exit(1)

    config = load_config()

    if args.month:
        try:
            year, month = parse_month(args.month)
        except ValueError as e:
            console.print(f"[red]Error: Invalid month format: {e}[/red]")
            sys.exit(1)
    else:
        now = datetime.now()
        year, month = now.year, now.month

    start, end = get_month_range(year, month)
    month_name = start.strftime("%B %Y")
    title = f"Work Summary for {month_name}"

    console.print(f"[dim]Fetching data for {month_name}...[/dim]")
    events, searches, commits = fetch_data_for_range(config, start, end)
    display_range_summary(title, start, end, events, searches, commits)


def cmd_chat(args):
    """Start the AI CTO agent conversation."""
    from agent import CTOAgent, run_chat_loop

    # Check AI configuration
    if not is_ai_configured():
        console.print("[red]Error: Anthropic API key not configured.[/red]")
        console.print("Run 'worklog setup' to add your API key.")
        sys.exit(1)

    if not is_configured():
        console.print("[yellow]Warning: Data sources not fully configured.[/yellow]")
        console.print("Some features may be limited. Run 'worklog setup' to configure.")

    # Initialize agent
    try:
        agent = CTOAgent(model=args.model)
    except Exception as e:
        console.print(f"[red]Error initializing agent: {e}[/red]")
        sys.exit(1)

    # Handle single query mode
    if args.query:
        with console.status("[bold blue]Thinking...[/bold blue]"):
            response = agent.chat(args.query)
        console.print(Markdown(response))
        return

    # Run interactive loop
    run_chat_loop(agent)


def main():
    parser = argparse.ArgumentParser(
        description="Worklog - Track your daily work across Calendar, Chrome, and GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  worklog                      Show today's work summary
  worklog --yesterday          Show yesterday's work summary
  worklog --date 2024-01-15    Show summary for a specific date
  worklog day 2024-01-15       Show summary for a specific day
  worklog week                 Show current week's summary
  worklog week 2               Show week 2 of current year
  worklog week 2024-W03        Show week 3 of 2024
  worklog month                Show current month's summary
  worklog month january        Show January of current year
  worklog month 2024-01        Show January 2024
  worklog chat                 Start AI CTO agent conversation
  worklog chat -q "question"   Ask a single question
  worklog setup                Configure API credentials
        """
    )

    subparsers = parser.add_subparsers(dest="command")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Configure API credentials")
    setup_parser.set_defaults(func=cmd_setup)

    # Day command
    day_parser = subparsers.add_parser("day", help="Show summary for a specific day")
    day_parser.add_argument("date", nargs="?", help="Date (YYYY-MM-DD, DD/MM/YYYY, or MM/DD/YYYY)")
    day_parser.set_defaults(func=cmd_day)

    # Week command
    week_parser = subparsers.add_parser("week", help="Show week's summary")
    week_parser.add_argument("week", nargs="?", help="Week number (e.g., '3' or '2024-W03')")
    week_parser.set_defaults(func=cmd_week)

    # Month command
    month_parser = subparsers.add_parser("month", help="Show month's summary")
    month_parser.add_argument("month", nargs="?", help="Month (e.g., 'january', '1', or '2024-01')")
    month_parser.set_defaults(func=cmd_month)

    # Chat command (AI CTO agent)
    chat_parser = subparsers.add_parser("chat", help="Start AI CTO agent conversation")
    chat_parser.add_argument(
        "--query", "-q",
        help="Single query mode (non-interactive)"
    )
    chat_parser.add_argument(
        "--model", "-m",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)"
    )
    chat_parser.set_defaults(func=cmd_chat)

    # Default command arguments (for running without subcommand)
    parser.add_argument("--date", "-d", help="Date to show summary for (YYYY-MM-DD)")
    parser.add_argument("--yesterday", "-y", action="store_true", help="Show yesterday's summary")

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        cmd_summary(args)


if __name__ == "__main__":
    main()
