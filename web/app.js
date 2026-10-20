/* StageLedger browser workspace. No server, third-party libraries or automatic storage. */
(function () {
  "use strict";
  var Engine = window.StageLedgerEngine;
  if (!Engine) throw new Error("StageLedger engine is missing");

  var DEMO_INVENTORY = {items: [
    {id:"pa-top",name:"Active PA speaker",quantity:4,category:"Sound"},
    {id:"pa-sub",name:"18-inch subwoofer",quantity:2,category:"Sound"},
    {id:"wireless-mic",name:"Wireless handheld microphone",quantity:4,category:"Microphones"},
    {id:"speaker-stand",name:"Speaker stand",quantity:4,category:"Rigging"},
    {id:"led-par",name:"LED PAR fixture",quantity:12,category:"Lighting"},
    {id:"xlr-cable",name:"XLR cable (10m)",quantity:20,category:"Cables"}
  ]};
  var DEMO_EVENTS = {events: [
    {id:"student-gala",title:"Student association gala · fictional demo",status:"confirmed",
     start:"2026-11-21T18:00:00Z",end:"2026-11-22T01:00:00Z",setup_minutes:120,teardown_minutes:90,
     requirements:[{item_id:"pa-top",quantity:2},{item_id:"pa-sub",quantity:2},{item_id:"wireless-mic",quantity:2},{item_id:"led-par",quantity:10}]},
    {id:"community-talk",title:"Community talk · fictional demo",status:"tentative",
     start:"2026-11-21T15:00:00Z",end:"2026-11-21T18:00:00Z",setup_minutes:60,teardown_minutes:60,
     requirements:[{item_id:"pa-top",quantity:3},{item_id:"wireless-mic",quantity:3},{item_id:"speaker-stand",quantity:2}]},
    {id:"cancelled-rehearsal",title:"Cancelled rehearsal · fictional demo",status:"cancelled",
     start:"2026-11-21T16:00:00Z",end:"2026-11-21T20:00:00Z",setup_minutes:0,teardown_minutes:0,
     requirements:[{item_id:"pa-sub",quantity:2}]}
  ]};
  var state={inventory:Engine.clone(DEMO_INVENTORY),events:Engine.clone(DEMO_EVENTS),demo:true};
  var activeScreen="overview", importKind="",toastTimer=null;

  function byId(id){return document.getElementById(id);}
  function node(tag, className, content) {
    var element=document.createElement(tag);
    if(className) element.className=className;
    if(content!==undefined && content!==null) element.textContent=String(content);
    return element;
  }
  function clean(target){target.replaceChildren();}
  function notify(message,isError) {
    var toast=byId("toast");
    toast.textContent=message;toast.className="toast show"+(isError?" error":"");
    window.clearTimeout(toastTimer);
    toastTimer=window.setTimeout(function(){toast.className="toast";},4200);
  }
  function formatTime(input) {
    var date=new Date(input);
    return new Intl.DateTimeFormat(undefined,{year:"numeric",month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"}).format(date);
  }
  function formatForInput(value) {
    var d=new Date(value);
    function pad(n){return String(n).padStart(2,"0");}
    return d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate())+"T"+pad(d.getHours())+":"+pad(d.getMinutes());
  }
  function fileSafe(value){return String(value).replace(/[^a-z0-9_-]/gi,"-").toLowerCase();}
  function escapeHtml(value) {return String(value).replace(/[&<>"']/g,function(ch){
    return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch];
  });}
  function saveFile(filename, content, mime) {
    var blob=new Blob([content],{type:mime || "text/plain;charset=utf-8"});
    var url=URL.createObjectURL(blob);
    var anchor=node("a");anchor.href=url;anchor.download=filename;
    document.body.appendChild(anchor);anchor.click();anchor.remove();
    window.setTimeout(function(){URL.revokeObjectURL(url);},1200);
    notify(filename+" downloaded. Store a backup before closing this tab.");
  }
  function saveJSON(filename,object){saveFile(filename,JSON.stringify(object,null,2)+"\n","application/json;charset=utf-8");}
  function available() {
    return Engine.audit(state.inventory,state.events);
  }
  function markChanged() {
    state.demo=false;
    var badge=byId("data-label");badge.textContent="UNSAVED WORK";badge.classList.add("custom");
  }
  function stateStatus(){
    var badge=byId("data-label");
    badge.textContent=state.demo?"DEMO DATA":"UNSAVED WORK";
    badge.classList.toggle("custom",!state.demo);
  }
  function statusPill(status){
    var label=status==="confirmed"?"Confirmed":status==="tentative"?"Tentative":"Cancelled";
    return node("span","pill "+(status==="confirmed"?"ok":status==="tentative"?"warn":"neutral"),label);
  }
  function availabilityPill(plan){
    if(!plan) return node("span","pill neutral","Not applicable");
    return node("span","pill "+(plan.ready?"ok":"bad"),plan.ready?"Available":"Shortage");
  }
  function metric(label,value,foot,symbol) {
    var card=node("div","metric");var top=node("div","metric-top");
    top.append(node("span","",label),node("span","metric-icon",symbol));
    card.append(top,node("div","metric-value",value),node("div","metric-foot",foot));
    return card;
  }
  function eventById(id){return state.events.events.find(function(e){return e.id===id;});}
  function plansMap() {return new Map(available().map(function(p){return [p.event,p];}));}
  function renderOverview(){
    var plans=available(), active=state.events.events.filter(function(x){return x.status!=="cancelled";});
    var errors=plans.filter(function(x){return !x.ready;});
    var total=state.inventory.items.reduce(function(s,x){return s+x.quantity;},0);
    byId("summary").replaceChildren(metric("Total units",total,"Across "+state.inventory.items.length+" equipment types","▦"),
      metric("Active events",active.length,"Excludes cancelled bookings","▤"),
      metric("Available plans",plans.length-errors.length,"No shortages detected","✓"),
      metric("At-risk events",errors.length,"Require action or more stock","!"));
    var box=byId("overview-events");clean(box);
    var ordered=state.events.events.slice().sort(function(a,b){return Date.parse(a.start)-Date.parse(b.start);});
    if(!ordered.length){box.append(node("div","surface empty","No events yet. Create your first booking."));return;}
    var map=new Map(plans.map(function(p){return[p.event,p];}));
    ordered.slice(0,6).forEach(function(event){
      var card=node("article","event-card"),top=node("div","event-top"),head=node("div");
      head.append(node("div","event-type","EVENT / "+event.id.toUpperCase()),node("h3","",event.title));
      top.append(head,statusPill(event.status));
      var meta=node("div","event-card-meta");
      meta.append(node("span","",formatTime(event.start)),node("span","",event.requirements.length+" equipment types"));
      var foot=node("div","event-card-foot");
      foot.append(availabilityPill(map.get(event.id)));
      var button=node("button","text-action","View details →");button.type="button";
      button.addEventListener("click",function(){openEvent(event.id);});
      foot.append(button);card.append(top,meta,foot);box.append(card);
    });
  }
  function renderInventory(){
    var filter=byId("inventory-search").value.toLowerCase().trim(),table=byId("inventory-table");
    clean(table);
    var sorted=state.inventory.items.slice().sort(function(a,b){return a.name.localeCompare(b.name);});
    var matched=sorted.filter(function(x){return [x.name,x.id,x.category].join(" ").toLowerCase().includes(filter);});
    if(!matched.length){var tr=node("tr"),td=node("td","empty","No matching equipment.");td.colSpan=5;tr.append(td);table.append(tr);return;}
    matched.forEach(function(item){
      var tr=node("tr");var name=node("td");name.append(node("div","item-name",item.name),node("div","item-sub",item.id));
      tr.append(name,node("td","",item.category || "—"),node("td","",item.id),node("td","right",item.quantity));
      var actions=node("td","right"),wrapper=node("div","table-actions");
      var edit=node("button","small-btn","Edit");edit.type="button";edit.addEventListener("click",function(){openItem(item.id);});
      var del=node("button","small-btn danger","Remove");del.type="button";del.addEventListener("click",function(){removeItem(item.id);});
      wrapper.append(edit,del);actions.append(wrapper);tr.append(actions);table.append(tr);
    });
  }
  function renderEvents(){
    var table=byId("events-table");clean(table);
    var filter=byId("events-search").value.toLowerCase().trim(),status=byId("events-filter").value;
    var plans=plansMap();
    var shown=state.events.events.filter(function(e){return (status==="all"||e.status===status)&&
      (e.title+" "+e.id).toLowerCase().includes(filter);})
      .sort(function(a,b){return Date.parse(a.start)-Date.parse(b.start);});
    if(!shown.length){var tr=node("tr"),td=node("td","empty","No matching events.");td.colSpan=5;tr.append(td);table.append(tr);return;}
    shown.forEach(function(event){
      var tr=node("tr"),heading=node("td");
      heading.append(node("div","event-name",event.title),node("div","item-sub",event.id));
      tr.append(heading,node("td","",formatTime(event.start)+" – "+formatTime(event.end)),node("td","",statusPill(event.status)),node("td","",availabilityPill(plans.get(event.id))));
      var cell=node("td","right"),actions=node("div","table-actions");
      var edit=node("button","small-btn","Edit");edit.type="button";edit.addEventListener("click",function(){openEvent(event.id);});
      var del=node("button","small-btn danger","Delete");del.type="button";del.addEventListener("click",function(){removeEvent(event.id);});
      actions.append(edit,del);cell.append(actions);tr.append(cell);table.append(tr);
    });
  }
  function renderReports(){
    var list=byId("report-events");clean(list);
    var plans=available();
    if(!plans.length){list.append(node("div","empty","No active events to export."));return;}
    plans.forEach(function(plan){
      var row=node("div","report-row"),detail=node("div");
      detail.append(node("strong","",plan.title),node("small","",formatTime(plan.start)+" · "+(plan.ready?"Ready":"Shortages detected")));
      var btn=node("button","btn btn-line","↓ Packing list");
      btn.type="button";btn.addEventListener("click",function(){saveFile(fileSafe(plan.event)+"-packing.html",reportHTML([plan]),"text/html;charset=utf-8");});
      row.append(detail,btn);list.append(row);
    });
  }
  function reportHTML(plans) {
    var body=plans.map(function(plan){
      var items=plan.items.map(function(item){
        return "<tr><td><input type='checkbox' aria-label='Packed "+escapeHtml(item.name)+"'></td>"+
          "<td><b>"+escapeHtml(item.name)+"</b><small>"+escapeHtml(item.id)+" · "+escapeHtml(item.category)+"</small></td>"+
          "<td>"+item.requested+"</td><td>"+item.available+"</td><td>"+item.shortage+"</td>"+
          "<td>"+escapeHtml(item.overlapping_events.join(", ")||"None")+"</td></tr>";
      }).join("");
      return "<section><div class='heading'><div><span class='kicker'>"+escapeHtml(plan.event)+"</span><h2>"+escapeHtml(plan.title)+"</h2></div>"+
        "<span class='pill "+(plan.ready?"good":"bad")+"'>"+(plan.ready?"READY":"SHORTAGE")+"</span></div>"+
        "<p class='dates'>Event: "+escapeHtml(formatTime(plan.start))+" → "+escapeHtml(formatTime(plan.end))+"<br>"+
        "Equipment reserved: "+escapeHtml(formatTime(plan.booking_start))+" → "+escapeHtml(formatTime(plan.booking_end))+
        " · "+escapeHtml(plan.status)+"</p><table><thead><tr><th>Packed</th><th>Item</th><th>Needed</th><th>Available</th><th>Missing</th><th>Other bookings</th></tr></thead><tbody>"+
        (items||"<tr><td colspan='6'>No equipment required</td></tr>")+"</tbody></table></section>";
    }).join("");
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+
      '<title>StageLedger packing report</title><style>'+
      'body{font:14px system-ui,sans-serif;color:#1b3542;background:#f6f8f9;margin:0}main{max-width:1100px;margin:auto;padding:40px 20px}h1{font-size:32px;margin:4px 0 14px}h2{margin:5px 0 0}p{color:#627c86;line-height:1.7}.kicker{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#69939c}'+
      'section{background:white;border:1px solid #dfe9ec;border-radius:14px;padding:24px;margin:20px 0;break-inside:avoid}.heading{display:flex;justify-content:space-between;gap:20px}.pill{font-size:11px;padding:8px 12px;border-radius:20px;align-self:center;font-weight:bold}.good{background:#dcf2e5;color:#17613f}.bad{background:#fde8e5;color:#9c302f}.dates{font-size:12px}'+
      'table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #e7eef0;padding:13px;text-align:left}th{font-size:11px;color:#75909c;text-transform:uppercase}td small{display:block;color:#8498a3}input[type=checkbox]{width:19px;height:19px;accent-color:#166e75}.print{border:0;background:#176e75;color:white;padding:12px;border-radius:8px;font-weight:bold}'+
      '@media print{body{background:white}main{padding:0}section{border-color:#bbb}.print{display:none}}'+
      '</style></head><body><main><button class="print" onclick="window.print()">Print / Save PDF</button><h1>StageLedger · Packing report</h1>'+
      '<p>Generated offline. Tick packed equipment before printing. Checkmarks are not permanently stored. Always verify physical availability.</p>'+body+
      '<p>Report data is from a local file; no online synchronization or guarantee of dispatch is provided.</p></main></body></html>';
  }
  function render(){stateStatus();renderOverview();renderInventory();renderEvents();renderReports();}
  function show(screen){
    activeScreen=screen;
    document.querySelectorAll(".screen").forEach(function(e){e.hidden=e.id!=="screen-"+screen;});
    document.querySelectorAll(".nav-link").forEach(function(btn){
      var on=btn.dataset.screen===screen;
      btn.classList.toggle("active",on);
      if(on) btn.setAttribute("aria-current","page");else btn.removeAttribute("aria-current");
    });
    var labels={overview:"Overview",inventory:"Inventory",events:"Events & bookings",reports:"Reports & exports",help:"Help & privacy"};
    byId("crumb-current").textContent=labels[screen]||screen;
  }
  function openItem(id){
    var form=byId("item-form");form.reset();
    var item=state.inventory.items.find(function(i){return i.id===id;});
    form.elements.namedItem("original_id").value=id||"";
    byId("item-dialog-title").textContent=item?"Edit equipment":"Add equipment";
    if(item) ["id","name","quantity","category"].forEach(function(k){form.elements.namedItem(k).value=item[k];});
    byId("item-dialog").showModal();
  }
  function removeItem(id){
    if(state.events.events.some(function(e){return e.requirements.some(function(r){return r.item_id===id;});})){
      notify("This item is used in event bookings. Remove those requirements first.",true);return;
    }
    if(!window.confirm("Remove equipment "+id+" from this working copy?"))return;
    state.inventory.items=state.inventory.items.filter(function(item){return item.id!==id;});
    markChanged();render();
  }
  function addRequirement(req){
    var line=node("div","requirement-line"),select=node("select"),amount=node("input");
    select.setAttribute("aria-label","Equipment type");select.required=true;
    state.inventory.items.forEach(function(item){
      var opt=node("option","",item.name+" ("+item.id+")");opt.value=item.id;select.append(opt);
    });
    if(req && req.item_id)select.value=req.item_id;
    amount.type="number";amount.min="1";amount.max="999999";amount.step="1";amount.required=true;amount.value=req?req.quantity:1;
    amount.setAttribute("aria-label","Units required");
    var remove=node("button","","×");remove.type="button";remove.title="Remove requirement";
    remove.addEventListener("click",function(){line.remove();});
    line.append(select,amount,remove);byId("requirements-list").append(line);
  }
  function openEvent(id){
    if(!state.inventory.items.length){notify("Add at least one inventory item before creating an event.",true);show("inventory");return;}
    var form=byId("event-form");form.reset();clean(byId("requirements-list"));
    var event=eventById(id);
    form.elements.namedItem("original_id").value=id||"";
    byId("event-dialog-title").textContent=event?"Edit event":"Create event";
    if(event){
      ["id","title","status"].forEach(function(k){form.elements.namedItem(k).value=event[k];});
      form.elements.namedItem("start").value=formatForInput(event.start);
      form.elements.namedItem("end").value=formatForInput(event.end);
      form.elements.namedItem("setup").value=event.setup_minutes;
      form.elements.namedItem("teardown").value=event.teardown_minutes;
      event.requirements.forEach(addRequirement);
    }else{
      var date=new Date();date.setDate(date.getDate()+1);
      date.setMinutes(0,0,0);
      form.elements.namedItem("start").value=formatForInput(date.toISOString());
      date.setHours(date.getHours()+2);
      form.elements.namedItem("end").value=formatForInput(date.toISOString());
      form.elements.namedItem("setup").value=0;form.elements.namedItem("teardown").value=0;
      addRequirement();
    }
    byId("event-dialog").showModal();
  }
  function removeEvent(id){
    if(!window.confirm("Delete the event "+id+" from this working copy?"))return;
    state.events.events=state.events.events.filter(function(event){return event.id!==id;});
    markChanged();render();
  }
  function saveItem(event){
    event.preventDefault();
    var f=event.currentTarget,original=f.elements.namedItem("original_id").value.trim(),id=f.elements.namedItem("id").value.trim();
    var copy=Engine.clone(state);
    var entry={id:id,name:f.elements.namedItem("name").value.trim(),
      quantity:Number(f.elements.namedItem("quantity").value),
      category:f.elements.namedItem("category").value.trim()};
    if(original){
      var current=copy.inventory.items.find(function(x){return x.id===original;});
      if(!current)throw new Error("Item was not found");
      Object.assign(current,entry);
      if(original!==id)copy.events.events.forEach(function(e){e.requirements.forEach(function(r){
        if(r.item_id===original)r.item_id=id;
      });});
    }else copy.inventory.items.push(entry);
    Engine.validated(copy.inventory,copy.events);
    state.inventory=copy.inventory;state.events=copy.events;markChanged();render();
    byId("item-dialog").close();notify("Equipment saved. Export your changes when finished.");
  }
  function saveEvent(event){
    event.preventDefault();
    var f=event.currentTarget,original=f.elements.namedItem("original_id").value.trim();
    var lines=Array.from(byId("requirements-list").children).map(function(row){
      return {item_id:row.querySelector("select").value,quantity:Number(row.querySelector("input").value)};
    });
    var start=new Date(f.elements.namedItem("start").value),end=new Date(f.elements.namedItem("end").value);
    if(!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()))throw new Error("Enter valid dates.");
    var entry={id:f.elements.namedItem("id").value.trim(),
      title:f.elements.namedItem("title").value.trim(),
      status:f.elements.namedItem("status").value,
      start:start.toISOString(),end:end.toISOString(),
      setup_minutes:Number(f.elements.namedItem("setup").value),
      teardown_minutes:Number(f.elements.namedItem("teardown").value),
      requirements:lines};
    var proposed=Engine.clone(state.events);
    if(original){
      var current=proposed.events.find(function(e){return e.id===original;});
      if(!current)throw new Error("Event was not found");
      Object.assign(current,entry);
    }else proposed.events.push(entry);
    Engine.validated(state.inventory,proposed);
    state.events=proposed;markChanged();render();
    byId("event-dialog").close();notify("Event saved and availability recalculated.");
  }
  function importFrom(kind){
    importKind=kind;
    byId("import-file").accept=kind==="inventory" ? ".csv,.json,text/csv,application/json" : ".json,application/json";
    byId("import-file").click();
  }
  async function importFile(input){
    var file=input.files[0];if(!file)return;
    var contents=await file.text();
    if(importKind==="inventory"){
      var newInventory=file.name.toLowerCase().endsWith(".csv")?Engine.csvInventory(contents):Engine.inventory(JSON.parse(contents));
      try {Engine.validated(newInventory,state.events);}
      catch(error){
        if(!window.confirm("The imported inventory is incompatible with some current event requirements. Clear the current event schedule to import it? You should export existing events first."))return;
        state.events={events:[]};
      }
      state.inventory=newInventory;
    }else {
      var schedule=JSON.parse(contents);
      state.events=Engine.events(schedule,state.inventory);
    }
    Engine.validated(state.inventory,state.events);
    markChanged();render();notify(file.name+" imported. Your changes exist only in this tab until exported.");
  }
  function action(name){
    if(name==="new-item")openItem();
    else if(name==="new-event")openEvent();
    else if(name==="import-inventory")importFrom("inventory");
    else if(name==="import-events")importFrom("events");
    else if(name==="export-inventory")saveFile("stageledger-inventory.csv",Engine.exportInventoryCsv(state.inventory),"text/csv;charset=utf-8");
    else if(name==="export-inventory-json")saveJSON("stageledger-inventory.json",state.inventory);
    else if(name==="export-events-json")saveJSON("stageledger-events.json",state.events);
    else if(name==="export-audit-html")saveFile("stageledger-audit.html",reportHTML(available()),"text/html;charset=utf-8");
  }
  document.addEventListener("click",function(event){
    var button=event.target.closest("[data-screen], [data-action], [data-close]");
    if(!button)return;
    if(button.dataset.screen){show(button.dataset.screen);}
    if(button.dataset.action){try{action(button.dataset.action);}catch(e){notify(e.message,true);}}
    if(button.dataset.close){byId(button.dataset.close).close();}
  });
  byId("item-form").addEventListener("submit",function(event){try{saveItem(event);}catch(e){event.preventDefault();notify(e.message,true);}});
  byId("event-form").addEventListener("submit",function(event){try{saveEvent(event);}catch(e){event.preventDefault();notify(e.message,true);}});
  byId("add-requirement").addEventListener("click",function(){addRequirement();});
  byId("inventory-search").addEventListener("input",renderInventory);
  byId("events-search").addEventListener("input",renderEvents);
  byId("events-filter").addEventListener("change",renderEvents);
  byId("import-file").addEventListener("change",async function(){
    try {await importFile(this);}catch(e){notify("Import failed: "+e.message,true);}
    finally {this.value="";}
  });
  byId("reset-demo").addEventListener("click",function(){
    if(!window.confirm("Reset to fictional demo data? Any unsaved edits in this tab will be lost."))return;
    state.inventory=Engine.clone(DEMO_INVENTORY);state.events=Engine.clone(DEMO_EVENTS);state.demo=true;
    byId("inventory-search").value="";byId("events-search").value="";byId("events-filter").value="all";
    render();show("overview");notify("Fictional sample restored.");
  });
  window.addEventListener("beforeunload",function(event){
    if(!state.demo){event.preventDefault();event.returnValue="";}
  });
  Engine.validated(state.inventory,state.events);
  render();
  show(activeScreen);
})();
