"""
Chat command handler for Worklog CLI (AI CTO agent).
"""

import sys

from rich.console import Console
from rich.markdown import Markdown

from config import is_configured, is_ai_configured

console = Console()


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
