"""
Summary command handlers for Worklog CLI.
"""

import sys
from datetime import datetime, timedelta

from rich.console import Console

from config import load_config, is_configured
from sources import get_calendar_events, get_chrome_history, get_github_commits
from display import display_summary, display_range_summary
from utils import parse_date, parse_week, parse_month, get_date_range, get_week_range, get_month_range

console = Console()


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


def cmd_summary(args):
    """Show work summary for a specific date (default command)."""
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

    events, searches, commits = fetch_data_for_range(config, start, end)
    display_summary(date, events, searches, commits)


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
