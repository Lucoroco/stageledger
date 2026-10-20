# StageLedger roadmap

StageLedger is an offline, volunteer-oriented equipment planning prototype. This document distinguishes existing functionality from potential improvements.

## Implemented in v0.2

- Inventory in JSON or CSV with strict validation
- Conflict checking across overlapping reservations, including setup and teardown
- Confirmed, tentative and cancelled bookings
- Print-friendly HTML, Markdown, JSON and CSV packing reports
- CI-tested Python command-line interface and realistic **fictional** sample scenarios

## Next priorities

1. Test the application with **independent** event organisers and collect reproducible feedback with consent.
2. Extend the tool to individual serialized equipment assets and condition tracking.
3. Allow configurable logistics/transport delays between venues.
4. Add inventory CSV export and easy event authoring from spreadsheet data.
5. Improve accessibility of generated reports and the English/French documentation.
6. Consider a no-account local user interface if organisers confirm it is useful.

## Out of scope for the current prototype

- Staff payroll, billing and client CRM
- Guaranteed dispatch availability or complex routing
- Automatically verified physical inventory

Read [the evidence record](VALIDATION_AND_IMPACT.md). Example data are demonstrations, **not proof of customer adoption**. Open an issue to discuss substantial changes before implementing them.
