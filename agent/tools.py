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

from sources import (
    get_chrome_history,
    get_github_commits,
    get_calendar_events,
    get_slack_messages,
    get_linear_activity,
    get_linear_audit_logs,
)
from config import load_config


# Tool schema definitions for Claude
TOOLS = [
    {
        "name": "get_work_data",
        "description": """Fetch work activity data from multiple sources for a specific date range.
Returns calendar events, browser history, GitHub commits, Slack messages, and Linear activity.
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
                        "enum": ["calendar", "browser", "github", "slack", "linear"]
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
    },
    {
        "name": "query_linear",
        "description": """Query Linear workspace for issues, projects, teams, or audit logs.
Use this for questions about Linear workspace data, project status, team members, or security audit logs.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["my_issues", "search_issues", "projects", "teams", "audit_logs"],
                    "description": "Type of query to run"
                },
                "search_text": {
                    "type": "string",
                    "description": "Search text (for search_issues query type)"
                },
                "team_key": {
                    "type": "string",
                    "description": "Team key to filter by (e.g., 'ENG')"
                },
                "state": {
                    "type": "string",
                    "description": "Issue state filter (e.g., 'started', 'completed')"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for audit logs (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for audit logs (YYYY-MM-DD)"
                }
            },
            "required": ["query_type"]
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
            tool_input.get("sources", ["calendar", "browser", "github", "slack", "linear"])
        )

    elif tool_name == "query_linear":
        return _query_linear(tool_input)

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

    # Fetch Linear activity
    if "linear" in sources:
        try:
            activity = get_linear_activity(config, start, end)
            result["data"]["linear_activity"] = [
                {
                    "id": a["id"],
                    "title": a["title"],
                    "state": a["state"],
                    "team": a["team"],
                    "time": a["time"],
                }
                for a in activity[:30]  # Limit results
            ]
            result["data"]["linear_activity_total"] = len(activity)
        except Exception as e:
            result["data"]["linear_activity"] = {"error": str(e)}

    return result


def _query_linear(tool_input: dict) -> dict:
    """Query Linear workspace data."""
    from mcp.linear import LinearMCPServer

    config = load_config()
    api_key = config.get("linear_api_key")

    if not api_key:
        return {"error": "Linear API key not configured. Run 'cto setup' first."}

    try:
        server = LinearMCPServer(api_key)
        query_type = tool_input.get("query_type")

        if query_type == "my_issues":
            state = tool_input.get("state")
            issues = server.get_my_issues(state=state)
            return {"issues": issues, "count": len(issues)}

        elif query_type == "search_issues":
            search_text = tool_input.get("search_text", "")
            if not search_text:
                return {"error": "search_text is required for search_issues query"}
            issues = server.search_issues(search_text)
            return {"issues": issues, "count": len(issues)}

        elif query_type == "projects":
            team_key = tool_input.get("team_key")
            projects = server.get_projects(team_key=team_key)
            return {"projects": projects, "count": len(projects)}

        elif query_type == "teams":
            teams = server.get_teams()
            return {"teams": teams, "count": len(teams)}

        elif query_type == "audit_logs":
            start_date = tool_input.get("start_date")
            end_date = tool_input.get("end_date")

            start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

            logs = server.get_audit_logs(start_date=start, end_date=end)
            return {"audit_logs": logs, "count": len(logs)}

        else:
            return {"error": f"Unknown query_type: {query_type}"}

    except Exception as e:
        return {"error": str(e)}
