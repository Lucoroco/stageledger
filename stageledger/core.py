"""Validated inventory, event scheduling, and equipment shortage calculations."""

from datetime import datetime, timezone
from pathlib import Path
import json


class InputError(ValueError):
    """Raised when inventory or event data is invalid."""


def _positive_int(value, context, *, allow_zero=False):
    if type(value) is not int or value < (0 if allow_zero else 1):
        minimum = 0 if allow_zero else 1
        raise InputError(f"{context} must be an integer >= {minimum}")
    return value


def _text(value, context):
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{context} must be a non-empty string")
    return value.strip()


def _timestamp(value, context):
    value = _text(value, context)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InputError(f"{context} must be an ISO 8601 timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise InputError(f"{context} must include a timezone (e.g. +00:00 or Z)")
    return dt.astimezone(timezone.utc)


def _json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"Cannot read JSON from {path}: {exc}") from exc


def load_inventory(path):
    """Return inventory indexed by unique item IDs."""
    raw = _json(path)
    if not isinstance(raw, dict) or not isinstance(raw.get("items"), list):
        raise InputError("inventory JSON must contain an 'items' array")
    items = {}
    for index, item in enumerate(raw["items"]):
        label = f"items[{index}]"
        if not isinstance(item, dict):
            raise InputError(f"{label} must be an object")
        item_id = _text(item.get("id"), f"{label}.id")
        if item_id in items:
            raise InputError(f"Duplicate inventory ID: {item_id}")
        items[item_id] = {
            "id": item_id,
            "name": _text(item.get("name"), f"{label}.name"),
            "quantity": _positive_int(item.get("quantity"), f"{label}.quantity", allow_zero=True),
            "category": str(item.get("category", "")).strip(),
        }
    return items


def load_events(path, inventory):
    """Validate event times and quantities; return events sorted by start."""
    raw = _json(path)
    if not isinstance(raw, dict) or not isinstance(raw.get("events"), list):
        raise InputError("events JSON must contain an 'events' array")
    events = []
    seen = set()
    for index, event in enumerate(raw["events"]):
        label = f"events[{index}]"
        if not isinstance(event, dict):
            raise InputError(f"{label} must be an object")
        event_id = _text(event.get("id"), f"{label}.id")
        if event_id in seen:
            raise InputError(f"Duplicate event ID: {event_id}")
        seen.add(event_id)
        title = _text(event.get("title"), f"{label}.title")
        start = _timestamp(event.get("start"), f"{label}.start")
        end = _timestamp(event.get("end"), f"{label}.end")
        if start >= end:
            raise InputError(f"{label}.end must be later than start")
        raw_requirements = event.get("requirements")
        if not isinstance(raw_requirements, list):
            raise InputError(f"{label}.requirements must be an array")
        requirements = {}
        for j, requirement in enumerate(raw_requirements):
            ref = f"{label}.requirements[{j}]"
            if not isinstance(requirement, dict):
                raise InputError(f"{ref} must be an object")
            item_id = _text(requirement.get("item_id"), f"{ref}.item_id")
            if item_id not in inventory:
                raise InputError(f"{ref}: unknown inventory item '{item_id}'")
            if item_id in requirements:
                raise InputError(f"{ref}: duplicate item '{item_id}'")
            requirements[item_id] = _positive_int(requirement.get("quantity"), f"{ref}.quantity")
        events.append({
            "id": event_id,
            "title": title,
            "start": start,
            "end": end,
            "requirements": requirements,
        })
    return sorted(events, key=lambda event: (event["start"], event["id"]))


def _peak_other_demand(event, others, item_id):
    """Maximum competing bookings at one instant during this event.

    Uses half-open intervals [start, end): one event ending when another
    starts is not a conflict. We count only actual overlapping windows.
    """
    changes = []
    for other in others:
        if other["id"] == event["id"]:
            continue
        count = other["requirements"].get(item_id, 0)
        start = max(event["start"], other["start"])
        end = min(event["end"], other["end"])
        if count and start < end:
            changes.extend(((start, count), (end, -count)))
    used, peak = 0, 0
    for _, delta in sorted(changes, key=lambda p: (p[0], p[1])):
        used += delta
        peak = max(peak, used)
    return peak


def build_plan(event_id, inventory, events):
    """Build an equipment checklist and shortages for one event."""
    event = next((item for item in events if item["id"] == event_id), None)
    if event is None:
        raise InputError(f"Unknown event ID: {event_id}")
    rows = []
    for item_id, requested in sorted(event["requirements"].items()):
        item = inventory[item_id]
        competing = _peak_other_demand(event, events, item_id)
        available = max(0, item["quantity"] - competing)
        shortage = max(0, requested - available)
        rows.append({
            "id": item_id, "name": item["name"],
            "category": item["category"], "requested": requested,
            "owned": item["quantity"], "other_bookings_peak": competing,
            "available": available, "shortage": shortage,
        })
    return {
        "event": event["id"], "title": event["title"],
        "start": event["start"].isoformat(), "end": event["end"].isoformat(),
        "ready": all(row["shortage"] == 0 for row in rows),
        "items": rows,
    }


def audit(inventory, events):
    """Return plans for every event, including conflicts between bookings."""
    return [build_plan(event["id"], inventory, events) for event in events]
