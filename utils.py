from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

def parse_csv_emails(csv_text: str):
    if not csv_text:
        return []
    return [x.strip() for x in csv_text.split(",") if x.strip()]

def parse_offsets(text: str):
    if not text:
        return None
    out = []
    for x in text.split(","):
        x = x.strip()
        if not x:
            continue
        try:
            out.append(int(x))
        except ValueError:
            continue
    return sorted(set(out), reverse=True)  # highest first for clarity

def next_occurrence(anchor: date, interval_months: int, ref: date) -> date:
    """Return the next due date >= ref based on an anchor date and interval in months.
    interval_months == 0 means one-off; returns anchor if anchor >= ref else None.
    """
    if interval_months == 0:
        return anchor if anchor >= ref else None

    # Step forward in month increments until >= ref
    due = anchor
    if due >= ref:
        return due

    # Calculate rough number of intervals to jump
    # months_diff = (ref.year - anchor.year) * 12 + (ref.month - anchor.month)
    # intervals_to_add = (months_diff // interval_months)
    # due = anchor + relativedelta(months=intervals_to_add * interval_months)

    # Simpler but safe loop (intervals typically small)
    while due < ref:
        due = due + relativedelta(months=interval_months)
    return due

def generate_upcoming_occurrences(anchor: date, interval_months: int, start: date, end: date, max_count: int = 24):
    """Generate due dates within [start, end], up to max_count occurrences."""
    if interval_months == 0:
        if anchor >= start and anchor <= end:
            return [anchor]
        return []

    out = []
    due = next_occurrence(anchor, interval_months, start)
    while due and due <= end and len(out) < max_count:
        out.append(due)
        due = due + relativedelta(months=interval_months)
    return out

def should_send_for_due(due: date, today: date, offsets: list[int]) -> list[int]:
    """Return a list of offsets that match today for the given due date."""
    matches = []
    for off in offsets:
        if due - timedelta(days=off) == today:
            matches.append(off)
    return matches
