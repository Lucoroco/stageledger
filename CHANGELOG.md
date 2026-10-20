# Changelog

## 0.4.0 — 2026-10-20

- Introduced a graphical, responsive and **offline browser dashboard**, usable without Python commands.
- Added form-based inventory and booking management, live shortage summaries, search/filtering and HTML packing exports.
- Added browser-side CSV inventory import/export and JSON data backups, with no automatic storage or external API calls.
- Added native Node.js calculation tests and Python/JavaScript parity checks in GitHub Actions.
- Updated accessibility, local privacy instructions and honest evidence documentation.


## 0.3.0 — 2026-10-20

- Import event schedules directly from CSV files exported from Excel or Google Sheets.
- Support multiple equipment types per event with strict consistency checks.
- Include spreadsheet-ready example events and step-by-step CSV documentation.
- Add tests for grouping, malformed rows, duplicate item requirements and end-to-end HTML export.

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
