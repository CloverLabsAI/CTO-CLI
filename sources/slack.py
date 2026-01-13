"""
Slack integration for Worklog CLI.
Fetches messages sent by the user within a date range from all conversations.
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

    Uses multiple methods to get comprehensive coverage:
    1. Search API (for searchable messages)
    2. Conversations API (for DMs, group DMs, and private channels)

    Required scopes:
    - search:read (for search)
    - im:history, im:read (for DMs)
    - mpim:history, mpim:read (for group DMs)
    - channels:history, channels:read (for public channels)
    - groups:history, groups:read (for private channels)
    """
    token = config.get("slack_token")
    if not token:
        raise ValueError("Slack token not configured. Run 'cto setup' first.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    messages = []
    user_id = _get_user_id(headers)

    # Method 1: Search API (works for searchable content)
    search_messages = _search_messages(headers, start, end)
    messages.extend(search_messages)

    # Method 2: Direct conversation history (for DMs and private channels)
    # This catches messages that might not be searchable
    conversation_messages = _get_conversation_messages(headers, user_id, start, end)

    # Merge and deduplicate by timestamp + channel
    seen = set()
    unique_messages = []
    for msg in messages + conversation_messages:
        key = (msg.get("datetime"), msg.get("channel"))
        if key not in seen:
            seen.add(key)
            unique_messages.append(msg)

    # Sort by datetime
    unique_messages.sort(key=lambda x: x.get("datetime") or datetime.min, reverse=True)

    return unique_messages


def _get_user_id(headers: dict) -> Optional[str]:
    """Get the authenticated user's ID."""
    try:
        response = requests.get(
            "https://slack.com/api/auth.test",
            headers=headers
        )
        data = response.json()
        if data.get("ok"):
            return data.get("user_id")
    except Exception:
        pass
    return None


def _search_messages(headers: dict, start: datetime, end: datetime) -> list[dict]:
    """Search for messages using the search API."""
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
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

        try:
            response = requests.get(
                "https://slack.com/api/search.messages",
                headers=headers,
                params=params
            )
            data = response.json()

            if not data.get("ok"):
                break

            matches = data.get("messages", {}).get("matches", [])

            for msg in matches:
                ts = float(msg.get("ts", 0))
                msg_dt = datetime.fromtimestamp(ts)

                if start <= msg_dt <= end:
                    channel_info = msg.get("channel", {})
                    channel_name = channel_info.get("name", "unknown")
                    is_dm = channel_info.get("is_im", False)
                    is_group_dm = channel_info.get("is_mpim", False)

                    if is_dm:
                        channel_name = "DM"
                    elif is_group_dm:
                        channel_name = "Group DM"

                    messages.append({
                        "time": msg_dt.strftime("%H:%M"),
                        "datetime": msg_dt,
                        "channel": channel_name,
                        "channel_type": "dm" if is_dm else ("group_dm" if is_group_dm else "channel"),
                        "text": msg.get("text", ""),
                        "permalink": msg.get("permalink", ""),
                    })

            paging = data.get("messages", {}).get("paging", {})
            if paging.get("page", 1) >= paging.get("pages", 1):
                break

            next_cursor = data.get("response_metadata", {}).get("next_cursor")
            if not next_cursor:
                break
            cursor = next_cursor

        except Exception:
            break

    return messages


def _get_conversation_messages(
    headers: dict,
    user_id: str,
    start: datetime,
    end: datetime
) -> list[dict]:
    """Get messages from all conversations (DMs, group DMs, channels)."""
    if not user_id:
        return []

    messages = []

    # Convert to Unix timestamps
    oldest = str(start.timestamp())
    latest = str(end.timestamp())

    # Get all conversations the user is part of
    conversations = _list_conversations(headers)

    for conv in conversations:
        conv_id = conv.get("id")
        conv_name = conv.get("name", "Unknown")
        conv_type = conv.get("type", "channel")

        try:
            # Fetch history for this conversation
            params = {
                "channel": conv_id,
                "oldest": oldest,
                "latest": latest,
                "limit": 200,
            }

            response = requests.get(
                "https://slack.com/api/conversations.history",
                headers=headers,
                params=params
            )
            data = response.json()

            if not data.get("ok"):
                continue

            for msg in data.get("messages", []):
                # Only include messages from the user
                if msg.get("user") != user_id:
                    continue

                ts = float(msg.get("ts", 0))
                msg_dt = datetime.fromtimestamp(ts)

                if start <= msg_dt <= end:
                    messages.append({
                        "time": msg_dt.strftime("%H:%M"),
                        "datetime": msg_dt,
                        "channel": conv_name,
                        "channel_type": conv_type,
                        "text": msg.get("text", ""),
                        "permalink": "",  # Would need another API call
                    })

        except Exception:
            continue

    return messages


def _list_conversations(headers: dict) -> list[dict]:
    """List all conversations (DMs, group DMs, channels) the user is in."""
    conversations = []
    cursor = None

    # Types: im (DM), mpim (group DM), public_channel, private_channel
    types = "im,mpim,public_channel,private_channel"

    while True:
        params = {
            "types": types,
            "limit": 200,
            "exclude_archived": "true",
        }
        if cursor:
            params["cursor"] = cursor

        try:
            response = requests.get(
                "https://slack.com/api/conversations.list",
                headers=headers,
                params=params
            )
            data = response.json()

            if not data.get("ok"):
                break

            for conv in data.get("channels", []):
                conv_id = conv.get("id")
                is_im = conv.get("is_im", False)
                is_mpim = conv.get("is_mpim", False)

                if is_im:
                    # For DMs, get the other user's name
                    conv_name = _get_dm_user_name(headers, conv.get("user")) or "DM"
                    conv_type = "dm"
                elif is_mpim:
                    conv_name = conv.get("name", "Group DM")
                    conv_type = "group_dm"
                else:
                    conv_name = conv.get("name", "Unknown")
                    conv_type = "private_channel" if conv.get("is_private") else "channel"

                conversations.append({
                    "id": conv_id,
                    "name": conv_name,
                    "type": conv_type,
                })

            next_cursor = data.get("response_metadata", {}).get("next_cursor")
            if not next_cursor:
                break
            cursor = next_cursor

        except Exception:
            break

    return conversations


def _get_dm_user_name(headers: dict, user_id: str) -> Optional[str]:
    """Get a user's display name for DM labeling."""
    if not user_id:
        return None

    try:
        response = requests.get(
            "https://slack.com/api/users.info",
            headers=headers,
            params={"user": user_id}
        )
        data = response.json()
        if data.get("ok"):
            user = data.get("user", {})
            return (
                user.get("profile", {}).get("display_name") or
                user.get("profile", {}).get("real_name") or
                user.get("name")
            )
    except Exception:
        pass
    return None


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
