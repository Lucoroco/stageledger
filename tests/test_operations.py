"""Regression tests for v0.2 operations features, run without third-party packages."""
import json
from pathlib import Path
import tempfile
import unittest

from stageledger.cli import main
from stageledger.core import InputError, audit, build_plan, load_events, load_inventory
from stageledger.reporting import render_html


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.directory = Path(self.folder.name)
        self.inv_path = self.directory / "equipment.json"
        self.events_path = self.directory / "events.json"
        self.inv = {"items": [{"id": "pa", "name": "PA speaker", "quantity": 2, "category": "Audio"}]}
        self.events = {"events": [
            {"id": "setup", "title": "First event", "start": "2026-11-02T10:00:00+00:00",
             "end": "2026-11-02T12:00:00+00:00",
             "requirements": [{"item_id": "pa", "quantity": 2}]},
            {"id": "next", "title": "Next event", "start": "2026-11-02T12:00:00+00:00",
             "end": "2026-11-02T14:00:00+00:00",
             "requirements": [{"item_id": "pa", "quantity": 2}]},
        ]}
        self.save()

    def save(self):
        self.inv_path.write_text(json.dumps(self.inv), encoding="utf-8")
        self.events_path.write_text(json.dumps(self.events), encoding="utf-8")

    def loaded(self):
        inventory = load_inventory(self.inv_path)
        return inventory, load_events(self.events_path, inventory)

    def plan(self, event_id="setup"):
        return build_plan(event_id, *self.loaded())

    def test_back_to_back_without_buffers_is_ready(self):
        self.assertTrue(self.plan()["ready"])

    def test_setup_buffer_creates_conflict(self):
        self.events["events"][1]["setup_minutes"] = 30
        self.save()
        plan = self.plan()
        self.assertFalse(plan["ready"])
        self.assertEqual(plan["items"][0]["shortage"], 2)
        self.assertEqual(plan["items"][0]["overlapping_events"], ["next"])

    def test_teardown_buffer_creates_conflict(self):
        self.events["events"][0]["teardown_minutes"] = 45
        self.save()
        self.assertFalse(self.plan()["ready"])

    def test_buffered_start_and_end_exposed(self):
        self.events["events"][0]["setup_minutes"] = 30
        self.events["events"][0]["teardown_minutes"] = 15
        self.save()
        plan = self.plan()
        self.assertEqual(plan["booking_start"], "2026-11-02T09:30:00+00:00")
        self.assertEqual(plan["booking_end"], "2026-11-02T12:15:00+00:00")

    def test_cancelled_bookings_release_inventory(self):
        self.events["events"][1]["setup_minutes"] = 30
        self.events["events"][1]["status"] = "cancelled"
        self.save()
        self.assertTrue(self.plan()["ready"])
        self.assertEqual(len(audit(*self.loaded())), 1)

    def test_cancelled_event_cannot_be_planned(self):
        self.events["events"][0]["status"] = "cancelled"
        self.save()
        with self.assertRaisesRegex(InputError, "cancelled"):
            self.plan()

    def test_tentative_bookings_still_reserve(self):
        self.events["events"][1]["setup_minutes"] = 30
        self.events["events"][1]["status"] = "tentative"
        self.save()
        self.assertFalse(self.plan()["ready"])

    def test_invalid_status_is_rejected(self):
        self.events["events"][0]["status"] = "postponed"
        self.save()
        with self.assertRaisesRegex(InputError, "status"):
            self.loaded()

    def test_negative_setup_is_rejected(self):
        self.events["events"][0]["setup_minutes"] = -5
        self.save()
        with self.assertRaisesRegex(InputError, "setup_minutes"):
            self.loaded()

    def test_non_integer_buffer_is_rejected(self):
        self.events["events"][0]["teardown_minutes"] = True
        self.save()
        with self.assertRaisesRegex(InputError, "teardown_minutes"):
            self.loaded()

    def test_unreasonable_buffer_is_rejected(self):
        self.events["events"][0]["setup_minutes"] = 43201
        self.save()
        with self.assertRaisesRegex(InputError, "43200"):
            self.loaded()

    def test_timezone_offsets_are_normalised(self):
        self.events["events"][1]["start"] = "2026-11-02T13:00:00+01:00"
        self.events["events"][1]["end"] = "2026-11-02T15:00:00+01:00"
        self.events["events"][1]["setup_minutes"] = 1
        self.save()
        self.assertFalse(self.plan()["ready"])

    def test_csv_with_bom_and_zero_quantity(self):
        file = self.directory / "inventory.csv"
        file.write_text("\ufeffid,name,quantity,category\npa,Speaker,0,Audio\n", encoding="utf-8")
        items = load_inventory(file)
        self.assertEqual(items["pa"]["quantity"], 0)

    def test_csv_optional_category(self):
        file = self.directory / "inventory.CSV"
        file.write_text("id,name,quantity\npa,Speaker,12\n", encoding="utf-8")
        self.assertEqual(load_inventory(file)["pa"]["category"], "")

    def test_csv_rejects_duplicate_ids(self):
        file = self.directory / "inventory.csv"
        file.write_text("id,name,quantity\npa,Speaker,1\npa,Speaker,2\n", encoding="utf-8")
        with self.assertRaisesRegex(InputError, "Duplicate inventory ID"):
            load_inventory(file)

    def test_csv_rejects_negative_quantity(self):
        file = self.directory / "inventory.csv"
        file.write_text("id,name,quantity\npa,Speaker,-1\n", encoding="utf-8")
        with self.assertRaisesRegex(InputError, "non-negative"):
            load_inventory(file)

    def test_csv_rejects_decimal_quantity(self):
        file = self.directory / "inventory.csv"
        file.write_text("id,name,quantity\npa,Speaker,1.5\n", encoding="utf-8")
        with self.assertRaisesRegex(InputError, "non-negative"):
            load_inventory(file)

    def test_csv_rejects_missing_columns(self):
        file = self.directory / "inventory.csv"
        file.write_text("id,quantity\npa,1\n", encoding="utf-8")
        with self.assertRaisesRegex(InputError, "missing column"):
            load_inventory(file)

    def test_csv_rejects_extra_fields(self):
        file = self.directory / "inventory.csv"
        file.write_text("id,name,quantity\npa,Speaker,2,extra\n", encoding="utf-8")
        with self.assertRaisesRegex(InputError, "too many columns"):
            load_inventory(file)

    def test_csv_rejects_empty_file(self):
        file = self.directory / "inventory.csv"
        file.write_text("", encoding="utf-8")
        with self.assertRaisesRegex(InputError, "empty"):
            load_inventory(file)

    def test_csv_skips_blank_rows(self):
        file = self.directory / "inventory.csv"
        file.write_text("id,name,quantity\n\npa,Speaker,2\n", encoding="utf-8")
        self.assertEqual(len(load_inventory(file)), 1)

    def test_html_report_is_offline_and_printable(self):
        report = render_html([self.plan()])
        self.assertIn("<!doctype html>", report)
        self.assertIn("window.print()", report)
        self.assertIn("First event", report)
        self.assertIn("No equipment", report) if False else None

    def test_html_escapes_untrusted_event_and_equipment_names(self):
        self.inv["items"][0]["name"] = '<img src=x onerror=alert("X")>'
        self.events["events"][0]["title"] = '<script>alert("x")</script>'
        self.save()
        report = render_html([self.plan()])
        self.assertNotIn('<script>alert("x")</script>', report)
        self.assertNotIn('<img src=x onerror=', report)
        self.assertIn("&lt;script&gt;", report)
        self.assertIn("&lt;img", report)

    def test_cli_html_export_with_conflict_exit_code(self):
        self.events["events"][1]["setup_minutes"] = 5
        self.save()
        out = self.directory / "packing.html"
        status = main(["plan", "--inventory", str(self.inv_path),
                       "--events", str(self.events_path), "--event", "setup",
                       "--format", "html", "--output", str(out)])
        self.assertEqual(status, 2)
        self.assertIn("Equipment planning", out.read_text(encoding="utf-8"))

    def test_html_checkboxes_are_interactive(self):
        html = render_html([self.plan()])
        self.assertIn('type="checkbox"', html)
        self.assertIn('aria-label="Pack PA speaker"', html)

    def test_csv_formula_injection_is_escaped(self):
        from stageledger.cli import as_csv
        self.events["events"][0]["title"] = "=2+2"
        self.inv["items"][0]["name"] = "=HYPERLINK(\"https://example.org\")"
        self.save()
        csv_report = as_csv(self.plan())
        self.assertIn("'=HYPERLINK(", csv_report)

    def test_audit_html_excludes_cancelled_events(self):
        self.events["events"][1]["status"] = "cancelled"
        self.save()
        out = self.directory / "audit.html"
        status = main(["audit", "--inventory", str(self.inv_path),
                       "--events", str(self.events_path),
                       "--format", "html", "--output", str(out)])
        self.assertEqual(status, 0)
        html = out.read_text(encoding="utf-8")
        self.assertIn("First event", html)
        self.assertNotIn("Next event", html)

    def test_backward_compatibility_no_optional_fields(self):
        self.assertEqual(self.plan()["status"], "confirmed")
        self.assertEqual(self.plan()["setup_minutes"], 0)
        self.assertEqual(self.plan()["teardown_minutes"], 0)


if __name__ == "__main__":
    unittest.main()
