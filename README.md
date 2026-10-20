# StageLedger

[![Python tests](https://github.com/Lucoroco/stageledger/actions/workflows/tests.yml/badge.svg)](https://github.com/Lucoroco/stageledger/actions/workflows/tests.yml) [![Browser and parity tests](https://github.com/Lucoroco/stageledger/actions/workflows/browser-tests.yml/badge.svg)](https://github.com/Lucoroco/stageledger/actions/workflows/browser-tests.yml)

**Open-source equipment booking and event packing for associations, student societies and small AV teams.**

StageLedger coordinates speakers, microphones, lighting and cables across overlapping events. It validates local data, flags equipment shortages and exports printable checklists — **offline**, without accounts, a server, telemetry or paid dependencies.

> **Status:** v0.3 public prototype with an offline browser dashboard and Python CLI. The source and tests are verifiable; independent adoption and external contributors are **not yet verified**. All provided association examples are fictional demonstrations.

## Features

| Feature | Benefit |
| --- | --- |
| Browser interface | Add equipment, edit bookings and download reports with no Python commands |
| Equipment inventory | Track pooled quantities by item type |
| CSV and JSON input | Export equipment from a spreadsheet or use JSON |
| Booking conflicts | Compare peak simultaneous demand across events |
| Setup and teardown | Reserve items before and after each event |
| Booking statuses | Confirmed, tentative and cancelled events |
| Packing lists | Markdown, JSON, CSV and offline printable HTML |
| Schedule audit | Analyse all non-cancelled events at once |
| Validation | Clear errors for duplicate IDs, quantities and timestamps |

## Easiest start: browser dashboard (no installation)

1. [Download the source ZIP](https://github.com/Lucoroco/stageledger/archive/refs/heads/main.zip) and extract it.
2. Open **`web/index.html`** in your browser, keeping the other files in `web/` next to it.
3. Browse the **fictional demo**, then add your own equipment or import a spreadsheet CSV.
4. Add bookings with setup/teardown buffers. View shortage warnings and generate packing reports.
5. Export your inventory and events as JSON **before closing or refreshing**. There is no automatic save or cloud sync.

**No server, account or Python install is needed for the browser dashboard.** Full details: [browser user guide](web/README.md). The browser inputs use your device's local timezone and save dates as UTC. If you need unattended integrations or scripts, use the Python CLI below.

## Command-line quick start (Python 3.10+)

[Download ZIP](https://github.com/Lucoroco/stageledger/archive/refs/heads/main.zip), extract it and open a terminal in the project directory. Alternatively clone the repository.

Generate an equipment checklist:

```bash
python -m stageledger plan --inventory examples/inventory.csv --events examples/events.json --event community-concert --format html --output packing.html
```

Open `packing.html` in your browser. You can **Print / Save PDF** to give a list to your crew. The sample intentionally has an equipment shortage: exit code `2` is expected.

Audit a richer, fictional association scenario:

```bash
python -m stageledger audit --inventory examples/association_inventory.json --events examples/association_events.json --format html --output audit.html
```

For Windows, see the [PowerShell quick start](docs/QUICKSTART_WINDOWS.md). Optional command-line installation:

```bash
python -m pip install -e .
stageledger --help
```

## Data example

Inventory can be provided as CSV:

```csv
id,name,quantity,category
pa-top,Active PA top,4,Audio
wireless-mic,Wireless microphone,4,Microphones
```

Schedule events in a JSON file:

```json
{
  "events": [{
    "id": "campus-talk",
    "title": "Campus talk",
    "status": "confirmed",
    "start": "2026-11-21T18:00:00+00:00",
    "end": "2026-11-21T20:00:00+00:00",
    "setup_minutes": 60,
    "teardown_minutes": 30,
    "requirements": [
      {"item_id": "pa-top", "quantity": 2},
      {"item_id": "wireless-mic", "quantity": 1}
    ]
  }]
}
```

The speaker stock for this event is reserved **17:00–20:30 UTC**, including preparation. Other events competing in that interval reduce availability.

## CLI commands

| Command or argument | Purpose |
| --- | --- |
| `python -m stageledger plan --inventory FILE --events FILE --event ID` | Packing plan for one event |
| `python -m stageledger audit --inventory FILE --events FILE` | All active-event shortages |
| `--format html --output FILE` | Offline print-friendly report |
| `--format csv` | Single-event spreadsheet output |
| `--format json` | Structured report for other tools |
| `--format markdown` | Markdown packing checklist |
| `python -m unittest discover -s tests -v` | Run all tests |

**Exit codes:** `0` = enough equipment; `1` = invalid input or file error; `2` = one or more shortages.

**Booking policy:** `tentative` bookings reserve inventory until cancelled; cancelled events are excluded. Dates must be timezone-aware ISO 8601. Intervals are half-open: adjacent bookings don't overlap unless their buffers do. Availability uses **peak simultaneous demand** (not a sum of disjoint competing bookings).

## Known limitations

- Quantities are pooled per item type, not tracked by serial number.
- Equipment condition, staff, travel routing, supplier orders and deposits are not managed.
- Transport time needs to be included in setup/teardown buffers.
- Browser dashboard data stays in memory until explicitly exported; a reload discards unsaved edits.
- HTML reports are local exports, not a hosted booking service.
- Do not expose personal information or real client schedules in public GitHub issues.

See the [operations guide](docs/OPERATIONS_GUIDE.md) for workflows and validation details.

## Community and development

- [Browser dashboard](web/index.html) and [browser guide](web/README.md)
- [Roadmap](docs/ROADMAP.md) and [changelog](CHANGELOG.md)
- [Open issues and feature requests](https://github.com/Lucoroco/stageledger/issues)
- [Contributing instructions](CONTRIBUTING.md)
- [Security guidance](SECURITY.md) · [Code of conduct](CODE_OF_CONDUCT.md)
- [Evidence and impact record](docs/VALIDATION_AND_IMPACT.md)

Real, independently tested feedback is welcome. We do not claim adoption, external contributors or registry downloads without proof. Development has included AI assistance, as disclosed in the evidence record.

**Licence:** MIT.
