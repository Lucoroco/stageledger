import json
import tempfile
import unittest
from pathlib import Path

from stageledger.core import InputError, audit, build_plan, load_events, load_inventory
from stageledger.cli import as_csv, as_markdown, main


class StageLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.inventory_path = Path(self.tmp.name) / "inventory.json"
        self.events_path = Path(self.tmp.name) / "events.json"
        self.inventory = {
            "items": [{"id": "a", "name": "Speaker", "quantity": 3}]
        }
        self.events = {"events": [
            {"id": "A", "title": "Main", "start": "2026-01-01T10:00:00Z",
             "end": "2026-01-01T14:00:00Z",
             "requirements": [{"item_id": "a", "quantity": 2}]},
            {"id": "B", "title": "Side", "start": "2026-01-01T12:00:00Z",
             "end": "2026-01-01T13:00:00Z",
             "requirements": [{"item_id": "a", "quantity": 2}]},
        ]}
        self.save()

    def save(self):
        self.inventory_path.write_text(json.dumps(self.inventory))
        self.events_path.write_text(json.dumps(self.events))

    def data(self):
        inventory = load_inventory(self.inventory_path)
        return inventory, load_events(self.events_path, inventory)

    def test_overlapping_bookings_flag_shortage(self):
        inv, events = self.data()
        plan = build_plan("A", inv, events)
        self.assertFalse(plan["ready"])
        self.assertEqual(plan["items"][0]["shortage"], 1)
        self.assertEqual(plan["items"][0]["other_bookings_peak"], 2)

    def test_back_to_back_no_conflict(self):
        self.events["events"][1]["start"] = "2026-01-01T14:00:00Z"
        self.events["events"][1]["end"] = "2026-01-01T15:00:00Z"
        self.save()
        inv, events = self.data()
        self.assertTrue(build_plan("A", inv, events)["ready"])

    def test_peak_does_not_sum_nonoverlapping_others(self):
        self.events["events"].append({
            "id": "C", "title": "Late", "start": "2026-01-01T13:00:00Z",
            "end": "2026-01-01T14:00:00Z",
            "requirements": [{"item_id": "a", "quantity": 2}],
        })
        self.save()
        inv, events = self.data()
        self.assertEqual(build_plan("A", inv, events)["items"][0]["other_bookings_peak"], 2)

    def test_reject_unknown_item(self):
        self.events["events"][0]["requirements"][0]["item_id"] = "missing"
        self.save()
        inv = load_inventory(self.inventory_path)
        with self.assertRaisesRegex(InputError, "unknown inventory item"):
            load_events(self.events_path, inv)

    def test_reject_duplicate_inventory_ids(self):
        self.inventory["items"].append(self.inventory["items"][0].copy())
        self.save()
        with self.assertRaisesRegex(InputError, "Duplicate"):
            load_inventory(self.inventory_path)

    def test_reject_boolean_quantity(self):
        self.inventory["items"][0]["quantity"] = True
        self.save()
        with self.assertRaisesRegex(InputError, "integer"):
            load_inventory(self.inventory_path)

    def test_reject_missing_timezone(self):
        self.events["events"][0]["start"] = "2026-01-01T10:00:00"
        self.save()
        inv = load_inventory(self.inventory_path)
        with self.assertRaisesRegex(InputError, "timezone"):
            load_events(self.events_path, inv)

    def test_reject_duplicate_requirements(self):
        self.events["events"][0]["requirements"] *= 2
        self.save()
        inv = load_inventory(self.inventory_path)
        with self.assertRaisesRegex(InputError, "duplicate"):
            load_events(self.events_path, inv)

    def test_report_formats(self):
        inv, events = self.data()
        plan = build_plan("A", inv, events)
        self.assertIn("| [ ] | Speaker", as_markdown(plan))
        self.assertIn("event_id,item_id", as_csv(plan))

    def test_cli_exit_codes(self):
        common = ["--inventory", str(self.inventory_path),
                  "--events", str(self.events_path)]
        path = Path(self.tmp.name) / "packing.md"
        result = main(["plan", *common, "--event", "A", "--output", str(path)])
        self.assertEqual(result, 2)
        self.assertIn("SHORTAGES", path.read_text())
        self.assertEqual(main(["plan", *common, "--event", "unknown"]), 1)

    def test_audit_all_events(self):
        inv, events = self.data()
        self.assertEqual(len(audit(inv, events)), 2)


if __name__ == "__main__":
    unittest.main()
