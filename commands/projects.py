"""
Projects command handler for Worklog CLI.
Displays Linear projects grouped by status, sorted by last status/health update.
"""

import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config

console = Console()

# Health status icons and colors
HEALTH_CONFIG = {
    "onTrack": {"icon": "🟢", "color": "green", "label": "On Track"},
    "atRisk": {"icon": "🟡", "color": "yellow", "label": "At Risk"},
    "offTrack": {"icon": "🔴", "color": "red", "label": "Off Track"},
}


def cmd_projects(args):
    """Display Linear projects grouped by status, sorted by last status update."""
    config = load_config()
    api_key = config.get("linear_api_key")

    if not api_key:
        console.print("[red]Error: Linear API key not configured.[/red]")
        console.print("Run 'cto setup' to add your Linear API key.")
        return

    from mcp.linear import LinearMCPServer

    try:
        server = LinearMCPServer(api_key)
        projects = server.get_projects(include_completed=args.all if hasattr(args, 'all') else False)
    except Exception as e:
        console.print(f"[red]Error fetching projects: {e}[/red]")
        return

    if not projects:
        console.print("[dim]No projects found.[/dim]")
        return

    # Group projects by status
    status_groups = {
        "started": [],      # In Progress
        "planned": [],      # Todo/Planned
        "backlog": [],      # Backlog
        "paused": [],       # Paused
        "completed": [],    # Completed
        "canceled": [],     # Canceled
    }

    for project in projects:
        state = (project.get("state") or "backlog").lower()
        if state in status_groups:
            status_groups[state].append(project)
        else:
            status_groups["backlog"].append(project)

    # Sort each group by health_updated_at (most recent first), fallback to status_updated_at
    for state in status_groups:
        status_groups[state].sort(
            key=lambda p: p.get("health_updated_at") or p.get("status_updated_at") or p.get("updated_at") or "",
            reverse=True
        )

    # Display header
    console.print()
    console.print(Panel(
        "[bold cyan]Linear Projects[/bold cyan]\n"
        "[dim]Sorted by last health update[/dim]",
        box=box.DOUBLE
    ))
    console.print()

    # Status display config
    status_config = {
        "started": {"title": "In Progress", "color": "green", "icon": "🚀"},
        "planned": {"title": "Planned / Todo", "color": "blue", "icon": "📋"},
        "backlog": {"title": "Backlog", "color": "yellow", "icon": "📦"},
        "paused": {"title": "Paused", "color": "orange3", "icon": "⏸️"},
        "completed": {"title": "Completed", "color": "dim", "icon": "✅"},
        "canceled": {"title": "Canceled", "color": "dim", "icon": "❌"},
    }

    # Display order
    display_order = ["started", "planned", "backlog", "paused"]
    if hasattr(args, 'all') and args.all:
        display_order.extend(["completed", "canceled"])

    total_projects = 0

    for state in display_order:
        projects_in_state = status_groups.get(state, [])
        if not projects_in_state:
            continue

        total_projects += len(projects_in_state)
        cfg = status_config.get(state, {"title": state.title(), "color": "white", "icon": "📁"})

        console.print(f"[bold {cfg['color']}]{cfg['icon']} {cfg['title']} ({len(projects_in_state)})[/bold {cfg['color']}]")
        console.print()

        table = Table(
            show_header=True,
            header_style="bold",
            box=box.ROUNDED,
            expand=True,
        )
        table.add_column("Project", style="white", ratio=3)
        table.add_column("Health", width=12, justify="center")
        table.add_column("Progress", style="cyan", width=10, justify="center")
        table.add_column("Lead", style="yellow", width=12)
        table.add_column("Target", style="green", width=12)
        table.add_column("Health Update", style="dim", width=14)

        for project in projects_in_state:
            # Format health - prefer latest_health from project updates
            health = project.get("latest_health") or project.get("health")

            if health:
                health_cfg = HEALTH_CONFIG.get(health, {"icon": "⚪", "color": "dim", "label": health})
                health_str = f"{health_cfg['icon']} [{health_cfg['color']}]{health_cfg['label']}[/{health_cfg['color']}]"
            else:
                health_str = "[dim]-[/dim]"

            # Format progress
            progress = project.get("progress")
            if progress is not None:
                progress_pct = int(progress * 100)
                progress_str = f"{progress_pct}%"
            else:
                progress_str = "-"

            # Format target date
            target = project.get("target_date")
            if target:
                try:
                    target_dt = datetime.fromisoformat(target.replace("Z", "+00:00"))
                    target_str = target_dt.strftime("%Y-%m-%d")
                    # Highlight overdue
                    if target_dt.date() < datetime.now().date() and state != "completed":
                        target_str = f"[red]{target_str}[/red]"
                except Exception:
                    target_str = target[:10] if len(target) >= 10 else target
            else:
                target_str = "-"

            # Format health_updated_at
            health_updated = project.get("health_updated_at") or project.get("status_updated_at")
            if health_updated:
                try:
                    updated_dt = datetime.fromisoformat(health_updated.replace("Z", "+00:00"))
                    updated_str = _relative_time(updated_dt)
                except Exception:
                    updated_str = health_updated[:10] if len(health_updated) >= 10 else health_updated
            else:
                updated_str = "-"

            table.add_row(
                project.get("name", "Untitled"),
                health_str,
                progress_str,
                project.get("lead") or "-",
                target_str,
                updated_str,
            )

        console.print(table)
        console.print()

    # Summary
    console.print(f"[dim]Total: {total_projects} active projects[/dim]")
    console.print()


def _relative_time(dt: datetime) -> str:
    """Convert datetime to relative time string."""
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt

    if diff.days == 0:
        hours = diff.seconds // 3600
        if hours == 0:
            minutes = diff.seconds // 60
            return f"{minutes}m ago" if minutes > 0 else "just now"
        return f"{hours}h ago"
    elif diff.days == 1:
        return "yesterday"
    elif diff.days < 7:
        return f"{diff.days}d ago"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks}w ago"
    elif diff.days < 365:
        months = diff.days // 30
        return f"{months}mo ago"
    else:
        years = diff.days // 365
        return f"{years}y ago"
