# Changelog

## 0.3.0 — 2026-10-20

- Added an **offline graphical browser dashboard** for volunteers and event teams, requiring no Python commands.
- Added form-based inventory and event editing with inline availability recalculation, equipment/status filtering and live summaries.
- Import JSON or CSV inventory, export CSV/JSON backups, and download self-contained HTML packing reports.
- New local event-editor inputs for confirmed, tentative and cancelled bookings with preparation and breakdown buffers.
- Included native Node.js test coverage for the browser calculation engine and cross-language comparison with the Python CLI.
- Documented local privacy and lack of automatic persistence; maintained fictional demonstration status for all sample data.


## 0.2.0 — 2026-10-20

- Import inventory from CSV, including UTF-8 BOM and optional category.
- Reserve equipment during optional setup and teardown windows.
- Support confirmed, tentative and cancelled event statuses.
- Export offline print-friendly HTML reports alongside Markdown, JSON and CSV.
- Explain conflicts using overlapping event IDs.
- Expand regression tests and provide a fictional realistic association scenario.
- Include operations guide and contributor-ready documentation.

## 0.1.0 — 2026-10-20

- Initial inventory and event JSON validation.
- Packing checklists and peak overlapping-booking shortage detection.
- Command-line interface, initial tests and CI workflow.
