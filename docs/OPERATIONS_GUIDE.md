# Operations guide: planning real events

StageLedger is a local-first tool for **planning pooled equipment counts**, not a production ERP or guarantee of fulfilment. Always verify hardware condition and physical logistics before committing equipment.

## Typical workflow

1. Make a **copy** of your inventory, remove private details and validate unit counts.
2. Export a spreadsheet as UTF-8 CSV with columns `id,name,quantity,category`, or use JSON.
3. Add future events to `events.json`, including status and time buffers.
4. Run `audit` to identify at-risk equipment and schedule collisions.
5. Resolve shortages by changing bookings, sourcing rentals or adding stock.
6. Run `plan` to generate one event's packing list; print an HTML copy for crew.

## Commands

From the repository folder:

```bash
python -m stageledger audit --inventory examples/association_inventory.json --events examples/association_events.json --format html --output audit.html
python -m stageledger plan --inventory examples/association_inventory.json --events examples/association_events.json --event student-gala --format html --output packing.html
python -m stageledger plan --inventory examples/inventory.csv --events examples/events.json --event community-concert --format csv --output packing.csv
```

Open `audit.html` in your browser. You can use the **Print / Save PDF** button without uploading any data.

**Exit codes:** `0` = no shortages; `1` = input/IO error; `2` = shortage detected. Code 2 can be expected for the intentionally conflicting demo schedules.

## Equipment catalogue

CSV:

```csv
id,name,quantity,category
pa-top,Active PA top,4,Sound
wireless-mic,Wireless microphone,4,Microphones
```

- Use unique stable IDs (e.g. `pa-top`). Item names can be changed freely.
- Count identical interchangeable units within each inventory type.
- A value of 0 represents an unavailable or unowned item.
- Treat incompatible models or kit variants as separate items.
- CSV accepts UTF-8 BOM, blank lines and an optional `category` column.

## Event fields

```json
{
  "id": "community-event",
  "title": "Community event",
  "status": "confirmed",
  "start": "2026-11-21T18:00:00+00:00",
  "end": "2026-11-21T22:00:00+00:00",
  "setup_minutes": 90,
  "teardown_minutes": 60,
  "requirements": [{"item_id": "pa-top", "quantity": 2}]
}
```

- `start` and `end` require explicit timezone offsets. Times are normalised to UTC.
- `setup_minutes` reserves stock **before** the event; `teardown_minutes` reserves stock **after** it. Both default to zero.
- `status` can be `confirmed` (default), `tentative` or `cancelled`.
- Tentative bookings conservatively reserve inventory until cancelled.
- Cancelled events do not reserve inventory and do not appear in audit reports.
- For an event scheduled from 18:00–22:00, with 90 minutes setup and 60 minutes teardown, stock is reserved from 16:30–23:00.
- Two adjacent events do not conflict unless their **effective equipment reservation windows** overlap.

## Understanding availability

For each required equipment type, StageLedger calculates the **peak simultaneous demand from other non-cancelled bookings** during that event's full reservation window.

Example: 4 speakers in stock, your event needs 3, and another overlapping event needs 2. Only 2 speakers remain, so the tool reports a shortage of 1.

The report lists the names/IDs of overlapping events for investigation. These overlapping events may not all be simultaneous; the shortage calculation uses the actual peak rather than summing all overlapping event requests.

**Limitations:** stock is pooled by item type. No asset-level serial numbers, team staffing, transport between venues, supplier rentals, travel time or damaged-inventory register are supported. Transport must be modelled by extending reservation buffers. Do not put customer contact details in public examples or issues.

## Evidence and independent feedback

The provided association scenarios are **invented demonstration data**, not a claim that LUKA LIVE or any other organisation has tested or adopted the software.

If using this with a real association, log the tester's permission, what data was trialled (anonymised), what the tool found and any concrete follow-up work. See [validation and impact](VALIDATION_AND_IMPACT.md).
