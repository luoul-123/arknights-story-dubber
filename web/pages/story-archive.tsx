"use client";
import {useMemo,useState} from "react";
import {Search,ChevronRight,CalendarDays,LibraryBig} from "lucide-react";
import {CATEGORIES,timelineFrom,releaseDate} from "../lib/story.mjs";
import {isVoicedChapter} from "./audio";
export default function StoryArchive({groups,currentId,onSelect,onRetry,focusGroupId}:any){
 const [view,setView]=useState("groups"),[category,setCategory]=useState("all"),[query,setQuery]=useState(""),[order,setOrder]=useState("oldest"),[limit,setLimit]=useState(80),[year,setYear]=useState("all"),[focused,setFocused]=useState<string|null>(focusGroupId||null);
 const q=query.trim().toLocaleLowerCase();
 const timeline=useMemo(()=>timelineFrom(groups),[groups]);
 const years=useMemo(()=>[...new Set<string>(timeline.filter((c:any)=>c.releasedAt).map(c=>releaseDate(c.releasedAt).slice(0,4)))].sort(),[timeline]);
 const counts=useMemo(()=>Object.fromEntries(CATEGORIES.map(c=>[c.id,groups.filter((g:any)=>g.category===c.id).reduce((n:number,g:any)=>n+g.chapters.length,0)])),[groups]);
 const matches=(c:any,g?:any)=>!q||[c.title,c.code,c.operator,c.groupTitle,g?.title,g?.operator].filter(Boolean).join(" ").toLocaleLowerCase().includes(q);
 const visibleGroups=useMemo(()=>groups.filter((g:any)=>(!focused||g.id===focused)&&(category==="all"||g.category===category)).map((g:any)=>({...g,chapters:g.chapters.filter((c:any)=>matches(c,g))})).filter((g:any)=>g.chapters.length),[groups,category,q,focused]);
 const entries=useMemo(()=>{const rows=groups.filter((c:any)=>(category==="all"||c.category===category)&&(year==="all"||releaseDate(c.releasedAt).startsWith(year))&&(matches(c)||c.chapters.some((chapter:any)=>matches(chapter,c))));return order==="newest"?[...rows.filter((c:any)=>c.releasedAt).sort((a:any,b:any)=>b.releasedAt-a.releasedAt||a.groupSort-b.groupSort||a.sort-b.sort),...rows.filter((c:any)=>!c.releasedAt)]:[...rows].sort((a:any,b:any)=>(a.releasedAt||Infinity)-(b.releasedAt||Infinity)||a.groupSort-b.groupSort);},[groups,category,year,q,order]);
 const reset=(fn:()=>void)=>{fn();setFocused(null);setLimit(80);};
 return <div className="story-archive">
  <div className="archive-views" role="tablist" aria-label="剧情档案视图"><button role="tab" aria-selected={view==="groups"} onClick={()=>setView("groups")}><LibraryBig size={15}/>分类阅读</button><button role="tab" aria-selected={view==="timeline"} onClick={()=>setView("timeline")}><CalendarDays size={15}/>实装时间线</button></div>
  <label className="search"><Search size={17}/><input aria-label="搜索剧情档案" placeholder="搜索章节、活动、剧情或干员" value={query} onChange={e=>reset(()=>setQuery(e.target.value))}/></label>
  <div className="archive-categories" aria-label="剧情分类"><button className={category==="all"?"selected":""} onClick={()=>reset(()=>setCategory("all"))}>全部<span>{timeline.length}</span></button>{CATEGORIES.map(c=><button key={c.id} className={category===c.id?"selected":""} onClick={()=>reset(()=>setCategory(c.id))}>{c.label}<span>{counts[c.id]||0}</span></button>)}</div>
  {!groups.length?<div className="archive-empty"><p>剧情目录暂未加载。</p><button onClick={onRetry}>重新加载</button></div>:view==="groups"?<div className="catalog">{focused&&<p className="archive-focus">已定位到这部剧情 · <button onClick={()=>setFocused(null)}>查看全部目录</button></p>}{!visibleGroups.length&&<p className="muted">没有找到符合条件的剧情。</p>}{visibleGroups.map((g:any)=><details key={g.id} open={q||focused?true:undefined}><summary><div><b>{g.operator?g.operator+" · ":""}{g.title}</b><small>{CATEGORIES.find(c=>c.id===g.category)?.label} · {g.date||"日期待补"}</small></div><span>{g.chapters.length}</span></summary>{g.chapters.map((c:any)=><button className={"chapter-row "+(c.id===currentId?"selected":"")} key={c.id} onClick={()=>onSelect(c)}><span>{c.code||"ST"}</span><div><b>{c.title}</b><small>{c.tag}{isVoicedChapter(c.id)?" · 凯尔希有声":""}</small></div><ChevronRight size={16}/></button>)}</details>)}</div>:<div className="archive-timeline">
   <div className="timeline-toolbar"><label>年份<select aria-label="实装年份" value={year} onChange={e=>reset(()=>setYear(e.target.value))}><option value="all">全部年份</option>{years.map(y=><option key={y}>{y}</option>)}</select></label><select aria-label="时间顺序" value={order} onChange={e=>reset(()=>setOrder(e.target.value))}><option value="oldest">从最早到最新</option><option value="newest">从最新到最早</option></select></div>
   <p className="timeline-note">国服首次实装 · 同一活动内保留原剧情顺序</p>
   {!entries.length&&<p className="muted">没有找到符合条件的剧情。</p>}
   {entries.slice(0,limit).map((g:any,i:number,shown:any[])=>{const date=releaseDate(g.releasedAt);return <div key={g.id}>{(i===0||releaseDate(shown[i-1].releasedAt)!==date)&&<h3 className="timeline-date">{date}</h3>}<details className="timeline-collection" data-release={g.releasedAt||"unknown"}><summary className="timeline-row"><span className="timeline-dot"/><div><small>{CATEGORIES.find(k=>k.id===g.category)?.label}</small><b>{g.category==="main"?"第 "+g.id.replace("main_","")+" 章 · ":g.operator?g.operator+" · ":""}{g.title}</b><span>{g.chapters.length} 段剧情 · 点击展开</span></div><ChevronRight size={15}/></summary>{g.chapters.filter((c:any)=>matches(c,g)).map((c:any)=><button className={"chapter-row "+(c.id===currentId?"selected":"")} key={c.id} onClick={()=>onSelect(c)}><span>{c.code||"ST"}</span><div><b>{c.title}</b><small>{c.tag}{isVoicedChapter(c.id)?" · 凯尔希有声":""}</small></div><ChevronRight size={16}/></button>)}</details></div>;})}
   {entries.length>limit&&<button className="archive-more" onClick={()=>setLimit(n=>n+80)}>继续查看 · 已显示 {Math.min(limit,entries.length)} / {entries.length}</button>}
  </div>}
  <p className="source-note">剧情与演出素材归鹰角网络及相关权利人所有。<a href="https://github.com/ArknightsAssets/ArknightsGamedata" target="_blank" rel="noreferrer">数据来源</a></p>
 </div>;
}
