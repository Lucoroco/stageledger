# Browser dashboard · StageLedger

The `web/` folder contains an **offline, client-side dashboard**. There is no server, login or telemetry. JavaScript executes in your browser; JSON and CSV files are never uploaded by the app.

## Run without installing Python

1. Download the [repository ZIP](https://github.com/Lucoroco/stageledger/archive/refs/heads/main.zip) and extract it.
2. Keep `web/index.html`, `web/app.js`, `web/engine.js` and `web/style.css` together in the same folder.
3. Double-click `web/index.html` in an up-to-date browser.
4. The application opens with **fictional demonstration data**. Use **Reset demo** to restore them.
5. Import a real inventory CSV/JSON, then import events JSON or create events by filling in the form.
6. Export your inventory and events to JSON and download printable packing reports.

**Important:** Your unsaved edits live in your current browser tab. Closing or refreshing the page resets to the fictional sample. Download both JSON files to retain edits; no automatic persistence is provided.

## Working with equipment

Go to **Inventory** and click **Add equipment**, or import a CSV. Required columns: `id,name,quantity` and optional `category`. Semicolon-separated European CSV and Excel-style quoted fields are supported.

For editing, existing event requirements follow a renamed equipment ID. Deleting a referenced item is blocked until you remove its event requirements.

## Managing events

Go to **Events & bookings** and choose **Add event**. Set an ID, title, start/end times, booking status, setup/teardown buffers and the quantity of each required equipment type.

Local date-time fields are interpreted using the **computer's current local timezone**, then saved in UTC. Teams collaborating across timezones should double-check the displayed times and exported ISO 8601 values.

Status options:
- **Confirmed:** reserves equipment.
- **Tentative:** also reserves equipment conservatively.
- **Cancelled:** does not reserve equipment.

## Reports

The **Overview** shows the number of events with insufficient stock. **Reports & exports** creates a downloadable audit HTML report or per-event packing lists that work without internet and can be printed or saved as PDFs.

The HTML packing reports provide interactive checkboxes, but their state is not stored. Tick equipment before printing, and keep the printed copy as your operational checklist.

## Test it

Install Node.js 20+ and Python 3.10+, then from the repository root:

```bash
node --test web/tests/*.test.cjs
python -m unittest discover -s tests -v
```

The web tests include a **cross-language parity test** against the Python CLI's calculated shortages on the same association example.

## Privacy and limitations

The dashboard uses no third-party JavaScript, remote APIs, analytics, external fonts or browser storage. All edits are in-memory, and saving is an explicit file download. Avoid loading personal data if the device is shared.

StageLedger is not a production asset-management ERP: it cannot verify damage, serial numbers, transport, staffing, or whether equipment is physically present. The provided demo schedule is fictional and does **not** demonstrate external users or adoption.

Please submit reproducible issues on GitHub and keep real customer details out of public reports.
