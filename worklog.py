#!/usr/bin/env python3
"""
Worklog CLI - A daily work breakdown tool that aggregates data from:
- Google Calendar events
- Chrome search history
- GitHub commits
- Slack messages

With an AI-powered CTO agent for generating reports and insights.
"""

import argparse

from commands import cmd_summary, cmd_day, cmd_week, cmd_month, cmd_chat, cmd_setup, cmd_projects


def main():
    parser = argparse.ArgumentParser(
        description="Worklog - Track your daily work across Calendar, Chrome, GitHub, and Slack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cto                          Show today's work summary
  cto --yesterday              Show yesterday's summary
  cto --date 2024-01-15        Show summary for a specific date
  cto day 2024-01-15           Show summary for a specific day
  cto week                     Show current week's summary
  cto week 2                   Show week 2 of current year
  cto month                    Show current month's summary
  cto month january            Show January of current year
  cto projects                 Show Linear projects by status
  cto projects --all           Include completed projects
  cto chat                     Start AI CTO agent conversation
  cto chat -q "question"       Ask a single question
  cto setup                    Configure API credentials
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

    # Projects command (Linear projects view)
    projects_parser = subparsers.add_parser("projects", help="Show Linear projects grouped by status")
    projects_parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Include completed and canceled projects"
    )
    projects_parser.set_defaults(func=cmd_projects)

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
