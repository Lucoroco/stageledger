"""Read spreadsheet-friendly inventory CSV with strict validation."""
import csv
from pathlib import Path


def read_inventory_csv(path):
    """Parse inventory CSV; shared item checks run in core.load_inventory."""
    # Avoid circular imports: import only when CSV functionality is invoked.
    from stageledger.core import InputError

    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise InputError("CSV inventory is empty or missing a header row")
            header = [name.strip() for name in reader.fieldnames if name is not None]
            if len(set(header)) != len(header):
                raise InputError("CSV inventory has duplicate column names")
            missing = {"id", "name", "quantity"} - set(header)
            if missing:
                raise InputError("CSV inventory missing column(s): " + ", ".join(sorted(missing)))
            items = []
            for line, row in enumerate(reader, start=2):
                if None in row:
                    raise InputError(f"CSV inventory line {line}: too many columns")
                if not any(str(v or "").strip() for v in row.values()):
                    continue
                fields = {str(k).strip(): str(v or "").strip() for k, v in row.items()}
                number = fields.get("quantity", "")
                if not number.isdecimal() or any(c not in "0123456789" for c in number):
                    raise InputError(f"CSV inventory line {line}: quantity must be a non-negative integer")
                items.append({
                    "id": fields.get("id", ""),
                    "name": fields.get("name", ""),
                    "quantity": int(number),
                    "category": fields.get("category", ""),
                })
            return {"items": items}
    except (OSError, UnicodeError, csv.Error) as exc:
        raise InputError(f"Cannot read CSV inventory {path}: {exc}") from exc

EVENT_COLUMNS = ("id", "title", "start", "end", "status",
                 "setup_minutes", "teardown_minutes")


def read_events_csv(path):
    """Read event/item rows from CSV, accepting blank metadata on later rows.

    The first row of each event must define the title and time interval. Later
    rows with the same ID can leave these fields blank, or repeat their original
    values. An explicitly conflicting value is rejected rather than overwritten.
    """
    from stageledger.core import InputError

    def non_negative_minutes(value, line, field):
        if not value.isascii() or not value.isdecimal():
            raise InputError(
                f"Events CSV line {line}: {field} must be a non-negative integer"
            )
        return int(value)

    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or any(name is None for name in reader.fieldnames):
                raise InputError("Events CSV needs a valid header")
            headers = [name.strip() for name in reader.fieldnames]
            if len(set(headers)) != len(headers):
                raise InputError("Events CSV contains duplicate columns")
            missing = {"id", "title", "start", "end", "item_id", "quantity"} - set(headers)
            if missing:
                raise InputError(
                    "Events CSV missing columns: " + ", ".join(sorted(missing))
                )

            events = {}
            for line, row in enumerate(reader, 2):
                if None in row:
                    raise InputError(f"Events CSV line {line}: too many columns")
                cells = {
                    key.strip(): str(value or "").strip()
                    for key, value in row.items()
                }
                if not any(cells.values()):
                    continue

                event_id = cells["id"]
                if not event_id:
                    raise InputError(f"Events CSV line {line}: missing id")

                if event_id not in events:
                    # Require the booking identity and schedule once per event,
                    # not for every equipment line.
                    for field in ("title", "start", "end"):
                        if not cells[field]:
                            raise InputError(
                                f"Events CSV line {line}: first row for event "
                                f"'{event_id}' requires {field}"
                            )
                    metadata = {
                        "id": event_id,
                        "title": cells["title"],
                        "start": cells["start"],
                        "end": cells["end"],
                        "status": cells.get("status") or "confirmed",
                    }
                    for field in ("setup_minutes", "teardown_minutes"):
                        minutes = cells.get(field, "") or "0"
                        metadata[field] = non_negative_minutes(minutes, line, field)
                    events[event_id] = dict(metadata, requirements=[])
                else:
                    saved = events[event_id]
                    # Empty repeated metadata means "same as first row".
                    # Non-empty values must agree; never allow a silent override.
                    for field in EVENT_COLUMNS[1:]:
                        value = cells.get(field, "")
                        if not value:
                            continue
                        if field in ("setup_minutes", "teardown_minutes"):
                            value = non_negative_minutes(value, line, field)
                        if value != saved[field]:
                            raise InputError(
                                f"Events CSV line {line}: inconsistent {field} "
                                f"for event '{event_id}'"
                            )

                item_id, quantity = cells["item_id"], cells["quantity"]
                if not item_id and not quantity:
                    continue  # Valid event with no equipment requirements
                if (not item_id or not quantity or not quantity.isascii()
                        or not quantity.isdecimal()):
                    raise InputError(
                        f"Events CSV line {line}: invalid item_id/quantity"
                    )
                events[event_id]["requirements"].append({
                    "item_id": item_id,
                    "quantity": int(quantity),
                })
            return {"events": list(events.values())}
    except (OSError, UnicodeError, csv.Error) as exc:
        raise InputError(f"Cannot read events CSV {path}: {exc}") from exc
