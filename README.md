# StageLedger

[![Python tests](https://github.com/Lucoroco/stageledger/actions/workflows/tests.yml/badge.svg)](https://github.com/Lucoroco/stageledger/actions/workflows/tests.yml)

**Open-source equipment planning for community events, student societies and small AV teams.**

StageLedger takes a shared equipment inventory and scheduled event requirements, then produces a packing checklist and flags equipment shortages caused by overlapping bookings. No accounts, cloud subscriptions or external Python dependencies are required.

> **Status:** early working prototype (v0.1.0). Contributions and real-world feedback are welcome. No adoption or download statistics are claimed.

## Why this project exists

Small volunteer-led events often coordinate speakers, microphones, stands and lighting using messages or spreadsheets. StageLedger provides a reproducible, human-readable checklist and a simple way to spot booking collisions before an event starts.

## Features

- Validate equipment inventories and upcoming event requirements
- Detect booking collisions using timezone-aware date and time ranges
- Correctly handle back-to-back events (no false overlap)
- Generate Markdown packing checklists, JSON plans or CSV tables
- Audit every scheduled event in one command
- Runs offline with Python 3.10+, using only the standard library

## Quick start

Clone the repository, then run from the repository directory:

    python -m stageledger plan --inventory examples/inventory.json --events examples/events.json --event community-concert

For CSV export:

    python -m stageledger plan --inventory examples/inventory.json --events examples/events.json --event community-concert --format csv --output packing.csv

Audit every scheduled event:

    python -m stageledger audit --inventory examples/inventory.json --events examples/events.json

Install the command-line tool locally (optional):

    python -m pip install -e .
    stageledger --help

**Exit codes:** `0` = plan ready, `1` = invalid input/file error, `2` = shortages present.

## JSON format

See `examples/inventory.json` and `examples/events.json`. IDs must be unique; inventory quantities are non-negative integers and requirement quantities are positive integers. Timestamps must use ISO 8601 with a timezone.

Time intervals are half-open `[start, end)`: back-to-back bookings are not counted as overlapping.

The shortage check uses **peak simultaneous demand** from other events; it does not naively sum events which overlap the target at different times.

## Tests

    python -m unittest discover -s tests -v

## Limitations and roadmap

This first version is deliberately offline. It does not track transport time, setup/teardown, broken equipment, individual serial numbers or staff. Include preparation and transport buffers explicitly in the booking windows.

Potential future features (not implemented): CSV import, reusable equipment presets, browser UI and individual asset reservations.

## Contributing / license

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [LICENSE](LICENSE). Avoid including real attendee personal data in public examples.
