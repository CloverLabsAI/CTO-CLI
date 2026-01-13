"""
GitHub integration for Worklog CLI.
Fetches commits made by the user across all their repositories.
"""

from datetime import datetime
from typing import Optional

import requests


def get_github_commits(config: dict, start: datetime, end: datetime) -> list[dict]:
    """
    Fetch GitHub commits for a given date range.
    Uses the GitHub Events API and Search API to find user's commits.
    """
    token = config.get("github_token")
    username = config.get("github_username")

    if not token or not username:
        raise ValueError("GitHub token and username not configured. Run 'worklog setup'.")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    commits = []

    # Format dates for GitHub API
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Method 1: Search API for commits by author
    search_url = "https://api.github.com/search/commits"
    query = f"author:{username} author-date:{start.strftime('%Y-%m-%d')}..{end.strftime('%Y-%m-%d')}"

    params = {
        "q": query,
        "sort": "author-date",
        "order": "desc",
        "per_page": 100,
    }

    try:
        resp = requests.get(
            search_url,
            headers={**headers, "Accept": "application/vnd.github.cloak-preview+json"},
            params=params
        )

        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("items", []):
                commit = item.get("commit", {})
                author_date = commit.get("author", {}).get("date", "")

                if author_date:
                    commit_dt = datetime.fromisoformat(author_date.replace("Z", "+00:00"))

                    # Get detailed commit info for stats
                    commit_url = item.get("url")
                    additions = 0
                    deletions = 0

                    if commit_url:
                        detail_resp = requests.get(commit_url, headers=headers)
                        if detail_resp.status_code == 200:
                            detail = detail_resp.json()
                            stats = detail.get("stats", {})
                            additions = stats.get("additions", 0)
                            deletions = stats.get("deletions", 0)

                    # Extract repo name from URL
                    repo_name = item.get("repository", {}).get("full_name", "unknown")

                    commits.append({
                        "time": commit_dt.strftime("%H:%M"),
                        "datetime": commit_dt,
                        "repo": repo_name,
                        "message": commit.get("message", "").split("\n")[0],  # First line only
                        "sha": item.get("sha", "")[:7],
                        "additions": additions,
                        "deletions": deletions,
                        "changes": f"+{additions}/-{deletions}",
                        "url": item.get("html_url", ""),
                    })

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to connect to GitHub API: {e}")

    # If search didn't work well, fall back to events API
    if not commits:
        commits = get_commits_from_events(config, start, end, headers)

    # Sort by time
    commits.sort(key=lambda x: x.get("datetime", datetime.min), reverse=True)

    return commits


def get_commits_from_events(
    config: dict,
    start: datetime,
    end: datetime,
    headers: dict
) -> list[dict]:
    """
    Fallback method: Get commits from GitHub Events API.
    Events are only available for the last 90 days.
    """
    username = config.get("github_username")
    events_url = f"https://api.github.com/users/{username}/events"

    commits = []
    page = 1

    while page <= 10:  # Max 10 pages
        resp = requests.get(
            events_url,
            headers=headers,
            params={"page": page, "per_page": 100}
        )

        if resp.status_code != 200:
            break

        events = resp.json()
        if not events:
            break

        for event in events:
            if event.get("type") != "PushEvent":
                continue

            created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))

            # Check if within date range
            if created_at < start.replace(tzinfo=created_at.tzinfo):
                # Events are sorted by date, so we can stop here
                return commits

            if created_at > end.replace(tzinfo=created_at.tzinfo):
                continue

            repo_name = event.get("repo", {}).get("name", "unknown")
            payload = event.get("payload", {})

            for commit in payload.get("commits", []):
                commits.append({
                    "time": created_at.strftime("%H:%M"),
                    "datetime": created_at,
                    "repo": repo_name,
                    "message": commit.get("message", "").split("\n")[0],
                    "sha": commit.get("sha", "")[:7],
                    "additions": 0,
                    "deletions": 0,
                    "changes": "N/A",
                    "url": f"https://github.com/{repo_name}/commit/{commit.get('sha', '')}",
                })

        page += 1

    return commits


def test_github_connection(config: dict) -> bool:
    """Test if GitHub connection is working."""
    token = config.get("github_token")
    if not token:
        return False

    try:
        headers = {"Authorization": f"token {token}"}
        resp = requests.get("https://api.github.com/user", headers=headers)
        return resp.status_code == 200
    except Exception:
        return False
