# Windows PowerShell quick start

## 1. Prepare

1. Install Python **3.10 or newer** from the official Python website.
2. Check with `py --version`.
3. Download this repository as a ZIP and extract it, or clone it.
4. In File Explorer open the project folder, click the address bar, enter `powershell` and press Enter.

## 2. Generate an HTML packing list

```powershell
py -m stageledger plan --inventory examples/inventory.csv --events examples/events.json --event community-concert --format html --output packing.html
```

Open `packing.html` in your browser. Click **Print / Save PDF** for an offline document.

The included sample intentionally has overlapping bookings. Exit code `2` signals shortages and **does not** mean Python crashed.

## 3. Audit an association schedule

```powershell
py -m stageledger audit --inventory examples/association_inventory.json --events examples/association_events.json --format html --output audit.html
```

Open `audit.html` in the same folder.

## 4. Use your own inventory

Export a spreadsheet as CSV (UTF-8 preferred). Required columns are `id,name,quantity`; `category` is optional. See [operations guide](OPERATIONS_GUIDE.md) for event JSON structure, booking status, setup/teardown buffers and limitations.

## 5. Verify the software

```powershell
py -m unittest discover -s tests -v
```

If PowerShell cannot find `py`, verify your Python installation or try `python` instead. No third-party runtime packages are required for the `py -m stageledger` workflow.
