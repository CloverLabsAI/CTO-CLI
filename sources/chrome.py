"""
Chrome browser history integration for Worklog CLI.
Reads directly from Chrome's local SQLite database.
"""

import platform
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_chrome_history_path(profile: str = "Default") -> Path:
    """Get the path to Chrome's history database based on OS."""
    system = platform.system()

    if system == "Darwin":  # macOS
        base = Path.home() / "Library/Application Support/Google/Chrome"
    elif system == "Windows":
        base = Path.home() / "AppData/Local/Google/Chrome/User Data"
    else:  # Linux
        base = Path.home() / ".config/google-chrome"

    return base / profile / "History"


def chrome_time_to_datetime(chrome_time: int) -> datetime:
    """
    Convert Chrome's timestamp format to Python datetime.
    Chrome uses microseconds since Jan 1, 1601.
    """
    # Chrome epoch is Jan 1, 1601. Unix epoch is Jan 1, 1970.
    # Difference is 11644473600 seconds
    if chrome_time == 0:
        return datetime.min

    seconds = (chrome_time / 1_000_000) - 11644473600
    try:
        return datetime.fromtimestamp(seconds)
    except (OSError, ValueError):
        return datetime.min


def get_chrome_history(
    start: datetime,
    end: datetime,
    chrome_profile: Optional[str] = "Default"
) -> list[dict]:
    """
    Fetch Chrome browsing history for a given date range.

    Note: Chrome locks its database while running, so we copy it first.
    """
    profile = chrome_profile or "Default"
    history_path = get_chrome_history_path(profile)

    if not history_path.exists():
        raise FileNotFoundError(f"Chrome history not found at {history_path}")

    # Copy the database to a temp file (Chrome locks the original)
    temp_dir = tempfile.mkdtemp()
    temp_db = Path(temp_dir) / "History"

    try:
        shutil.copy2(history_path, temp_db)
    except PermissionError:
        raise PermissionError(
            "Cannot access Chrome history. Please close Chrome and try again."
        )

    # Convert datetime to Chrome timestamp format
    def to_chrome_time(dt: datetime) -> int:
        return int((dt.timestamp() + 11644473600) * 1_000_000)

    start_chrome = to_chrome_time(start)
    end_chrome = to_chrome_time(end)

    history = []

    try:
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()

        # Query for URLs visited in the time range
        query = """
            SELECT
                urls.url,
                urls.title,
                visits.visit_time
            FROM urls
            JOIN visits ON urls.id = visits.url
            WHERE visits.visit_time >= ? AND visits.visit_time <= ?
            ORDER BY visits.visit_time DESC
        """

        cursor.execute(query, (start_chrome, end_chrome))

        for row in cursor.fetchall():
            url, title, visit_time = row

            # Skip empty titles and internal chrome pages
            if not title or url.startswith("chrome://") or url.startswith("chrome-extension://"):
                continue

            visit_dt = chrome_time_to_datetime(visit_time)

            history.append({
                "url": url,
                "title": title,
                "time": visit_dt.strftime("%H:%M"),
                "datetime": visit_dt,
            })

        conn.close()

    finally:
        # Clean up temp file
        try:
            Path(temp_db).unlink()
            Path(temp_dir).rmdir()
        except Exception:
            pass

    return history


def test_chrome_access(profile: Optional[str] = "Default") -> bool:
    """Test if Chrome history is accessible."""
    try:
        history_path = get_chrome_history_path(profile or "Default")
        return history_path.exists()
    except Exception:
        return False
