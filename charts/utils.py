"""Charts utility functions"""
from datetime import datetime, date


def _parse_date_str(date_value):
    """Parse date string or date object to date."""
    if not date_value:
        return None
    if isinstance(date_value, datetime):
        return date_value.date()
    if isinstance(date_value, date):
        return date_value
    s = str(date_value)
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).date()
    except Exception:
        pass
    for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None
