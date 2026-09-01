"""Pure helpers shared by Voltcast action entities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def parse_utc(value: str | None) -> datetime | None:
    """Parse an API timestamp into a timezone-aware UTC datetime."""
    if not value:
        return None

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def recommended_window(data: dict[str, Any]) -> dict[str, Any] | None:
    """Return the API's highest-ranked optimization window."""
    windows = data.get("optimization", {}).get("data", [])
    return windows[0] if windows else None


def charge_now(data: dict[str, Any], now: datetime | None = None) -> bool:
    """Whether the current instant sits inside the recommended window."""
    window = recommended_window(data)
    if window is None:
        return False

    start = parse_utc(window.get("start"))
    end = parse_utc(window.get("end"))
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    return start is not None and end is not None and start <= current < end


def negative_risk(
    data: dict[str, Any],
    now: datetime | None = None,
    horizon: timedelta = timedelta(hours=24),
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Summarize negative-price risk inside the next action horizon."""
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    until = current + horizon
    risk_data = data.get("risk", {}).get("data", {})
    rows = risk_data.get("curve", []) if isinstance(risk_data, dict) else []
    upcoming: list[dict[str, Any]] = []

    for row in rows:
        start = parse_utc(row.get("target_start"))
        if start is not None and current <= start < until:
            upcoming.append(row)

    qualifying = [
        row for row in upcoming if float(row.get("p_negative", 0)) >= threshold
    ]
    first = min(qualifying, key=lambda row: row["target_start"], default=None)
    maximum = max(
        (float(row.get("p_negative", 0)) for row in upcoming),
        default=0.0,
    )

    return {
        "incoming": first is not None,
        "next_start": first.get("target_start") if first else None,
        "next_probability": float(first["p_negative"]) if first else None,
        "max_probability": maximum,
        "threshold": threshold,
        "horizon_hours": int(horizon.total_seconds() / 3600),
    }
