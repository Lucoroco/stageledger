/* StageLedger browser engine: intentionally framework-free and offline. */
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.StageLedgerEngine = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function fail(message) { throw new Error(message); }
  function text(value, label) {
    if (typeof value !== "string" || !value.trim()) fail(label + " must be a non-empty string");
    return value.trim();
  }
  function integer(value, label, allowZero) {
    if (typeof value !== "number" || !Number.isSafeInteger(value) || value < (allowZero ? 0 : 1))
      fail(label + " must be an integer >= " + (allowZero ? 0 : 1));
    return value;
  }
  function instant(value, label) {
    if (typeof value !== "string" || !/T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})$/i.test(value))
      fail(label + " must contain an ISO 8601 timestamp with a timezone");
    var ms = Date.parse(value);
    if (!Number.isFinite(ms)) fail(label + " is not a valid timestamp");
    return ms;
  }
  function inventory(data) {
    if (!data || !Array.isArray(data.items)) fail("Inventory must contain an items array");
    var seen = new Set();
    return { items: data.items.map(function (entry, index) {
      var p = "items[" + index + "]";
      if (!entry || Array.isArray(entry) || typeof entry !== "object") fail(p + " must be an object");
      var id = text(entry.id, p + ".id");
      if (seen.has(id)) fail("Duplicate inventory ID: " + id);
      seen.add(id);
      return {id: id, name: text(entry.name, p + ".name"),
        quantity: integer(entry.quantity, p + ".quantity", true),
        category: typeof entry.category === "string" ? entry.category.trim() : ""};
    })};
  }
  function events(data, stock) {
    if (!data || !Array.isArray(data.events)) fail("Events must contain an events array");
    var names = new Set(stock.items.map(function (x) { return x.id; }));
    var ids = new Set();
    return { events: data.events.map(function (entry, index) {
      var p = "events[" + index + "]";
      if (!entry || Array.isArray(entry) || typeof entry !== "object") fail(p + " must be an object");
      var id = text(entry.id, p + ".id");
      if (ids.has(id)) fail("Duplicate event ID: " + id);
      ids.add(id);
      var start = instant(entry.start, p + ".start");
      var end = instant(entry.end, p + ".end");
      if (start >= end) fail(p + ".end must be after start");
      var setup = integer(entry.setup_minutes === undefined ? 0 : entry.setup_minutes, p + ".setup_minutes", true);
      var teardown = integer(entry.teardown_minutes === undefined ? 0 : entry.teardown_minutes, p + ".teardown_minutes", true);
      if (setup > 43200 || teardown > 43200) fail(p + " buffer cannot exceed 43200 minutes");
      var status = entry.status === undefined ? "confirmed" : entry.status;
      if (!["confirmed", "tentative", "cancelled"].includes(status)) fail(p + ".status is invalid");
      if (!Array.isArray(entry.requirements)) fail(p + ".requirements must be an array");
      var used = new Set();
      var requirements = entry.requirements.map(function (line, j) {
        var q = p + ".requirements[" + j + "]";
        if (!line || typeof line !== "object") fail(q + " must be an object");
        var itemId = text(line.item_id, q + ".item_id");
        if (!names.has(itemId)) fail(q + " references unknown item " + itemId);
        if (used.has(itemId)) fail(q + " duplicates item " + itemId);
        used.add(itemId);
        return {item_id: itemId, quantity: integer(line.quantity, q + ".quantity", false)};
      });
      return {id: id, title: text(entry.title, p + ".title"),
        start: new Date(start).toISOString(), end: new Date(end).toISOString(),
        status: status, setup_minutes: setup, teardown_minutes: teardown,
        requirements: requirements};
    })};
  }
  function validated(stock, schedule) {
    var inv = inventory(stock);
    return {inventory: inv, events: events(schedule, inv)};
  }
  function interval(event) {
    return {start: Date.parse(event.start) - event.setup_minutes * 60000,
      end: Date.parse(event.end) + event.teardown_minutes * 60000};
  }
  function maxCompeting(event, schedule, itemId) {
    var target = interval(event), points = [], overlaps = [];
    schedule.events.forEach(function (other) {
      if (other.id === event.id || other.status === "cancelled") return;
      var requirement = other.requirements.find(function (r) { return r.item_id === itemId; });
      if (!requirement) return;
      var window = interval(other), lo = Math.max(window.start, target.start);
      var hi = Math.min(window.end, target.end);
      if (lo >= hi) return;
      overlaps.push(other.id);
      points.push({t:lo, n:requirement.quantity}, {t:hi, n:-requirement.quantity});
    });
    points.sort(function(a,b) { return a.t - b.t || a.n - b.n; });
    var running = 0, peak = 0;
    points.forEach(function (x) { running += x.n; peak = Math.max(peak,running); });
    overlaps.sort();
    return {peak:peak, overlaps:overlaps};
  }
  function plan(id, stock, schedule) {
    var checked = validated(stock, schedule);
    var event = checked.events.events.find(function(x) { return x.id === id; });
    if (!event) fail("Unknown event ID: " + id);
    if (event.status === "cancelled") fail("Cancelled event does not reserve equipment: " + id);
    var itemMap = new Map(checked.inventory.items.map(function(x) { return [x.id,x]; }));
    var lines = event.requirements.map(function (req) {
      var item = itemMap.get(req.item_id);
      var c = maxCompeting(event, checked.events,req.item_id);
      var available = Math.max(0, item.quantity - c.peak);
      return {id:item.id, name:item.name, category:item.category,
        requested:req.quantity, owned:item.quantity, other_bookings_peak:c.peak,
        available:available, shortage:Math.max(0,req.quantity-available),
        overlapping_events:c.overlaps};
    });
    lines.sort(function(a,b) { return a.id.localeCompare(b.id); });
    var window = interval(event);
    return {event:event.id,title:event.title,start:event.start,end:event.end,
      booking_start:new Date(window.start).toISOString(),
      booking_end:new Date(window.end).toISOString(),
      setup_minutes:event.setup_minutes,teardown_minutes:event.teardown_minutes,
      status:event.status,ready:lines.every(function(x) {return x.shortage === 0;}),
      items:lines};
  }
  function audit(stock, schedule) {
    var checked = validated(stock,schedule);
    return checked.events.events.filter(function(x) { return x.status !== "cancelled"; })
      .sort(function(a,b) { return Date.parse(a.start)-Date.parse(b.start) || a.id.localeCompare(b.id); })
      .map(function(x) {return plan(x.id, checked.inventory, checked.events);});
  }
  function csvRows(input) {
    if (typeof input !== "string") fail("CSV must be text");
    input = input.replace(/^\uFEFF/, "");
    var header = input.split(/\r?\n/,1)[0] || "";
    var delimiter = (header.match(/;/g) || []).length > (header.match(/,/g) || []).length ? ";" : ",";
    var result = [], row = [], field = "", quoted = false;
    for (var i=0; i<input.length; i++) {
      var c=input[i];
      if (c === '"') {
        if (quoted && input[i+1] === '"') {field += '"';i++;}
        else if (quoted) quoted=false;
        else if (field==="") quoted=true;
        else fail("Unexpected quote in CSV");
      } else if (c === delimiter && !quoted) {row.push(field);field="";}
      else if ((c === "\n" || c === "\r") && !quoted) {
        if (c === "\r" && input[i+1] === "\n") i++;
        row.push(field); result.push(row); row=[];field="";
      } else field += c;
    }
    if (quoted) fail("Unclosed quoted CSV field");
    if (field !== "" || row.length) {row.push(field);result.push(row);}
    return result;
  }
  function csvInventory(input) {
    var rows = csvRows(input);
    if (!rows.length) fail("Inventory CSV is empty");
    var header = rows.shift().map(function(x) { return x.trim(); });
    if (new Set(header).size !== header.length) fail("Duplicate CSV column header");
    ["id","name","quantity"].forEach(function(k) {
      if (!header.includes(k)) fail("Missing CSV column: " + k);
    });
    var items=[];
    rows.forEach(function(row, i) {
      if (row.length === 1 && row[0].trim() === "") return;
      if (row.length !== header.length) fail("CSV line " + (i+2) + " has an incorrect number of columns");
      var object={}; header.forEach(function(k,j) {object[k]=row[j].trim();});
      if (!/^[0-9]+$/.test(object.quantity)) fail("CSV line " + (i+2) + " quantity must be a non-negative integer");
      items.push({id:object.id,name:object.name,quantity:Number(object.quantity),category:object.category || ""});
    });
    return inventory({items:items});
  }
  function csvQuote(value) {
    var content = String(value);
    if (/^[\s]*[=+\-@]/.test(content) || /^[\t\r\n]/.test(content)) content = "'" + content;
    return '"' + content.replace(/"/g,'""') + '"';
  }
  function exportInventoryCsv(stock) {
    var checked = inventory(stock);
    return "id,name,quantity,category\r\n" + checked.items.map(function(x) {
      return [x.id,x.name,x.quantity,x.category].map(csvQuote).join(",");
    }).join("\r\n") + "\r\n";
  }
  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  return {inventory:inventory,events:events,validated:validated,interval:interval,
    plan:plan,audit:audit,csvInventory:csvInventory,exportInventoryCsv:exportInventoryCsv,clone:clone};
});
