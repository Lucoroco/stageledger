import tempfile
import unittest
from pathlib import Path

from stageledger.core import InputError, load_events, load_inventory, build_plan
from stageledger.cli import main


HEADER = "id,title,start,end,status,setup_minutes,teardown_minutes,item_id,quantity\n"
ROWS = (
    "gala,Charity Gala,2026-11-21T18:00:00Z,2026-11-21T23:00:00Z,confirmed,60,45,speaker,2\n"
    "gala,Charity Gala,2026-11-21T18:00:00Z,2026-11-21T23:00:00Z,confirmed,60,45,mic,1\n"
    "meeting,Student Meeting,2026-11-21T20:00:00Z,2026-11-21T21:00:00Z,tentative,0,0,speaker,2\n"
)


class EventCSVTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.inventory = self.dir / "inventory.csv"
        self.inventory.write_text("id,name,quantity\nspeaker,PA Speaker,3\nmic,Microphone,4\n")
        self.events = self.dir / "events.csv"
        self.events.write_text(HEADER + ROWS)

    def load(self):
        stock = load_inventory(self.inventory)
        return stock, load_events(self.events, stock)

    def test_grouped_event_rows(self):
        stock, events = self.load()
        self.assertEqual(len(events), 2)
        plan = build_plan("gala", stock, events)
        self.assertEqual(len(plan["items"]), 2)
        self.assertEqual(plan["items"][0]["id"], "mic")
        self.assertEqual(plan["booking_start"], "2026-11-21T17:00:00+00:00")
        self.assertEqual(next(i for i in plan["items"] if i["id"] == "speaker")["shortage"], 1)

    def test_empty_equipment_event(self):
        self.events.write_text(HEADER + "e,No Kit,2026-11-21T10:00:00Z,2026-11-21T11:00:00Z,,,,,\n")
        stock, events = self.load()
        self.assertEqual(build_plan("e", stock, events)["items"], [])

    def test_conflicting_metadata(self):
        self.events.write_text(HEADER + ROWS.replace("gala,Charity Gala", "gala,Different Title", 1))
        with self.assertRaisesRegex(InputError, "inconsistent title"):
            self.load()

    def test_bad_quantity(self):
        self.events.write_text(HEADER + ROWS.replace("speaker,2", "speaker,-2", 1))
        with self.assertRaisesRegex(InputError, "invalid item_id/quantity"):
            self.load()

    def test_duplicate_equipment(self):
        self.events.write_text(HEADER + ROWS + ROWS.splitlines(True)[0])
        with self.assertRaisesRegex(InputError, "duplicate item"):
            self.load()

    def test_missing_header(self):
        self.events.write_text("id,title\nfoo,bar\n")
        with self.assertRaisesRegex(InputError, "missing columns"):
            self.load()

    def test_extra_column(self):
        self.events.write_text(HEADER + ROWS.splitlines(True)[0].rstrip() + ",extra\n")
        with self.assertRaisesRegex(InputError, "too many columns"):
            self.load()

    def test_bom(self):
        self.events.write_text("\ufeff" + HEADER + ROWS, encoding="utf-8")
        self.assertEqual(len(self.load()[1]), 2)


    def test_continuation_row_inherits_booking_fields(self):
        rows = ROWS.splitlines(True)
        rows[1] = "gala,,,,,,,mic,1\\n".replace("\\\\n", "\\n")
        self.events.write_text(HEADER + "".join(rows))
        stock, events = self.load()
        gala = build_plan("gala", stock, events)
        self.assertEqual(len(gala["items"]), 2)
        self.assertEqual(gala["setup_minutes"], 60)
        self.assertEqual(gala["teardown_minutes"], 45)

    def test_continuation_row_rejects_changed_start(self):
        rows = ROWS.splitlines(True)
        rows[1] = "gala,,2026-11-21T19:00:00Z,,,,,mic,1\\n".replace("\\\\n", "\\n")
        self.events.write_text(HEADER + "".join(rows))
        with self.assertRaisesRegex(InputError, "inconsistent start"):
            self.load()

    def test_continuation_rejects_explicit_default_status(self):
        rows = ROWS.splitlines(True)
        rows[1] = "gala,,,,tentative,,,mic,1\\n".replace("\\\\n", "\\n")
        self.events.write_text(HEADER + "".join(rows))
        with self.assertRaisesRegex(InputError, "inconsistent status"):
            self.load()

    def test_continuation_rejects_explicit_different_buffer(self):
        rows = ROWS.splitlines(True)
        rows[1] = "gala,,,,,0,,mic,1\\n".replace("\\\\n", "\\n")
        self.events.write_text(HEADER + "".join(rows))
        with self.assertRaisesRegex(InputError, "inconsistent setup_minutes"):
            self.load()

    def test_first_row_must_have_booking_fields(self):
        self.events.write_text(HEADER + "gala,,,,,,,speaker,2\\n".replace("\\\\n", "\\n"))
        with self.assertRaisesRegex(InputError, "first row"):
            self.load()

    def test_interleaved_event_continuation(self):
        rows = ROWS.splitlines(True)
        self.events.write_text(HEADER + rows[0] + rows[2] +
                               "gala,,,,,,,mic,1\\n".replace("\\\\n", "\\n"))
        stock, events = self.load()
        self.assertEqual(len(build_plan("gala", stock, events)["items"]), 2)

    def test_cli_end_to_end(self):
        out = self.dir / "plan.html"
        code = main(["plan", "--inventory", str(self.inventory),
                     "--events", str(self.events), "--event", "gala",
                     "--format", "html", "--output", str(out)])
        self.assertEqual(code, 2)
        self.assertIn("Charity Gala", out.read_text())


if __name__ == "__main__":
    unittest.main()
