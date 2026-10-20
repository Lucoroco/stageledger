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
