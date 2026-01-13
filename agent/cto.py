"""
Main CTO Agent class that handles conversations with Claude.
"""

import json
import sys
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich import box

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from agent.tools import TOOLS, execute_tool
from agent.prompts import get_system_prompt

console = Console()


class CTOAgent:
    """Conversational CTO agent powered by Claude."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        config = load_config()
        api_key = config.get("anthropic_api_key")

        if not api_key:
            raise ValueError(
                "Anthropic API key not configured. Run 'worklog setup' first."
            )

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.system_prompt = get_system_prompt()
        self.messages: list[dict] = []

    def clear_history(self):
        """Clear conversation history."""
        self.messages = []

    def chat(self, user_message: str) -> str:
        """Send a message and get a response, handling tool use."""

        # Add user message to history
        self.messages.append({"role": "user", "content": user_message})

        # Initial API call
        response = self._call_api()

        # Handle tool use loop
        while response.stop_reason == "tool_use":
            # Process tool calls
            tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type == "tool_use":
                    console.print(f"[dim]Fetching {block.name}...[/dim]")

                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str),
                    })

            # Add assistant message with tool use
            self.messages.append({
                "role": "assistant",
                "content": assistant_content,
            })

            # Add tool results
            self.messages.append({
                "role": "user",
                "content": tool_results,
            })

            # Continue conversation
            response = self._call_api()

        # Extract text response
        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text += block.text

        # Add assistant response to history
        self.messages.append({"role": "assistant", "content": response_text})

        return response_text

    def _call_api(self):
        """Make an API call to Claude."""
        return self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            tools=TOOLS,
            messages=self.messages,
        )


def run_chat_loop(agent: CTOAgent):
    """Run the interactive chat loop in fullscreen alternate screen mode (like vim/nano)."""
    import curses
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr

    def _main_loop(stdscr):
        """Main curses loop - runs in alternate screen."""
        # Exit curses mode temporarily to use Rich for display
        curses.endwin()

        # Now we're in the alternate screen but can use normal terminal I/O
        alt_console = Console()

        def _draw_header(message: str = None):
            """Draw the header panel."""
            alt_console.clear()
            alt_console.print()
            alt_console.print(Panel(
                "[bold cyan]CTO Agent[/bold cyan]\n"
                f"[dim]{message or 'Ask me about your work, request reports, or get insights.'}[/dim]\n"
                "[dim]Type 'exit' to end, 'clear' for new conversation, 'help' for commands.[/dim]",
                box=box.ROUNDED,
                width=min(80, alt_console.width),
            ), justify="center")
            alt_console.print()

        _draw_header()

        while True:
            try:
                # Get user input
                user_input = alt_console.input("[bold green]You:[/bold green] ").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ("exit", "quit", "q"):
                    break

                if user_input.lower() == "help":
                    _show_help_alt(alt_console)
                    continue

                if user_input.lower() == "clear":
                    agent.clear_history()
                    _draw_header("New conversation started.")
                    continue

                # Get response from agent
                with alt_console.status("[bold blue]Thinking...[/bold blue]"):
                    response = agent.chat(user_input)

                # Display response
                alt_console.print()
                alt_console.print("[bold blue]CTO Agent:[/bold blue]")
                alt_console.print(Markdown(response))
                alt_console.print()

            except KeyboardInterrupt:
                alt_console.print("\n[dim]Interrupted. Type 'exit' to quit.[/dim]")
            except Exception as e:
                alt_console.print(f"[red]Error: {e}[/red]")

    # Use curses.wrapper to handle alternate screen setup/teardown
    curses.wrapper(_main_loop)


def _show_help_alt(alt_console):
    """Display help information in alternate screen."""
    help_text = """
## Commands
- `exit` / `quit` - End the conversation
- `clear` - Start a new conversation
- `help` - Show this help

## Example Questions
- "What did I work on today?"
- "Generate my standup notes"
- "Create a weekly report"
- "How many commits did I make this week?"
- "What meetings do I have today?"
- "Summarize my browser research this week"
"""
    alt_console.print(Markdown(help_text))


def _show_help():
    """Display help information."""
    help_text = """
## Commands
- `exit` / `quit` - End the conversation
- `clear` - Start a new conversation
- `help` - Show this help

## Example Questions
- "What did I work on today?"
- "Generate my standup notes"
- "Create a weekly report"
- "How many commits did I make this week?"
- "What meetings do I have today?"
- "Summarize my browser research this week"
"""
    console.print(Markdown(help_text))
