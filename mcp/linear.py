"""
Linear MCP Server for CTO CLI.
Provides tools for querying Linear audit logs and workspace data.
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Optional

# Linear GraphQL API endpoint
LINEAR_API_URL = "https://api.linear.app/graphql"


class LinearMCPServer:
    """MCP server for Linear integration."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }

    def _query(self, query: str, variables: dict = None) -> dict:
        """Execute a GraphQL query against Linear API."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            LINEAR_API_URL,
            headers=self.headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(f"Linear API error: {response.status_code} - {response.text}")

        data = response.json()
        if "errors" in data:
            raise Exception(f"Linear GraphQL error: {data['errors']}")

        return data.get("data", {})

    def get_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
        actor_email: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Fetch audit log entries from Linear.

        Args:
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            event_type: Filter by event type (e.g., 'login', 'issue.create')
            actor_email: Filter by actor's email
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        # Build filter
        filters = []
        if event_type:
            filters.append(f'type: {{eq: "{event_type}"}}')
        if actor_email:
            filters.append(f'actor: {{email: {{eq: "{actor_email}"}}}}')
        if start_date:
            filters.append(f'createdAt: {{gte: "{start_date.isoformat()}"}}')
        if end_date:
            filters.append(f'createdAt: {{lte: "{end_date.isoformat()}"}}')

        filter_str = ""
        if filters:
            filter_str = f"filter: {{{', '.join(filters)}}}, "

        query = f"""
        query {{
            auditEntries({filter_str}first: {limit}) {{
                nodes {{
                    id
                    type
                    createdAt
                    ip
                    countryCode
                    actor {{
                        id
                        name
                        email
                    }}
                    metadata
                }}
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
            }}
        }}
        """

        data = self._query(query)
        entries = data.get("auditEntries", {}).get("nodes", [])

        return [
            {
                "id": e.get("id"),
                "type": e.get("type"),
                "timestamp": e.get("createdAt"),
                "ip": e.get("ip"),
                "country": e.get("countryCode"),
                "actor": e.get("actor", {}).get("name") or e.get("actor", {}).get("email"),
                "actor_email": e.get("actor", {}).get("email"),
                "metadata": e.get("metadata"),
            }
            for e in entries
        ]

    def get_audit_entry_types(self) -> list[dict]:
        """Get all available audit log entry types."""
        query = """
        query {
            auditEntryTypes {
                type
                description
            }
        }
        """
        data = self._query(query)
        return data.get("auditEntryTypes", [])

    def get_my_issues(
        self,
        state: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Get issues assigned to the authenticated user.

        Args:
            state: Filter by state (e.g., 'started', 'completed', 'canceled')
            limit: Maximum number of issues

        Returns:
            List of issues
        """
        filter_str = ""
        if state:
            filter_str = f'filter: {{state: {{name: {{eq: "{state}"}}}}}}, '

        query = f"""
        query {{
            viewer {{
                assignedIssues({filter_str}first: {limit}) {{
                    nodes {{
                        id
                        identifier
                        title
                        description
                        priority
                        createdAt
                        updatedAt
                        state {{
                            name
                            color
                        }}
                        project {{
                            name
                        }}
                        team {{
                            name
                        }}
                        labels {{
                            nodes {{
                                name
                                color
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """

        data = self._query(query)
        issues = data.get("viewer", {}).get("assignedIssues", {}).get("nodes", [])

        return [
            {
                "id": i.get("identifier"),
                "title": i.get("title"),
                "description": (i.get("description") or "")[:200],
                "priority": i.get("priority"),
                "state": i.get("state", {}).get("name"),
                "project": i.get("project", {}).get("name") if i.get("project") else None,
                "team": i.get("team", {}).get("name"),
                "labels": [l.get("name") for l in i.get("labels", {}).get("nodes", [])],
                "created_at": i.get("createdAt"),
                "updated_at": i.get("updatedAt"),
            }
            for i in issues
        ]

    def get_my_activity(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Get recent activity/issues I've worked on.

        Args:
            start_date: Filter activity after this date
            end_date: Filter activity before this date
            limit: Maximum number of items

        Returns:
            List of recently updated issues
        """
        filter_parts = []
        if start_date:
            filter_parts.append(f'updatedAt: {{gte: "{start_date.isoformat()}"}}')
        if end_date:
            filter_parts.append(f'updatedAt: {{lte: "{end_date.isoformat()}"}}')

        filter_str = ""
        if filter_parts:
            filter_str = f"filter: {{{', '.join(filter_parts)}}}, "

        query = f"""
        query {{
            viewer {{
                assignedIssues({filter_str}first: {limit}, orderBy: updatedAt) {{
                    nodes {{
                        id
                        identifier
                        title
                        state {{
                            name
                        }}
                        updatedAt
                        team {{
                            name
                        }}
                    }}
                }}
            }}
        }}
        """

        data = self._query(query)
        issues = data.get("viewer", {}).get("assignedIssues", {}).get("nodes", [])

        return [
            {
                "id": i.get("identifier"),
                "title": i.get("title"),
                "state": i.get("state", {}).get("name"),
                "team": i.get("team", {}).get("name"),
                "updated_at": i.get("updatedAt"),
            }
            for i in issues
        ]

    def get_teams(self) -> list[dict]:
        """Get all teams in the workspace."""
        query = """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                    members {
                        nodes {
                            id
                            name
                            email
                        }
                    }
                }
            }
        }
        """

        data = self._query(query)
        teams = data.get("teams", {}).get("nodes", [])

        return [
            {
                "id": t.get("id"),
                "name": t.get("name"),
                "key": t.get("key"),
                "description": t.get("description"),
                "members": [
                    {"name": m.get("name"), "email": m.get("email")}
                    for m in t.get("members", {}).get("nodes", [])
                ],
            }
            for t in teams
        ]

    def get_projects(self, team_key: Optional[str] = None, include_completed: bool = False) -> list[dict]:
        """
        Get projects with their latest status/health updates.

        Args:
            team_key: Filter by team key (e.g., 'ENG')
            include_completed: Include completed/canceled projects

        Returns:
            List of projects sorted by last status update
        """
        filter_parts = []
        if team_key:
            filter_parts.append(f'accessibleTeams: {{key: {{eq: "{team_key}"}}}}')
        if not include_completed:
            # Only include active projects (not completed or canceled)
            filter_parts.append('state: {nin: ["completed", "canceled"]}')

        filter_str = ""
        if filter_parts:
            filter_str = f"filter: {{{', '.join(filter_parts)}}}, "

        query = f"""
        query {{
            projects({filter_str}first: 100, orderBy: updatedAt) {{
                nodes {{
                    id
                    name
                    description
                    state
                    progress
                    health
                    targetDate
                    startDate
                    updatedAt
                    createdAt
                    lead {{
                        name
                    }}
                    teams {{
                        nodes {{
                            name
                            key
                        }}
                    }}
                    projectUpdates(first: 10, orderBy: createdAt) {{
                        nodes {{
                            id
                            body
                            health
                            createdAt
                            user {{
                                name
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """

        data = self._query(query)
        projects = data.get("projects", {}).get("nodes", [])

        result = []
        for p in projects:
            # Get all project updates
            updates = p.get("projectUpdates", {}).get("nodes", [])
            latest_update = updates[0] if updates else None

            # Find the most recent update that has a health value
            latest_health_update = None
            for update in updates:
                if update.get("health"):
                    latest_health_update = update
                    break  # Already sorted by createdAt desc, so first match is most recent

            result.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "description": (p.get("description") or "")[:200],
                "state": p.get("state"),
                "progress": p.get("progress"),
                "health": p.get("health"),
                "target_date": p.get("targetDate"),
                "start_date": p.get("startDate"),
                "updated_at": p.get("updatedAt"),
                "created_at": p.get("createdAt"),
                "lead": p.get("lead", {}).get("name") if p.get("lead") else None,
                "teams": [t.get("name") for t in p.get("teams", {}).get("nodes", [])],
                "latest_update": {
                    "body": (latest_update.get("body") or "")[:200] if latest_update else None,
                    "health": latest_update.get("health") if latest_update else None,
                    "created_at": latest_update.get("createdAt") if latest_update else None,
                    "author": latest_update.get("user", {}).get("name") if latest_update else None,
                } if latest_update else None,
                # Use the health update timestamp for sorting, fallback to any update, then project update
                "health_updated_at": latest_health_update.get("createdAt") if latest_health_update else None,
                "latest_health": latest_health_update.get("health") if latest_health_update else None,
                "status_updated_at": latest_update.get("createdAt") if latest_update else p.get("updatedAt"),
            })

        return result

    def search_issues(self, query_text: str, limit: int = 20) -> list[dict]:
        """
        Search for issues by text.

        Args:
            query_text: Search query
            limit: Maximum results

        Returns:
            List of matching issues
        """
        query = """
        query($query: String!, $limit: Int!) {
            searchIssues(query: $query, first: $limit) {
                nodes {
                    id
                    identifier
                    title
                    description
                    state {
                        name
                    }
                    team {
                        name
                    }
                    assignee {
                        name
                    }
                }
            }
        }
        """

        variables = {"query": query_text, "limit": limit}
        data = self._query(query, variables)
        issues = data.get("searchIssues", {}).get("nodes", [])

        return [
            {
                "id": i.get("identifier"),
                "title": i.get("title"),
                "description": (i.get("description") or "")[:150],
                "state": i.get("state", {}).get("name"),
                "team": i.get("team", {}).get("name"),
                "assignee": i.get("assignee", {}).get("name") if i.get("assignee") else None,
            }
            for i in issues
        ]

    def get_viewer(self) -> dict:
        """Get information about the authenticated user."""
        query = """
        query {
            viewer {
                id
                name
                email
                admin
                organization {
                    name
                    urlKey
                }
            }
        }
        """

        data = self._query(query)
        viewer = data.get("viewer", {})

        return {
            "id": viewer.get("id"),
            "name": viewer.get("name"),
            "email": viewer.get("email"),
            "is_admin": viewer.get("admin"),
            "organization": viewer.get("organization", {}).get("name"),
            "org_url": viewer.get("organization", {}).get("urlKey"),
        }


def test_linear_connection(api_key: str) -> bool:
    """Test if Linear connection is working."""
    try:
        server = LinearMCPServer(api_key)
        viewer = server.get_viewer()
        return bool(viewer.get("id"))
    except Exception:
        return False


def get_linear_user_info(api_key: str) -> Optional[dict]:
    """Get info about the authenticated Linear user."""
    try:
        server = LinearMCPServer(api_key)
        return server.get_viewer()
    except Exception:
        return None
