const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const api = require("../engine.js");

const inventory = {items:[
  {id:"pa",name:"Main PA",quantity:4,category:"Audio"},
  {id:"mic",name:"Microphone",quantity:5,category:"Audio"}
]};
const schedule = {events:[
  {id:"a",title:"Main event",status:"confirmed",start:"2026-11-21T18:00:00Z",end:"2026-11-21T22:00:00Z",setup_minutes:60,teardown_minutes:0,requirements:[{item_id:"pa",quantity:3}]},
  {id:"b",title:"Side event",status:"tentative",start:"2026-11-21T16:30:00Z",end:"2026-11-21T17:30:00Z",setup_minutes:0,teardown_minutes:0,requirements:[{item_id:"pa",quantity:2}]}
]};
const copy = x => JSON.parse(JSON.stringify(x));

test("validated data normalizes UTC timestamps",()=>{
  const checked=api.validated(inventory,schedule);
  assert.equal(checked.events.events[0].start,"2026-11-21T18:00:00.000Z");
});
test("buffer creates a shortage between adjacent events",()=>{
  const result=api.plan("a",inventory,schedule);
  assert.equal(result.ready,false);
  assert.equal(result.items[0].shortage,1);
  assert.deepEqual(result.items[0].overlapping_events,["b"]);
  assert.equal(result.booking_start,"2026-11-21T17:00:00.000Z");
});
test("without buffers, adjacent equipment reservations do not conflict",()=>{
  const edited=copy(schedule);edited.events[0].setup_minutes=0;
  const result=api.plan("a",inventory,edited);
  assert.equal(result.ready,true);
});
test("cancelled reservations do not reserve inventory",()=>{
  const edited=copy(schedule);edited.events[1].status="cancelled";
  assert.equal(api.plan("a",inventory,edited).ready,true);
  assert.equal(api.audit(inventory,edited).length,1);
});
test("tentative reservations count toward availability",()=>{
  assert.equal(api.plan("a",inventory,schedule).items[0].other_bookings_peak,2);
});
test("overlapping windows use peak simultaneous demand not sum of disjoint bookings",()=>{
  const edited=copy(schedule);
  edited.events[0].setup_minutes=120;
  edited.events.push({id:"c",title:"Third",start:"2026-11-21T18:00:00Z",end:"2026-11-21T19:00:00Z",requirements:[{item_id:"pa",quantity:2}]});
  const result=api.plan("a",inventory,edited);
  assert.equal(result.items[0].other_bookings_peak,2);
  assert.deepEqual(result.items[0].overlapping_events,["b","c"]);
});
test("back-to-back competing events do not double-count",()=>{
  const edited=copy(schedule);
  edited.events[1].start="2026-11-21T17:00:00Z";
  edited.events[1].end="2026-11-21T18:00:00Z";
  edited.events.push({id:"c",title:"Third",start:"2026-11-21T18:00:00Z",end:"2026-11-21T19:00:00Z",requirements:[{item_id:"pa",quantity:2}]});
  assert.equal(api.plan("a",inventory,edited).items[0].other_bookings_peak,2);
});
test("unknown inventory references are rejected",()=>{
  const edited=copy(schedule);edited.events[1].requirements[0].item_id="unknown";
  assert.throws(()=>api.audit(inventory,edited),/unknown item/);
});
test("duplicate inventory IDs are rejected",()=>{
  const edited=copy(inventory);edited.items.push(copy(edited.items[0]));
  assert.throws(()=>api.inventory(edited),/Duplicate inventory/);
});
test("duplicate event IDs are rejected",()=>{
  const edited=copy(schedule);edited.events.push(copy(edited.events[0]));
  assert.throws(()=>api.events(edited,api.inventory(inventory)),/Duplicate event/);
});
test("duplicate item requirements are rejected",()=>{
  const edited=copy(schedule);edited.events[0].requirements.push({item_id:"pa",quantity:1});
  assert.throws(()=>api.audit(inventory,edited),/duplicates item/);
});
test("boolean, fractional and negative stock are rejected",()=>{
  for(const value of [true,1.5,-2,null,"5"]){
    const edited=copy(inventory);edited.items[0].quantity=value;
    assert.throws(()=>api.inventory(edited),/integer/);
  }
});
test("timezone-free date strings are rejected",()=>{
  const edited=copy(schedule);edited.events[0].start="2026-11-21T18:00:00";
  assert.throws(()=>api.audit(inventory,edited),/timezone/);
});
test("bad status rejected and cancelled event can't be planned",()=>{
  const edited=copy(schedule);edited.events[0].status="unknown";
  assert.throws(()=>api.audit(inventory,edited),/status/);
  edited.events[0].status="cancelled";
  assert.throws(()=>api.plan("a",inventory,edited),/Cancelled event/);
});
test("CSV parser accepts semicolons, embedded commas, BOM and escaped quotes",()=>{
  const csv='\uFEFFid;name;quantity;category\r\npa;"PA, ""main""";4;Sound\r\nmic;Wireless mic;5;Sound\r\n';
  const result=api.csvInventory(csv);
  assert.equal(result.items[0].name,'PA, "main"');
  assert.equal(result.items[1].quantity,5);
});
test("CSV parser accepts multiline quoted equipment names",()=>{
  const csv='id,name,quantity\npa,"Big PA\nspeaker",4\n';
  assert.equal(api.csvInventory(csv).items[0].name,"Big PA\nspeaker");
});
test("CSV parser skips blank rows and accepts zero stock",()=>{
  const csv='id,name,quantity\n\npa,PA,0\n';
  assert.equal(api.csvInventory(csv).items[0].quantity,0);
});
test("CSV parser rejects malformed and incomplete input",()=>{
  for(const csv of ["", "name,quantity\nX,1\n", "id,name,quantity\npa,PA,-1\n",
    'id,name,quantity\npa,PA,1,extra\n','id,name,quantity\npa,"PA,1\n']){
    assert.throws(()=>api.csvInventory(csv));
  }
});
test("CSV export quotes equipment names and blocks spreadsheet formula injection",()=>{
  const edited=copy(inventory);edited.items[0].name='=HYPERLINK("https://example.org")';
  const csv=api.exportInventoryCsv(edited);
  assert.match(csv, /"'=HYPERLINK\(""https:\/\//);
  assert.equal(api.csvInventory(csv).items[0].name,"'=HYPERLINK(\"https://example.org\")");
});
test("audit only returns non-cancelled events ordered by start time",()=>{
  const edited=copy(schedule);edited.events[0].status="cancelled";
  const plans=api.audit(inventory,edited);
  assert.deepEqual(plans.map(x=>x.event),["b"]);
});
test("engine validation does not mutate source input",()=>{
  const original=JSON.stringify(schedule);
  api.plan("a",inventory,schedule);
  assert.equal(JSON.stringify(schedule),original);
});
test("HTML entry point has local assets and no third-party script or CDN",()=>{
  const html=fs.readFileSync(path.resolve(__dirname,"../index.html"),"utf8");
  assert.match(html, /src="engine.js"/);
  assert.match(html, /src="app.js"/);
  assert.doesNotMatch(html, /src="https?:\/\//);
  assert.doesNotMatch(html, /(?:cdn\.|googletagmanager)/i);
});
test("browser app includes real data backup and no auto cloud storage",()=>{
  const src=fs.readFileSync(path.resolve(__dirname,"../app.js"),"utf8");
  assert.match(src,/saveJSON\("stageledger-events\.json"/);
  assert.match(src,/Engine\.validated/);
  assert.doesNotMatch(src,/\bfetch\s*\(/);
  assert.doesNotMatch(src,/localStorage\s*\./);
});
