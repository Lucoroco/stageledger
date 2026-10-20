"""Command-line interface for StageLedger."""
import argparse
import csv
import io
import json
import sys

from stageledger.core import InputError, audit, build_plan, load_events, load_inventory


def as_markdown(plan):
    status = "READY" if plan["ready"] else "SHORTAGES FOUND"
    lines = [
        f"# Packing list: {plan['title']}", "",
        f"- Event ID: `{plan['event']}`",
        f"- Start: {plan['start']}", f"- End: {plan['end']}",
        f"- Status: **{status}**", "",
        "| Packed | Equipment | Needed | Available | Missing |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for item in plan["items"]:
        name = item["name"].replace("|", r"\|").replace("\n", " ")
        lines.append(
            f"| [ ] | {name} | {item['requested']} | "
            f"{item['available']} | {item['shortage']} |"
        )
    if not plan["items"]:
        lines += ["", "No equipment required for this event."]
    lines += ["", "_Availability accounts for peak overlapping event bookings._", ""]
    return "\n".join(lines)


def as_csv(plan):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["event_id", "item_id", "name", "requested", "available", "shortage"])
    for item in plan["items"]:
        writer.writerow([
            plan["event"], item["id"], item["name"], item["requested"],
            item["available"], item["shortage"],
        ])
    return buffer.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Event equipment planning and booking audit")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("plan", "audit"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--inventory", required=True, help="Path to inventory JSON")
        cmd.add_argument("--events", required=True, help="Path to events JSON")
        cmd.add_argument("--output", help="Write output to a file instead of stdout")
        cmd.add_argument(
            "--format", choices=["markdown", "json", "csv"] if command == "plan"
            else ["json", "markdown"], default="markdown" if command == "plan" else "json"
        )
        if command == "plan":
            cmd.add_argument("--event", required=True, help="ID of the event to plan")
    args = parser.parse_args(argv)
    try:
        inventory = load_inventory(args.inventory)
        events = load_events(args.events, inventory)
        if args.command == "plan":
            plan = build_plan(args.event, inventory, events)
            output = {
                "markdown": lambda: as_markdown(plan),
                "json": lambda: json.dumps(plan, indent=2) + "\n",
                "csv": lambda: as_csv(plan),
            }[args.format]()
            failed = not plan["ready"]
        else:
            plans = audit(inventory, events)
            output = (
                json.dumps(plans, indent=2) + "\n"
                if args.format == "json"
                else "\n".join(as_markdown(p) for p in plans)
            )
            failed = any(not plan["ready"] for plan in plans)
        if args.output:
            from pathlib import Path
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 2 if failed else 0
    except (InputError, OSError) as exc:
        print(f"stageledger: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
