// Original parser. Story text/media are fetched at runtime from documented sources.
export const DATA_ROOT="https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/master/cn/gamedata/";
export const MEDIA_ROOT="https://raw.githubusercontent.com/ArknightsAssets/ArknightsAssets2/cn/assets/dyn/avg/";
export function attrs(source=""){
 const out={}; const re=/([\w]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^,\)]+))/g; let m;
 while((m=re.exec(source)))out[m[1].toLowerCase()]=(m[2]??m[3]??m[4]).trim();
 return out;
}
export function imageUrl(kind,name){
 if(!name || !/^[a-zA-Z0-9_#-]+$/.test(name))return null;
 const base=name.split("#")[0];
 // Base portraits are reliable; expression overlays require separate composition.
 return MEDIA_ROOT+(kind==="character"?"characters/"+base+"/"+base+".png":(kind==="cg"?"images/":"backgrounds/")+base+".png");
}
export function parseStory(raw,id="chapter"){
 const steps=[]; let state={background:null,cg:null,actors:[],focus:0}; let route=null; let n=0; let pending=[]; const unsupported=new Set();
 for(const original of raw.replace(/^\uFEFF/,"").split(/\r?\n/)){
  const line=original.trim(); if(!line||line.startsWith("//"))continue;
  const cmd=/^\[([\w]+)(?:\((.*)\))?\]\s*(.*)$/.exec(line);
  const named=/^\[name\s*=\s*["']([^"']*)["']\]\s*(.*)$/.exec(line);
  if(named){steps.push({id:id+":"+n++,type:"line",speaker:named[1],text:clean(named[2]),route,scene:structuredClone(state),events:pending.splice(0)});continue;}
  if(cmd){
   const name=cmd[1].toLowerCase(), a=attrs(cmd[2]),tail=cmd[3];
   if(["background","image","character","charslot"].includes(name))pending.push({name,a,route:route?[...route]:null});
   if(name==="background")state={...state,background:imageUrl("background",a.image),cg:null};
   else if(name==="image")state={...state,cg:imageUrl("cg",a.image)};
   else if(name==="character"){
    state={...state,actors:[a.name,a.name2].filter(Boolean).map(x=>({key:x,url:imageUrl("character",x)})),focus:Number(a.focus||1)-1};
   }else if(name==="charslot"){
    if(!a.name && !a.focus)state={...state,actors:[]};
    else{
     const actors=[...state.actors]; const slot={l:0,m:0,r:1}[a.slot]??0;
     if(a.name)actors[slot]={key:a.name,url:imageUrl("character",a.name)};
     state={...state,actors:actors.filter(Boolean),focus:a.focus==="r"?1:0};
    }
   }else if(name==="decision"){
    const labels=(a.options||"").split(";"),values=(a.values||"").split(";");
    steps.push({id:id+":"+n++,type:"choice",choices:labels.map((label,i)=>({label:clean(label),value:values[i]||String(i+1)})),route,scene:structuredClone(state),events:pending.splice(0)});
   }else if(name==="predicate")route=a.references ? a.references.split(";") : null;
   else if(name==="subtitle"||name==="sticker"){
    if(a.text||tail)steps.push({id:id+":"+n++,type:"line",speaker:"",text:clean(a.text||tail),route,scene:structuredClone(state),events:pending.splice(0)});
   }else if(!["delay","blocker","playmusic","stopmusic","playsound","playvoice","cameraeffect","camerashake","dialog","dialogue","multiline","animtext","backgroundtween","imagetween","characteraction","charslot","animator","curtain","soundvolume","musicvolume","startb","endb"].includes(name))unsupported.add(name);
   continue;
  }
  if(!line.startsWith("["))steps.push({id:id+":"+n++,type:"line",speaker:"旁白",text:clean(line),route,scene:structuredClone(state),events:pending.splice(0)});
 }
 return {id,steps,warnings:[...unsupported]};
}
export function clean(text){return text.replace(/<[^>]+>/g,"").replace(/\{@nickname\}/g,"博士").replace(/\\n/g,"\n").trim();}
export function nextIndex(steps,from,choice){
 for(let i=from+1;i<steps.length;i++)if(!steps[i].route || steps[i].route.includes(choice))return i;
 return -1;
}
export function catalogFrom(raw){
 return Object.values(raw).filter(g=>Array.isArray(g.infoUnlockDatas)).map(g=>({id:g.id,title:g.name,type:g.entryType,chapters:g.infoUnlockDatas.filter(s=>s.storyTxt).map(s=>({id:s.storyTxt,title:s.storyName,code:s.storyCode,tag:s.avgTag,sort:s.storySort})).sort((a,b)=>a.sort-b.sort)})).filter(g=>g.chapters.length);
}

export function resolveScene(steps,index,decisions={}){
 let state={background:null,cg:null,actors:[],focus:0},choice=null;
 for(let i=0;i<=index;i++){
  const step=steps[i];if(!step)break;
  for(const event of step.events||[]){
   if(event.route&&!event.route.includes(choice))continue;
   const {name,a}=event;
   if(name==="background")state={...state,background:imageUrl("background",a.image),cg:null};
   if(name==="image")state={...state,cg:imageUrl("cg",a.image)};
   if(name==="character")state={...state,actors:[a.name,a.name2].filter(Boolean).map(key=>({key,url:imageUrl("character",key)})),focus:Number(a.focus||1)-1};
   if(name==="charslot"){
    if(!a.name&&!a.focus)state={...state,actors:[]};
    else{const actors=[...state.actors];const slot={l:0,m:0,r:1}[a.slot]??0;if(a.name)actors[slot]={key:a.name,url:imageUrl("character",a.name)};state={...state,actors:actors.filter(Boolean),focus:a.focus==="r"?1:0};}
   }
  }
  if(step.type==="choice"&&i<index&&(!step.route||step.route.includes(choice)))choice=decisions[step.id]??choice;
 }
 return state;
}
