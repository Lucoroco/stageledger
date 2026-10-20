"""Event CSV continuation-row regression tests for issue #7."""
import csv
from pathlib import Path
import tempfile
import unittest

from stageledger.cli import main
from stageledger.core import InputError, build_plan, load_events, load_inventory


HEADERS = [
    "id", "title", "start", "end", "status", "setup_minutes",
    "teardown_minutes", "item_id", "quantity",
]
FIRST = [
    "gala", "Community gala", "2026-11-21T18:00:00Z",
    "2026-11-21T23:00:00Z", "tentative", "90", "45", "speaker", "2",
]
CONTINUATION = ["gala", "", "", "", "", "", "", "microphone", "1"]


class CSVContinuationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        folder = Path(temp.name)
        self.inventory_file = folder / "inventory.csv"
        self.events_file = folder / "events.csv"
        self.report_file = folder / "packing.html"
        self.inventory_file.write_text(
            "id,name,quantity\nspeaker,PA speaker,2\nmicrophone,Handheld,3\n",
            encoding="utf-8",
        )

    def write_rows(self, rows, headers=HEADERS):
        with self.events_file.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)

    def plans(self):
        inventory = load_inventory(self.inventory_file)
        events = load_events(self.events_file, inventory)
        return inventory, events

    def test_blank_continuation_metadata_is_inherited(self):
        self.write_rows([FIRST, CONTINUATION])
        inventory, events = self.plans()
        self.assertEqual(len(events), 1)
        plan = build_plan("gala", inventory, events)
        self.assertEqual(plan["status"], "tentative")
        self.assertEqual(plan["setup_minutes"], 90)
        self.assertEqual(plan["teardown_minutes"], 45)
        self.assertEqual(
            sorted(item["id"] for item in plan["items"]), ["microphone", "speaker"]
        )

    def test_fully_repeated_original_format_still_supported(self):
        self.write_rows([FIRST, FIRST[:7] + ["microphone", "1"]])
        inventory, events = self.plans()
        self.assertEqual(len(build_plan("gala", inventory, events)["items"]), 2)

    def test_explicit_consistent_partial_metadata_allowed(self):
        row = CONTINUATION.copy()
        row[1] = "Community gala"
        row[4] = "tentative"
        row[5] = "090"  # Equivalent integer value
        self.write_rows([FIRST, row])
        self.assertEqual(len(self.plans()[1]), 1)

    def test_explicit_conflicting_title_rejected(self):
        row = CONTINUATION.copy()
        row[1] = "Different title"
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "line 3: inconsistent title"):
            self.plans()

    def test_explicit_conflicting_start_rejected(self):
        row = CONTINUATION.copy()
        row[2] = "2026-11-21T17:00:00Z"
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "inconsistent start"):
            self.plans()

    def test_explicit_conflicting_end_rejected(self):
        row = CONTINUATION.copy()
        row[3] = "2026-11-22T00:00:00Z"
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "inconsistent end"):
            self.plans()

    def test_explicit_conflicting_status_rejected(self):
        row = CONTINUATION.copy()
        row[4] = "confirmed"
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "inconsistent status"):
            self.plans()

    def test_explicit_conflicting_setup_rejected(self):
        row = CONTINUATION.copy()
        row[5] = "89"
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "inconsistent setup_minutes"):
            self.plans()

    def test_explicit_conflicting_teardown_rejected(self):
        row = CONTINUATION.copy()
        row[6] = "46"
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "inconsistent teardown_minutes"):
            self.plans()

    def test_malformed_explicit_minutes_rejected(self):
        row = CONTINUATION.copy()
        row[5] = "invalid"
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "setup_minutes must be"):
            self.plans()

    def test_first_row_cannot_omit_title(self):
        first = FIRST.copy()
        first[1] = ""
        self.write_rows([first, CONTINUATION])
        with self.assertRaisesRegex(InputError, "first row.*requires title"):
            self.plans()

    def test_first_row_cannot_omit_start(self):
        first = FIRST.copy()
        first[2] = ""
        self.write_rows([first, CONTINUATION])
        with self.assertRaisesRegex(InputError, "first row.*requires start"):
            self.plans()

    def test_first_row_cannot_omit_end(self):
        first = FIRST.copy()
        first[3] = ""
        self.write_rows([first, CONTINUATION])
        with self.assertRaisesRegex(InputError, "first row.*requires end"):
            self.plans()

    def test_different_event_does_not_inherit(self):
        row = ["second", "", "", "", "", "", "", "microphone", "1"]
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "first row for event 'second'"):
            self.plans()

    def test_interleaved_event_rows_inherit_by_id(self):
        second = [
            "meeting", "Student talk", "2026-11-22T10:00:00Z",
            "2026-11-22T11:00:00Z", "", "", "", "speaker", "1",
        ]
        self.write_rows([FIRST, second, CONTINUATION])
        inventory, events = self.plans()
        self.assertEqual(len(events), 2)
        self.assertEqual(len(build_plan("gala", inventory, events)["items"]), 2)

    def test_missing_event_id_still_rejected(self):
        row = CONTINUATION.copy()
        row[0] = ""
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "line 3: missing id"):
            self.plans()

    def test_duplicate_equipment_still_rejected(self):
        row = CONTINUATION.copy()
        row[7] = "speaker"
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "duplicate item"):
            self.plans()

    def test_missing_quantity_still_rejected(self):
        row = CONTINUATION.copy()
        row[8] = ""
        self.write_rows([FIRST, row])
        with self.assertRaisesRegex(InputError, "invalid item_id/quantity"):
            self.plans()

    def test_optional_columns_missing_and_defaulted(self):
        headers = ["id", "title", "start", "end", "item_id", "quantity"]
        self.write_rows([
            [FIRST[0], FIRST[1], FIRST[2], FIRST[3], "speaker", "2"],
            ["gala", "", "", "", "microphone", "1"],
        ], headers)
        inventory, events = self.plans()
        plan = build_plan("gala", inventory, events)
        self.assertEqual(plan["status"], "confirmed")
        self.assertEqual(plan["setup_minutes"], 0)
        self.assertEqual(plan["teardown_minutes"], 0)

    def test_blank_line_skipped(self):
        self.write_rows([FIRST, [""] * len(HEADERS), CONTINUATION])
        self.assertEqual(len(self.plans()[1][0]["requirements"]), 2)

    def test_empty_requirements_row_is_supported(self):
        row = FIRST[:7] + ["", ""]
        self.write_rows([row])
        inventory, events = self.plans()
        self.assertEqual(build_plan("gala", inventory, events)["items"], [])

    def test_existing_defaults_can_be_explicitly_repeated(self):
        first = FIRST.copy()
        first[4] = ""
        first[5] = ""
        first[6] = ""
        row = CONTINUATION.copy()
        row[4] = "confirmed"
        row[5] = "0"
        row[6] = "00"
        self.write_rows([first, row])
        self.assertEqual(len(self.plans()[1]), 1)

    def test_cli_with_continuation_creates_printable_report(self):
        self.write_rows([FIRST, CONTINUATION])
        exit_code = main([
            "plan", "--inventory", str(self.inventory_file),
            "--events", str(self.events_file), "--event", "gala",
            "--format", "html", "--output", str(self.report_file),
        ])
        self.assertEqual(exit_code, 0)
        output = self.report_file.read_text(encoding="utf-8")
        self.assertIn("Community gala", output)
        self.assertIn("Handheld", output)
        self.assertIn("PA speaker", output)


if __name__ == "__main__":
    unittest.main()
