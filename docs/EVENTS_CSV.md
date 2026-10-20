# Event planning from CSV (Excel and Google Sheets)

StageLedger can read both **inventory** and **events** directly from UTF-8 CSV files. No JSON editing is necessary.

## Spreadsheet format

Use one row per required equipment type. Events with several types appear on several rows, sharing the same event ID. The first row must include title and timestamps; later rows may leave unchanged booking fields blank.

| id | title | start | end | status | setup_minutes | teardown_minutes | item_id | quantity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gala | Community gala | 2026-11-21T18:00:00+00:00 | 2026-11-21T23:00:00+00:00 | confirmed | 90 | 60 | speaker | 3 |
| gala | *(blank)* | *(blank)* | *(blank)* | *(blank)* | *(blank)* | *(blank)* | microphone | 2 |

Columns `id,title,start,end,item_id,quantity` are required. `status`, `setup_minutes` and `teardown_minutes` can be omitted (defaults: confirmed, 0, 0). Use a single row with empty `item_id` and `quantity` for an event with no equipment.

**Validation:** conflicting titles, dates, statuses or buffers for one event ID are rejected. Duplicate item requirements are rejected. Use unique IDs and timezone-aware ISO 8601 dates. Numeric quantity must be a positive whole number. CSV formula input is treated as plain text; avoid sensitive information in shared examples.

## Run from your exported spreadsheets

```bash
python -m stageledger audit --inventory examples/inventory.csv --events examples/events.csv --format html --output schedule.html
python -m stageledger plan --inventory examples/inventory.csv --events examples/events.csv --event gala --format html --output packing.html
```

The demo intentionally includes a shortage, so exit code 2 is expected. Open the generated HTML file locally in a browser and print a PDF when required.

StageLedger is a planning aid, not a guarantee that a particular physical unit is operational or onsite.

## Continuation rows (since this fix)

For a repeated event ID, empty booking cells inherit values from its **first row**. Explicit values must agree; for example, setting `setup_minutes` to `0` on a continuation row conflicts with a first-row value of `90`. The first occurrence of an event still requires its title, start and end fields. Do not use this shorthand to hide inconsistent data. It also works when rows for different events are interleaved.
