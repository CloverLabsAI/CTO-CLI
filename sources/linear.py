"""
Linear integration for Worklog CLI.
Fetches user activity and audit logs from Linear.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.linear import LinearMCPServer


def get_linear_activity(
    config: dict,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """
    Fetch Linear activity for a given date range.
    Returns issues the user worked on during the period.
    """
    api_key = config.get("linear_api_key")
    if not api_key:
        raise ValueError("Linear API key not configured. Run 'cto setup' first.")

    server = LinearMCPServer(api_key)
    activity = server.get_my_activity(start_date=start, end_date=end)

    return [
        {
            "id": item["id"],
            "title": item["title"],
            "state": item["state"],
            "team": item["team"],
            "time": datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")).strftime("%H:%M") if item.get("updated_at") else "",
            "datetime": datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")) if item.get("updated_at") else None,
        }
        for item in activity
    ]


def get_linear_audit_logs(
    config: dict,
    start: datetime,
    end: datetime,
    actor_email: Optional[str] = None,
) -> list[dict]:
    """
    Fetch Linear audit logs for a given date range.
    Note: Requires admin access and Linear Plus plan.
    """
    api_key = config.get("linear_api_key")
    if not api_key:
        raise ValueError("Linear API key not configured. Run 'cto setup' first.")

    server = LinearMCPServer(api_key)

    try:
        logs = server.get_audit_logs(
            start_date=start,
            end_date=end,
            actor_email=actor_email,
        )
        return logs
    except Exception as e:
        # Audit logs may not be available (requires Plus plan + admin)
        if "auditEntries" in str(e):
            return []
        raise


def test_linear_connection(config: dict) -> bool:
    """Test if Linear connection is working."""
    api_key = config.get("linear_api_key")
    if not api_key:
        return False

    try:
        from mcp.linear import test_linear_connection as _test
        return _test(api_key)
    except Exception:
        return False


def get_linear_user_info(config: dict) -> Optional[dict]:
    """Get info about the authenticated Linear user."""
    api_key = config.get("linear_api_key")
    if not api_key:
        return None

    try:
        from mcp.linear import get_linear_user_info as _get_info
        return _get_info(api_key)
    except Exception:
        return None
