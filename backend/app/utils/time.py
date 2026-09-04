from datetime import datetime, timezone

def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO formatted timestamp string or return current UTC time."""
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)

def format_iso(dt: datetime) -> str:
    """Format datetime to standard ISO string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
