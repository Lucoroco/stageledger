# Event planning from CSV (Excel and Google Sheets)

StageLedger can read both **inventory** and **events** directly from UTF-8 CSV files. No JSON editing is necessary.

## Spreadsheet format

Use one row per required equipment type. The **first row for each event ID** must include its title, start and end. Further equipment rows with the same event ID may omit the repeated booking metadata (title, dates, status and setup/teardown times), or repeat matching values. **The event ID must still appear on every row.**

For example, these two rows belong to the same event; the second row inherits its event details:

```csv
id,title,start,end,status,setup_minutes,teardown_minutes,item_id,quantity
gala,Community gala,2026-11-21T18:00:00+00:00,2026-11-21T23:00:00+00:00,confirmed,90,60,speaker,3
gala,,,,,,,microphone,2
```

If an event ID appears later in the file (even after other events), blank booking metadata will still inherit from its **own first row**, never from a different event.

| id | title | start | end | status | setup_minutes | teardown_minutes | item_id | quantity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gala | Community gala | 2026-11-21T18:00:00+00:00 | 2026-11-21T23:00:00+00:00 | confirmed | 90 | 60 | speaker | 3 |
| gala | Community gala | 2026-11-21T18:00:00+00:00 | 2026-11-21T23:00:00+00:00 | confirmed | 90 | 60 | microphone | 2 |

Columns `id,title,start,end,item_id,quantity` are required. `status`, `setup_minutes` and `teardown_minutes` can be omitted (defaults: confirmed, 0, 0). Use a single row with empty `item_id` and `quantity` for an event with no equipment.

**Validation:** explicitly conflicting titles, dates, statuses or buffers for one event ID are rejected, even on continuation rows. A first event row missing its title, start or end is rejected; blank metadata only works on subsequent rows of an existing event. Duplicate item requirements are rejected. Use unique IDs and timezone-aware ISO 8601 dates. Numeric quantity must be a positive whole number. CSV formula input is treated as plain text; avoid sensitive information in shared examples.

## Run from your exported spreadsheets

```bash
python -m stageledger audit --inventory examples/inventory.csv --events examples/events.csv --format html --output schedule.html
python -m stageledger plan --inventory examples/inventory.csv --events examples/events.csv --event gala --format html --output packing.html
```

The demo intentionally includes a shortage, so exit code 2 is expected. Open the generated HTML file locally in a browser and print a PDF when required.

StageLedger is a planning aid, not a guarantee that a particular physical unit is operational or onsite.
