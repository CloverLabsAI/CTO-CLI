"""
Date parsing and range utilities for Worklog CLI.
"""

import calendar as cal
from datetime import datetime, timedelta


def parse_date(date_str: str) -> datetime:
    """Parse a date string in various formats."""
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {date_str}")


def get_date_range(date: datetime) -> tuple[datetime, datetime]:
    """Get start and end of day for a given date."""
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def get_week_range(date: datetime) -> tuple[datetime, datetime]:
    """Get start (Monday) and end (Sunday) of the week containing the given date."""
    start = date - timedelta(days=date.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=6)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def get_month_range(year: int, month: int) -> tuple[datetime, datetime]:
    """Get start and end of a given month."""
    start = datetime(year, month, 1, 0, 0, 0, 0)
    last_day = cal.monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59, 999999)
    return start, end


def parse_week(week_str: str) -> tuple[int, int]:
    """Parse a week string like '2024-W03' or just '3' for current year."""
    if '-W' in week_str.upper():
        parts = week_str.upper().split('-W')
        return int(parts[0]), int(parts[1])
    else:
        return datetime.now().year, int(week_str)


def parse_month(month_str: str) -> tuple[int, int]:
    """Parse a month string like '2024-01', 'January', or just '1' for current year."""
    month_names = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }

    if '-' in month_str:
        parts = month_str.split('-')
        return int(parts[0]), int(parts[1])
    elif month_str.lower() in month_names:
        return datetime.now().year, month_names[month_str.lower()]
    else:
        return datetime.now().year, int(month_str)
