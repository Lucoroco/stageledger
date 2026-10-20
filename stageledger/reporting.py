"""Self-contained, printable and safely escaped HTML reporting."""
from html import escape


def _safe(value):
    return escape(str(value), quote=True)


def render_html(plans):
    """Return an offline HTML page containing one or more equipment plans."""
    total = len(plans)
    shortages = sum(not plan["ready"] for plan in plans)
    sections = []
    for plan in plans:
        rows = []
        for item in plan["items"]:
            missing = item["shortage"]
            status = '<span class="chip danger">Shortage</span>' if missing else '<span class="chip good">Available</span>'
            conflicts = ", ".join(item["overlapping_events"]) or "None"
            rows.append(
                "<tr><td><span class='tick'>□</span></td>"
                f"<td><strong>{_safe(item['name'])}</strong><small>{_safe(item['category'])} · {_safe(item['id'])}</small></td>"
                f"<td>{item['requested']}</td><td>{item['available']}</td>"
                f"<td><strong>{missing}</strong></td><td>{status}<small>Overlaps: {_safe(conflicts)}</small></td></tr>"
            )
        badge = '<span class="pill bad">Action needed</span>' if not plan["ready"] else '<span class="pill ok">Equipment available</span>'
        body = "\n".join(rows) if rows else '<tr><td colspan="6" class="empty">No equipment required</td></tr>'
        sections.append(
            '<section class="event"><div class="event-head"><div>'
            f'<div class="overline">Event · {_safe(plan["event"])}</div>'
            f'<h2>{_safe(plan["title"])}</h2></div>{badge}</div>'
            '<div class="meta">'
            f'<div><b>Event starts</b><span>{_safe(plan["start"])}</span></div>'
            f'<div><b>Event ends</b><span>{_safe(plan["end"])}</span></div>'
            f'<div><b>Equipment reserved from</b><span>{_safe(plan["booking_start"])}</span></div>'
            f'<div><b>Equipment reserved until</b><span>{_safe(plan["booking_end"])}</span></div>'
            f'<div><b>Booking status</b><span>{_safe(plan["status"])}</span></div>'
            f'<div><b>Setup / teardown</b><span>{plan["setup_minutes"]} / {plan["teardown_minutes"]} min</span></div>'
            '</div><div class="table-wrap"><table><thead><tr><th>Packed</th><th>Equipment</th>'
            '<th>Needed</th><th>Available</th><th>Missing</th><th>Availability check</th></tr>'
            f'</thead><tbody>{body}</tbody></table></div></section>'
        )
    style = """
    :root {color-scheme:light;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:#f2f5f8;color:#172535}
    * {box-sizing:border-box} body{margin:0} main{max-width:1100px;margin:auto;padding:38px 22px 70px}
    .top{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;margin-bottom:26px}
    .brand{font-size:13px;font-weight:800;letter-spacing:.18em;color:#176780;text-transform:uppercase}
    h1{font-size:clamp(30px,4vw,43px);letter-spacing:-.05em;margin:6px 0 8px}
    .sub{color:#647587;line-height:1.6;margin:0;max-width:650px}
    .actions{display:flex;gap:8px}.print{background:#12354d;color:white;border:0;border-radius:8px;padding:12px 18px;font-weight:650;cursor:pointer}
    .summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:26px 0}
    .stat{border-radius:14px;padding:20px 22px;background:white;border:1px solid #e3e8ef}
    .stat b{display:block;font-size:30px;letter-spacing:-.04em}.stat span{color:#607488;font-size:13px}
    .event{background:white;border:1px solid #dee6ed;border-radius:15px;margin:20px 0;overflow:hidden;page-break-inside:avoid}
    .event-head{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:22px 25px 4px}
    h2{font-size:23px;letter-spacing:-.035em;margin:5px 0 15px}
    .overline{color:#698294;font-size:11px;text-transform:uppercase;letter-spacing:.12em;font-weight:800}
    .pill,.chip{font-size:11px;font-weight:750;border-radius:40px;padding:7px 11px;white-space:nowrap}
    .ok,.good{background:#e1f5e8;color:#15603d}.bad,.danger{background:#ffe7e6;color:#a73332}
    .meta{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;padding:10px 25px 25px}
    .meta div{display:flex;flex-direction:column;gap:4px;min-width:0}
    .meta b{font-size:11px;text-transform:uppercase;color:#6e8091;letter-spacing:.06em}
    .meta span{font-size:12px;overflow-wrap:anywhere}
    .table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:710px}
    th{text-align:left;background:#f5f8fb;font-size:11px;color:#536a7f;text-transform:uppercase;letter-spacing:.055em;padding:13px 18px}
    td{border-top:1px solid #e8eef3;padding:15px 18px;font-size:13px;vertical-align:middle}
    td small{display:block;color:#698092;font-size:11px;margin-top:5px}
    .tick{font-size:22px;color:#718294}.empty{text-align:center;color:#728295}
    footer{color:#738395;font-size:12px;line-height:1.65;margin-top:30px}
    @media(max-width:760px){.summary{grid-template-columns:1fr}.meta{grid-template-columns:1fr 1fr}.event-head{align-items:flex-start;flex-direction:column}}
    @media print{ :root{background:white}main{max-width:none;padding:0}.actions{display:none}.event{box-shadow:none;border:1px solid #bbb}.stat{border:1px solid #bbb}th{-webkit-print-color-adjust:exact;print-color-adjust:exact} }
    """
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>StageLedger · Equipment plans</title>'
        f'<style>{style}</style></head><body><main>'
        '<header class="top"><div><div class="brand">StageLedger / Field operations</div>'
        '<h1>Equipment planning</h1>'
        '<p class="sub">Print-ready lists and booking conflict checks for community events.</p></div>'
        '<div class="actions"><button class="print" onclick="window.print()">Print / Save PDF</button></div></header>'
        f'<div class="summary"><div class="stat"><b>{total}</b><span>Active events</span></div>'
        f'<div class="stat"><b>{total-shortages}</b><span>Plans with enough equipment</span></div>'
        f'<div class="stat"><b>{shortages}</b><span>Events requiring attention</span></div></div>'
        + "\n".join(sections)
        + '<footer>Offline report generated by StageLedger. Availability is conservative: tentative bookings count, '
        'cancelled bookings do not; inventory counts are pooled by item type. '
        'Confirm real asset condition, logistics and timings before dispatch.</footer>'
        '</main></body></html>\n'
    )
