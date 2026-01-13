"""
Tool definitions for Claude to fetch work data.
Uses Anthropic's tool_use feature.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources import get_chrome_history, get_github_commits, get_calendar_events, get_slack_messages
from config import load_config


# Tool schema definitions for Claude
TOOLS = [
    {
        "name": "get_work_data",
        "description": """Fetch work activity data from multiple sources for a specific date range.
Returns calendar events, browser history, GitHub commits, and Slack messages.
Use this tool when you need to analyze the user's work activities, generate reports,
or answer questions about what they worked on.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format"
                },
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["calendar", "browser", "github", "slack"]
                    },
                    "description": "Which data sources to fetch. Defaults to all if not specified."
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_current_date",
        "description": "Get the current date and time. Use this to understand temporal references like 'today', 'yesterday', 'this week'.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]


def execute_tool(tool_name: str, tool_input: dict) -> dict[str, Any]:
    """Execute a tool and return the result."""

    if tool_name == "get_current_date":
        now = datetime.now()
        return {
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "week_number": now.isocalendar()[1],
        }

    elif tool_name == "get_work_data":
        return _fetch_work_data(
            tool_input["start_date"],
            tool_input["end_date"],
            tool_input.get("sources", ["calendar", "browser", "github", "slack"])
        )

    else:
        return {"error": f"Unknown tool: {tool_name}"}


def _fetch_work_data(start_date: str, end_date: str, sources: list[str]) -> dict:
    """Fetch work data from specified sources."""
    config = load_config()

    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    start = start.replace(hour=0, minute=0, second=0)
    end = datetime.strptime(end_date, "%Y-%m-%d")
    end = end.replace(hour=23, minute=59, second=59)

    result = {
        "date_range": {
            "start": start_date,
            "end": end_date,
        },
        "data": {}
    }

    # Fetch calendar events
    if "calendar" in sources:
        try:
            events = get_calendar_events(config, start, end)
            result["data"]["calendar_events"] = events
        except Exception as e:
            result["data"]["calendar_events"] = {"error": str(e)}

    # Fetch browser history
    if "browser" in sources:
        try:
            history = get_chrome_history(start, end, config.get("chrome_profile"))
            # Deduplicate and limit to prevent token overflow
            seen = set()
            unique_history = []
            for item in history:
                key = item["title"].lower()
                if key not in seen:
                    seen.add(key)
                    unique_history.append({
                        "title": item["title"],
                        "url": item["url"],
                        "time": item["time"],
                    })
                    if len(unique_history) >= 50:  # Limit results
                        break
            result["data"]["browser_history"] = unique_history
            result["data"]["browser_history_total"] = len(history)
        except Exception as e:
            result["data"]["browser_history"] = {"error": str(e)}

    # Fetch GitHub commits
    if "github" in sources:
        try:
            commits = get_github_commits(config, start, end)
            result["data"]["github_commits"] = [
                {
                    "repo": c["repo"],
                    "message": c["message"],
                    "time": c["time"],
                    "changes": c["changes"],
                }
                for c in commits
            ]
        except Exception as e:
            result["data"]["github_commits"] = {"error": str(e)}

    # Fetch Slack messages
    if "slack" in sources:
        try:
            messages = get_slack_messages(config, start, end)
            # Limit and format messages
            result["data"]["slack_messages"] = [
                {
                    "channel": m["channel"],
                    "text": m["text"][:200] + "..." if len(m["text"]) > 200 else m["text"],
                    "time": m["time"],
                }
                for m in messages[:50]  # Limit to 50 messages
            ]
            result["data"]["slack_messages_total"] = len(messages)
        except Exception as e:
            result["data"]["slack_messages"] = {"error": str(e)}

    return result
