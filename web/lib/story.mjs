// Original parser. Story text/media are fetched at runtime from documented sources.
export const DATA_ROOT="https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/master/cn/gamedata/";
export const MEDIA_ROOT="https://raw.githubusercontent.com/ArknightsAssets/ArknightsAssets2/cn/assets/dyn/avg/";
export function attrs(source=""){
 const out={}; const re=/([\w]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^,\)]+))/g; let m;
 while((m=re.exec(source)))out[m[1].toLowerCase()]=(m[2]??m[3]??m[4]).trim();
 return out;
}
export function imageUrl(kind,name){
 if(!name || !/^[a-zA-Z0-9_#$-]+$/.test(name))return null;
 if(kind==="character")return "/api/media?kind=portrait&name="+encodeURIComponent(name);
 const base=name.split("#")[0];
 // Background and CG identifiers refer to standalone images.
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
   if(["background","image","character","charslot","playmusic","stopmusic","musicvolume"].includes(name))pending.push({name,a,route:route?[...route]:null});
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
export const CATEGORIES=[{id:"main",label:"主线"},{id:"side",label:"SideStory"},{id:"collection",label:"故事集"},{id:"personal",label:"个人密录"},{id:"other",label:"其他"}];
// Early entries use archive-launch timestamps; first-release corrections are sourced in docs/catalog-sources.md.
const EARLY_MAIN={main_0:"2019-04-30T10:00:00+08:00",main_1:"2019-04-30T10:00:00+08:00",main_2:"2019-04-30T10:00:00+08:00",main_3:"2019-04-30T10:00:00+08:00",main_4:"2019-04-30T10:00:00+08:00",main_5:"2019-07-09T16:00:00+08:00",main_6:"2019-12-24T16:00:00+08:00",main_7:"2020-05-01T16:00:00+08:00"};
export function releaseDate(timestamp){return timestamp>0?new Date(timestamp*1000+8*3600000).toISOString().slice(0,10):"日期待补";}
export function catalogFrom(raw,metadata={}){
 return Object.values(raw).filter(g=>Array.isArray(g.infoUnlockDatas)).map((g,groupSort)=>{
  const personal=metadata.personal?.[g.id];
  const category=g.entryType==="MAINLINE"?"main":g.entryType==="ACTIVITY"?"side":g.entryType==="MINI_ACTIVITY"?"collection":personal||g.infoUnlockDatas.some(s=>s.storyTxt?.startsWith("obt/memory/"))?"personal":"other";
  const releasedAt=personal?.releasedAt>0?personal.releasedAt:EARLY_MAIN[g.id]?Date.parse(EARLY_MAIN[g.id])/1000:metadata.mainline?.[g.id]>0?metadata.mainline[g.id]:g.startTime>0?g.startTime:category==="main"&&g.startShowTime>0?g.startShowTime:null;
  const operator=personal?.operator||"";
  return {id:g.id,title:g.name,type:g.entryType,category,operator,releasedAt,date:releaseDate(releasedAt),groupSort,chapters:g.infoUnlockDatas.filter(s=>s.storyTxt).map(s=>({id:s.storyTxt,title:s.storyName||g.name,code:s.storyCode||"",tag:s.avgTag||"",sort:s.storySort||0,releasedAt,category,groupId:g.id,groupTitle:g.name,operator})).sort((a,b)=>a.sort-b.sort)};
 }).filter(g=>g.chapters.length);
}
export function timelineFrom(groups){return groups.flatMap(g=>g.chapters.map(c=>({...c,groupSort:g.groupSort}))).sort((a,b)=>(a.releasedAt||Infinity)-(b.releasedAt||Infinity)||a.groupSort-b.groupSort||a.sort-b.sort);}

export function resolveScene(steps,index,decisions={}){
 let state={background:null,cg:null,actors:[],focus:0,music:null,musicVolume:1},choice=null;
 const slots=new Map();
 for(let i=0;i<=index;i++){
  const step=steps[i];if(!step)break;
  for(const event of step.events||[]){
   if(event.route&&!event.route.includes(choice))continue;
   const {name,a}=event;
   if(name==="background")state={...state,background:imageUrl("background",a.image),cg:null};
   if(name==="image")state={...state,cg:imageUrl("cg",a.image)};
   if(name==="character"){
    slots.clear();[a.name,a.name2].forEach((key,j)=>{if(key)slots.set(a.name2?(j?'r':'l'):'m',{key,url:imageUrl('character',key),slot:a.name2?(j?'r':'l'):'m'});});
    state={...state,actors:[...slots.values()],focus:Number(a.focus||1)-1};
   }
   if(name==="charslot"){
    if(!Object.keys(a).length)slots.clear();
    else if(a.slot){
     const previous=slots.get(a.slot);
     if(Object.hasOwn(a,'name')){if(a.name)slots.set(a.slot,{...previous,key:a.name,url:imageUrl('character',a.name),slot:a.slot});else slots.delete(a.slot);}
     const actor=slots.get(a.slot);
     if(actor){if(a.ato!==undefined)actor.opacity=Number(a.ato);if(a.scale!==undefined)actor.scale=Number(a.scale);if(a.posto)actor.offset=a.posto.split(',').map(Number);}
    }
    const actors=['l','m','r'].map(slot=>slots.get(slot)).filter(Boolean);
    state={...state,actors,focus:a.focus==='all'?-1:a.focus?actors.findIndex(actor=>actor.slot===a.focus):state.focus};
   }
   if(name==='playmusic')state={...state,music:{key:a.key||a.intro||'',intro:a.intro||null,event:step.id+':'+i},musicVolume:Number(a.volume??1)};
   if(name==='stopmusic')state={...state,music:null};
   if(name==='musicvolume')state={...state,musicVolume:Number(a.volume??1)};
  }
  if(step.type==='choice'&&i<index&&(!step.route||step.route.includes(choice)))choice=decisions[step.id]??choice;
 }
 return state;
}

export function nextChapter(groups,currentId){
 const group=groups.find(g=>g.chapters.some(c=>c.id===currentId));if(!group)return null;
 const index=group.chapters.findIndex(c=>c.id===currentId);if(index+1<group.chapters.length)return group.chapters[index+1];
 const siblings=groups.filter(g=>g.category===group.category).sort((a,b)=>(a.releasedAt||Infinity)-(b.releasedAt||Infinity)||a.groupSort-b.groupSort);
 return siblings[siblings.findIndex(g=>g.id===group.id)+1]?.chapters[0]||null;
}

export function previousStep(steps,index,decisions={}){
 let choice=null,previous=null;
 for(let i=0;i<Math.min(index,steps.length);i++){const step=steps[i];if(step.route&&!step.route.includes(choice))continue;previous={index:i,step,choice};if(step.type==='choice')choice=decisions[step.id]??choice;}
 return previous;
}
