# Windows PowerShell quick start

Install Python 3.10 or newer from the official Python website. Check with `py --version`.

Clone or download the StageLedger repository, then open PowerShell in its root folder.

```powershell
py -m stageledger plan --inventory examples/inventory.json --events examples/events.json --event community-concert
```

The example deliberately includes overlapping bookings; the reported equipment shortage is expected and exits with code `2`.

Save a Markdown packing list:

```powershell
py -m stageledger plan --inventory examples/inventory.json --events examples/events.json --event community-concert --output packing.md
```

Run tests:

```powershell
py -m unittest discover -s tests -v
```

Python 3.10+ is required. No runtime packages need installing for `py -m stageledger` from the repository root.
