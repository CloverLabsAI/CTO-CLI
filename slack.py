"""
Slack integration for Worklog CLI.
Fetches messages sent by the user within a date range.
"""

import requests
from datetime import datetime
from typing import Optional


def get_slack_messages(
    config: dict,
    start: datetime,
    end: datetime
) -> list[dict]:
    """
    Fetch Slack messages sent by the user in a given date range.

    Requires a Slack User OAuth Token with 'search:read' scope.
    Get one at: https://api.slack.com/apps → Create App → OAuth & Permissions
    """
    token = config.get("slack_token")
    if not token:
        raise ValueError("Slack token not configured. Run 'worklog setup' first.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Format dates for Slack search (YYYY-MM-DD)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    # Search for messages from "me" (the authenticated user) in date range
    # Slack search query syntax: from:me after:YYYY-MM-DD before:YYYY-MM-DD
    query = f"from:me after:{start_str} before:{end_str}"

    messages = []
    cursor = None

    while True:
        params = {
            "query": query,
            "sort": "timestamp",
            "sort_dir": "desc",
            "count": 100,
        }
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            "https://slack.com/api/search.messages",
            headers=headers,
            params=params
        )

        data = response.json()

        if not data.get("ok"):
            error = data.get("error", "Unknown error")
            raise Exception(f"Slack API error: {error}")

        matches = data.get("messages", {}).get("matches", [])

        for msg in matches:
            # Parse timestamp
            ts = float(msg.get("ts", 0))
            msg_dt = datetime.fromtimestamp(ts)

            # Only include messages within our exact range
            if start <= msg_dt <= end:
                channel_name = msg.get("channel", {}).get("name", "unknown")

                messages.append({
                    "time": msg_dt.strftime("%H:%M"),
                    "datetime": msg_dt,
                    "channel": channel_name,
                    "text": msg.get("text", ""),
                    "permalink": msg.get("permalink", ""),
                })

        # Check for pagination
        paging = data.get("messages", {}).get("paging", {})
        if paging.get("page", 1) >= paging.get("pages", 1):
            break

        # Slack uses cursor-based pagination for some endpoints
        next_cursor = data.get("response_metadata", {}).get("next_cursor")
        if not next_cursor:
            break
        cursor = next_cursor

    return messages


def test_slack_connection(config: dict) -> bool:
    """Test if Slack connection is working."""
    token = config.get("slack_token")
    if not token:
        return False

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://slack.com/api/auth.test",
            headers=headers
        )
        data = response.json()
        return data.get("ok", False)
    except Exception:
        return False


def get_slack_user_info(config: dict) -> Optional[dict]:
    """Get info about the authenticated Slack user."""
    token = config.get("slack_token")
    if not token:
        return None

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://slack.com/api/auth.test",
            headers=headers
        )
        data = response.json()
        if data.get("ok"):
            return {
                "user": data.get("user"),
                "user_id": data.get("user_id"),
                "team": data.get("team"),
            }
        return None
    except Exception:
        return None
