/* Cross-check web engine against the Python CLI using the same public scenario. */
const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const {spawnSync}=require("node:child_process");
const engine=require("../engine.js");

test("JavaScript and Python agree on example shortage calculations",()=>{
  const root=path.resolve(__dirname,"../..");
  const invPath=path.join(root,"examples/association_inventory.json");
  const eventsPath=path.join(root,"examples/association_events.json");
  const inventory=JSON.parse(fs.readFileSync(invPath,"utf8"));
  const events=JSON.parse(fs.readFileSync(eventsPath,"utf8"));
  const js=engine.audit(inventory,events);
  const python=process.env.PYTHON || (process.platform==="win32"?"python":"python3");
  const child=spawnSync(python,["-m","stageledger","audit",
    "--inventory",invPath,"--events",eventsPath,"--format","json"],{cwd:root,encoding:"utf8"});
  assert.ok([0,2].includes(child.status),"Python CLI failed: "+child.stderr);
  const py=JSON.parse(child.stdout);
  const simplified=plans=>plans.map(p=>({
    event:p.event,ready:p.ready,items:p.items.map(i=>({
      id:i.id,requested:i.requested,available:i.available,
      shortage:i.shortage,other_bookings_peak:i.other_bookings_peak,
      overlapping_events:i.overlapping_events
    }))
  }));
  assert.deepEqual(simplified(js),simplified(py));
});
