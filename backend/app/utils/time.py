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

def format_iso_utc(val) -> str:
    """Format datetime or timestamp string to standard ISO 8601 UTC format (e.g., 2026-09-04T18:00:00Z)."""
    if not val:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(val, str):
        val = parse_datetime(val)
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        else:
            val = val.astimezone(timezone.utc)
        return val.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(val)
