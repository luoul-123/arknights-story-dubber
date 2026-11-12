"use client";
import {useCallback,useEffect,useRef,useState} from "react";
import {BookOpen,Settings2,Volume2,VolumeX,ChevronsRight,Play,Pause,History,ChevronLeft,ChevronRight,X,Maximize,Minimize,Headphones,Mic2,Upload,Check,RefreshCw,Search,ArrowLeft,LoaderCircle,SkipForward,Keyboard,Cloud,Triangle,Save} from "lucide-react";
import StoryArchive from "./story-archive";
import ReaderStudio from "./reader-studio";
import {DialogueAudio,resolveVoice} from "../lib/audio.mjs";
import {nextIndex,nextChapter,resolveScene,MEDIA_ROOT} from "../lib/story.mjs";
type Scene={background:string|null;cg:string|null;actors:{key:string;url:string}[];focus:number};
type Step={id:string;type:string;text?:string;speaker?:string;route:string[]|null;choices?:{label:string;value:string}[];scene:Scene};
type Chapter={id:string;title:string;code:string;tag:string};
type Group={id:string;title:string;chapters:Chapter[]};
type Voice={id:string;speaker:string;version:string;aliases?:string[];kind?:string};
const FIRST:Chapter={id:"obt/main/level_main_00-01_beg",title:"坍塌",code:"0-1",tag:"行动前"};
const BG=MEDIA_ROOT+"backgrounds/bg_cher_1.png";
function IconButton({label,onClick,active=false,children}:any){return <button className={"icon-button "+(active?"active":"")} title={label} aria-label={label} onClick={onClick}>{children}</button>;}
async function api(path:string,options?:RequestInit):Promise<any>{const r=await fetch("/api/voice/"+path,options);const j:any=await r.json();if(!r.ok)throw Error(j.error||"操作失败");return j;}
function Actor({actor,focus,total}:any){const [attempt,setAttempt]=useState(0);useEffect(()=>setAttempt(0),[actor.key]);const base=actor.key.split("#")[0];const urls=[actor.url,MEDIA_ROOT+"characters/"+base+".png"];if(attempt>=urls.length)return null;return <img alt="" className={"actor "+(focus?"focused":"dimmed")+" "+(total===1?"solo":"")} src={urls[attempt]} onError={()=>setAttempt(a=>a+1)}/>;}
export default function Theater(){
 const [chapter,setChapter]=useState<Chapter>(FIRST),[steps,setSteps]=useState<Step[]>([]),[index,setIndex]=useState(0),[choice,setChoice]=useState<string|null>(null),[decisions,setDecisions]=useState<Record<string,string>>({});
 const [catalog,setCatalog]=useState<Group[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState(""),[drawer,setDrawer]=useState<string|null>(null),[search,setSearch]=useState("");
 const [history,setHistory]=useState<{index:number;step:Step;choice:string|null}[]>([]),[typing,setTyping]=useState(true),[shown,setShown]=useState(0);
 const [readerVoice,setReaderVoice]=useState<Voice|null>(null);
 const selectReaderVoice=(voice:Voice|null)=>{setReaderVoice(voice);localStorage.setItem("terra-reader-mode",voice?"unified":"characters");};
 const [listening,setListening]=useState(false);const listeningRef=useRef(false),moveRef=useRef<()=>void>(()=>{}),backRef=useRef<()=>void>(()=>{});
 const [auto,setAuto]=useState(false),[muted,setMuted]=useState(false),[volume,setVolume]=useState(.85),[rate,setRate]=useState(1);
 const [voices,setVoices]=useState<Voice[]>([]),[voiceStatus,setVoiceStatus]=useState("idle"),[voiceError,setVoiceError]=useState(""),[backend,setBackend]=useState<any>({connected:false,admin:false});
 const [started,setStarted]=useState(false),[ended,setEnded]=useState(false),[full,setFull]=useState(false),[saved,setSaved]=useState<any>(null),[toast,setToast]=useState("");
 const chapterEpoch=useRef(0);
 const player=useRef<any>(null),advanceRef=useRef<()=>void>(()=>{}),speechEpoch=useRef(0),stage=useRef<HTMLDivElement>(null);
 const step=steps[index],text=step?.text||"",characters=Array.from(text),complete=!typing||shown>=characters.length;
 useEffect(()=>{player.current=new DialogueAudio({onState:(state:string,msg?:string)=>{setVoiceStatus(state);setVoiceError(msg||"");if("mediaSession" in navigator)navigator.mediaSession.playbackState=state==="playing"?"playing":state==="paused"?"paused":"none";}});return()=>{player.current?.dispose();window.speechSynthesis?.cancel();};},[]);
 useEffect(()=>{
  try{const s=JSON.parse(localStorage.getItem("zhousheng-progress")||"null");if(s)setSaved(s);const settings=JSON.parse(localStorage.getItem("zhousheng-settings")||"null");if(settings){setTyping(settings.typing??true);setVolume(settings.volume??.85);}}catch{}
  fetch("/api/stories?catalog=2").then(r=>{if(!r.ok)throw Error();return r.json() as Promise<Group[]>;}).then(setCatalog).catch(()=>{});
  api("status").then(status=>{setBackend(status);if(status.userId&&localStorage.getItem("terra-reader-mode")==="unified")api("reader/voice").then(p=>setReaderVoice(p.voice)).catch(()=>{});}).catch(()=>{});
  api("voices").then(j=>setVoices(j.voices||[])).catch(e=>setVoiceError(e.message));
 },[]);
 useEffect(()=>{localStorage.setItem("zhousheng-settings",JSON.stringify({typing,volume}));},[typing,volume]);
 const loadChapter=useCallback(async(c:Chapter,resume?:any)=>{
  const requestId=++chapterEpoch.current;player.current?.stop();window.speechSynthesis?.cancel();speechEpoch.current++;setStarted(false);setLoading(true);setError("");setEnded(false);setHistory([]);setChapter(c);setSteps([]);
  try{const r=await fetch("/api/stories?id="+encodeURIComponent(c.id));const j:any=await r.json();if(requestId!==chapterEpoch.current)return;if(!r.ok)throw Error(j.error);if(!j.steps.length)throw Error("本章暂时没有可读取的台词");setSteps(j.steps);setIndex(Math.min(resume?.index||0,j.steps.length-1));setChoice(resume?.choice||null);setDecisions(resume?.decisions||{});if(listeningRef.current)setStarted(true);}
  catch(e){if(requestId===chapterEpoch.current)setError((e as Error).message||"章节加载失败");}finally{if(requestId===chapterEpoch.current)setLoading(false);}
 },[]);
 useEffect(()=>{loadChapter(FIRST);},[loadChapter]);
 useEffect(()=>{setShown(0);if(!step||!typing)return;const timer=setInterval(()=>setShown(n=>Math.min(n+1,Array.from(step.text||"").length)),30);return()=>clearInterval(timer);},[step?.id,typing]);
 useEffect(()=>{if(!step||loading)return;const data={chapter,index,choice,decisions,time:Date.now()};localStorage.setItem("zhousheng-progress",JSON.stringify(data));},[chapter,index,choice,decisions,step,loading]);
 useEffect(()=>{player.current?.setOptions({volume,rate});},[volume,rate]);
 const voiceFor=useCallback((line:Step)=>resolveVoice(voices,line,readerVoice),[voices,readerVoice]);
 const playCurrent=useCallback(()=>{
  if(!step||step.type!=="line"||ended)return;
  player.current?.stop();window.speechSynthesis?.cancel();const token=++speechEpoch.current;setVoiceError("");
  if(!started||muted){setVoiceStatus("silent");return;}
  const voice=voiceFor(step);
  if(voice){player.current.play(step,voice,{onEnd:()=>{if(listeningRef.current)moveRef.current();}});const ni=nextIndex(steps,index,choice);if(ni>=0&&steps[ni].type==="line"){const nv=voiceFor(steps[ni]);if(nv)player.current.prefetch(steps[ni],nv);}return;}
  setVoiceStatus("unavailable");
 },[step,started,muted,voiceFor,steps,index,choice,ended]);
 useEffect(()=>{playCurrent();return()=>{player.current?.stop();window.speechSynthesis?.cancel();speechEpoch.current++;};},[playCurrent]);
 const move=useCallback((selected?:string)=>{
  if(!step)return;if(step.type==="choice"&&!selected)return;
  player.current?.stop();window.speechSynthesis?.cancel();speechEpoch.current++;
  if(selected)setDecisions(d=>({...d,[step.id]:selected}));
  const route=selected??choice;const next=nextIndex(steps,index,route);
  setHistory(h=>[...h,{index,step,choice}].slice(-200));
  if(next<0){setEnded(true);setAuto(false);setVoiceStatus("ended");return;}
  setChoice(route);setIndex(next);
 },[step,choice,index,steps]);
 moveRef.current=()=>move();
 const advance=useCallback(()=>{if(drawer||loading||ended)return;if(!started){setStarted(true);return;}if(step?.type==="choice")return;if(!complete){setShown(characters.length);return;}move();},[drawer,loading,ended,started,step,complete,characters.length,move]);
 advanceRef.current=advance;
 useEffect(()=>{
  if(listening||!auto||!started||!complete||drawer||ended||step?.type!=="line"||["loading","playing","paused","error"].includes(voiceStatus))return;
  const timer=setTimeout(()=>move(),voiceStatus==="ended"?700:Math.max(1600,text.length*110));return()=>clearTimeout(timer);
 },[listening,auto,started,complete,drawer,ended,step,voiceStatus,text,move]);
 useEffect(()=>{const listener=(e:KeyboardEvent)=>{if((e.target as HTMLElement).closest("input,textarea,select,button"))return;if(e.key==="Escape"){setDrawer(null);return;}if(drawer)return;if(e.key===" "||e.key==="Enter"||e.key==="ArrowRight"){e.preventDefault();advanceRef.current();}if(e.key.toLowerCase()==="a")setAuto(v=>!v);if(e.key.toLowerCase()==="h")setDrawer("history");};window.addEventListener("keydown",listener);return()=>window.removeEventListener("keydown",listener);},[drawer]);
 useEffect(()=>{if(!toast)return;const t=setTimeout(()=>setToast(""),2500);return()=>clearTimeout(t);},[toast]);
 const back=()=>{if(!history.length)return;const item=history[history.length-1];setHistory(h=>h.slice(0,-1));setIndex(item.index);setChoice(item.choice);setEnded(false);};
 backRef.current=back;
 const openDrawer=(name:string)=>{setDrawer(name);if(!listeningRef.current){setAuto(false);player.current?.pause();}};
 const scene=step?resolveScene(steps,index,decisions):null;const currentVoice=step?voiceFor(step):null;
 useEffect(()=>{
  if(!("mediaSession" in navigator))return;
  navigator.mediaSession.metadata=new MediaMetadata({title:step?.type==="choice"?"请选择剧情分支":chapter.code+" · "+chapter.title,artist:step?.speaker||"旁白",album:"泰拉之声 · 随身听"});
  const handlers:Record<string,()=>void>={play:()=>{setStarted(true);if(player.current?.current)player.current.resume();else playCurrent();},pause:()=>player.current?.pause(),nexttrack:()=>moveRef.current(),previoustrack:()=>backRef.current(),stop:()=>{player.current?.stop();setListening(false);listeningRef.current=false;}};
  for(const [action,handler] of Object.entries(handlers)){try{navigator.mediaSession.setActionHandler(action as MediaSessionAction,handler);}catch{}}
  return()=>{for(const action of Object.keys(handlers)){try{navigator.mediaSession.setActionHandler(action as MediaSessionAction,null);}catch{}}};
 },[step?.id,chapter,playCurrent]);
 const toggleListening=()=>{const enabled=!listening;setListening(enabled);listeningRef.current=enabled;setAuto(false);if(enabled){setStarted(true);setMuted(false);if(started)playCurrent();setToast("随身听已开启：遇到分支或段落结束时等待确认");}};
 const nextSection=nextChapter(catalog,chapter.id);
 const continueSection=async()=>{if(!nextSection)return;setDrawer(null);await loadChapter(nextSection);setStarted(true);};
 const fullScreen=async()=>{if(document.fullscreenElement)await document.exitFullscreen();else await stage.current?.requestFullscreen();setFull(!!document.fullscreenElement);};
 return <main className="theater" ref={stage}>
  <div className="scene" onClick={advance} aria-hidden="true">
   <img key={scene?.background||"blank"} className="background" style={{opacity:started&&!scene?.background?0:undefined}} src={scene?.background||BG} alt="" onError={e=>{e.currentTarget.style.opacity="0";}}/>
   <div className="scene-shade"/>
   {!scene?.cg&&<div className="actors">{scene?.actors?.map((actor,i)=><Actor key={actor.key+i} actor={actor} focus={scene.focus===i} total={scene.actors.length}/>)}</div>}
   {scene?.cg&&<img key={scene.cg} className="cg" src={scene.cg} alt="剧情 CG" onError={e=>{e.currentTarget.style.opacity="0";}}/>}
   <div className="scene-grain"/><div className="vignette"/>
  </div>
  <header className="topbar">
   <button className="brand" onClick={()=>openDrawer("chapters")}><span className="brand-mark"><Triangle size={23}/><span/></span><b>泰拉之声</b><span className="brand-en">VOICES OF TERRA</span></button>
   <div className="chapter-heading"><span>EPISODE 00</span><span className="divider"/><b>{chapter.code} · {chapter.title}</b><span className="tag">{chapter.tag}</span></div>
   <div className="top-actions"><button className={"listen-toggle "+(listening?"active":"")} onClick={toggleListening}><Headphones size={16}/><span>{listening?"随身听中":"随身听"}</span></button><span className="private-note">非官方同人剧场</span><IconButton label="章节目录" onClick={()=>openDrawer("chapters")}><BookOpen size={19}/></IconButton><IconButton label="音色工作室" onClick={()=>openDrawer("studio")}><Mic2 size={19}/></IconButton><IconButton label="阅读设置" onClick={()=>openDrawer("settings")}><Settings2 size={19}/></IconButton></div>
  </header>
  <aside className="scene-meta"><span className="tiny-cross">+</span><span>RHODES ISLAND</span><div/><span>STORY ARCHIVE / {chapter.code}</span></aside>
  {loading&&<div className="center-card loading"><LoaderCircle className="spin" size={27}/><h2>正在打开泰拉的故事</h2><p>加载章节与演出资源</p></div>}
  {error&&<div className="center-card"><h2>这一页暂时没有打开</h2><p>{error}</p><button className="primary" onClick={()=>loadChapter(chapter)}><RefreshCw size={16}/>重新加载</button><button onClick={()=>openDrawer("chapters")}>选择其他章节</button></div>}
  {!loading&&!error&&!started&&<div className="entry-overlay"><div className="entry-copy"><span className="eyebrow">ARKNIGHTS · VOICED STORY THEATER</span><h1>让故事，<br/>有声而至<span>。</span></h1><p>重返泰拉。在每一次相遇里，听见他们的声音。</p><div className="entry-actions"><button className="primary" onClick={()=>setStarted(true)}><Play size={17} fill="currentColor"/>进入剧情<span>{chapter.code} / {chapter.title}</span></button>{saved&&<button className="text-button" onClick={()=>loadChapter(saved.chapter,saved).then(()=>setStarted(true))}>继续上次阅读 <ChevronRight size={15}/></button>}</div><span className="entry-foot"><Headphones size={14}/>角色、NPC 与旁白自动配音 · 无需配置</span></div><div className="entry-number">00<span>黑暗时代</span></div></div>}
  {started&&step?.type==="choice"&&!ended&&<div className="choice-panel"><span className="eyebrow">博士，你的选择</span>{step.choices?.map((c,i)=><button key={c.value+i} onClick={()=>move(c.value)}><span>0{i+1}</span>{c.label}<ChevronRight size={17}/></button>)}</div>}
  {ended&&<div className="center-card chapter-complete"><span className="eyebrow">TO BE CONTINUED</span><h2>本段故事已读完</h2>{nextSection?<><p>下一段：{nextSection.code} · {nextSection.title}<br/><span>{nextSection.tag}</span></p><button className="primary" onClick={continueSection}>继续下一段 <ChevronRight size={17}/></button></>:<p>这一系列暂时读完了，去探索其他故事吧。</p>}<button onClick={()=>openDrawer("chapters")}>打开剧情档案</button><button onClick={()=>{setEnded(false);back();}}>返回上一句</button></div>}
  {started&&!loading&&!error&&step?.type==="line"&&!ended&&<section className="dialogue-shell" aria-label="剧情对话">
   <div className="dialogue-header"><div className="speaker-rule"/><h2>{step.speaker||"旁白"}</h2><div className="voice-indicator"><span className={"voice-dot "+(voiceStatus==="playing"?"pulsing":"")}/>{muted?"静音":voiceStatus==="loading"?"正在生成配音":currentVoice?(currentVoice.kind==="reader"?"统一朗读":currentVoice.kind==="narrator"?"旁白":currentVoice.kind==="fallback"?"通用角色声音":"AI 角色配音"):"配音服务待连接"}</div></div>
   <button className="dialogue-text" onClick={advance} aria-label={complete?"下一句":"显示完整台词"}><span>{typing?characters.slice(0,shown).join(""):text}</span><span className="advance-glyph">{complete?<Triangle size={11} fill="currentColor"/>:<span className="typing-cursor"/>}</span></button>
   <div className="dialogue-bottom"><span className="line-number">{String(index+1).padStart(3,"0")} <span>/ {String(steps.length).padStart(3,"0")}</span></span><span className="click-hint">{voiceError||(!complete?"点击显示完整台词":"点击继续 · Space")}</span></div>
  </section>}
  <footer className="controlbar">
   <div className="control-left"><button onClick={()=>openDrawer("chapters")}><BookOpen size={16}/>目录</button><span className="control-sep"/><button onClick={()=>openDrawer("history")}><History size={16}/>回顾</button><button onClick={()=>{setSaved({chapter,index,choice,decisions});setToast("阅读进度已保存在此浏览器");}}><Save size={16}/>存档</button></div>
   <div className="control-center"><IconButton label="上一句" onClick={back}><ChevronLeft size={21}/></IconButton><button className={"auto-button "+(auto?"active":"")} onClick={()=>{if(listening){if(voiceStatus==="paused")player.current.resume();else player.current.pause();}else{if(!started)setStarted(true);setAuto(a=>!a);}}}>{(listening?voiceStatus!=="paused":auto)?<Pause size={14}/>:<Play size={14}/>}<span className="play-label">{listening?(voiceStatus==="paused"?"播放":"暂停"):"自动"}</span><span>{listening?"LISTEN":"AUTO"}</span></button><IconButton label="立即跳过当前句" onClick={()=>{if(!started)setStarted(true);else move();}}><SkipForward size={19}/></IconButton></div>
   <div className="control-right"><IconButton label={muted?"开启配音":"静音"} active={!muted} onClick={()=>setMuted(m=>!m)}>{muted?<VolumeX size={18}/>:<Volume2 size={18}/>}</IconButton><button className="voice-label" onClick={()=>openDrawer("settings")}>{voices.length?"配音已就绪":"配音设置"}</button><span className="control-sep"/><IconButton label="全屏" onClick={fullScreen}>{full?<Minimize size={17}/>:<Maximize size={17}/>}</IconButton></div>
  </footer>
  <div className="progress-track"><div style={{width:steps.length?((index+1)/steps.length*100)+"%":"0"}}/></div>
  {listening&&started&&<div className="listen-badge"><Headphones size={13}/>{ended?"本节播放完毕":step?.type==="choice"?"等待你的选择":voiceStatus==="error"?"播放遇到问题，请重试":voiceStatus==="paused"?"已暂停":voiceStatus==="loading"?"正在准备下一句":"随身听 · 可切换到后台"}</div>}
  {toast&&<div className="toast"><Check size={16}/>{toast}</div>}
  {drawer&&<div className="drawer-backdrop" onClick={()=>setDrawer(null)}><aside className={"drawer "+(drawer==="studio"?"studio-drawer":"")} onClick={e=>e.stopPropagation()}>
   <div className="drawer-head"><div><span className="eyebrow">{drawer==="studio"?"VOICE STUDIO":drawer==="chapters"?"STORY ARCHIVE":drawer==="history"?"BACKLOG":"PREFERENCES"}</span><h2>{{chapters:"剧情档案",studio:"朗读录音室",history:"对话回顾",settings:"阅读设置"}[drawer]}</h2></div><IconButton label="关闭面板" onClick={()=>setDrawer(null)}><X size={21}/></IconButton></div>
   {listening&&started&&<div className="drawer-player"><Headphones size={17}/><div><b>{ended?"本段播放完毕":step?.type==="choice"?"等待剧情选择":voiceStatus==="paused"?"收听已暂停":"正在收听"} · {chapter.code}</b><span>{step?.speaker||"旁白"} · {text.slice(0,32)}</span></div><button aria-label={voiceStatus==="paused"?"继续随身听":"暂停随身听"} onClick={()=>voiceStatus==="paused"?player.current?.resume():player.current?.pause()}>{voiceStatus==="paused"?<Play size={16}/>:<Pause size={16}/>}</button>{ended&&nextSection&&<button aria-label="确认进入下一段" onClick={continueSection}><ChevronRight size={17}/></button>}<button aria-label="随身听下一句" onClick={()=>move()}><SkipForward size={17}/></button></div>}
   {drawer==="chapters"&&<StoryArchive groups={catalog} currentId={chapter.id} onSelect={(c:Chapter)=>{setDrawer(null);loadChapter(c);}} onRetry={()=>fetch("/api/stories?catalog=2").then(r=>r.json()).then(j=>Array.isArray(j)&&setCatalog(j))}/>}
   {drawer==="history"&&<div className="backlog">{!history.length?<p className="muted">读过的台词会出现在这里。</p>:history.map((h,i)=><button key={i} onClick={()=>{setIndex(h.index);setChoice(h.choice);setHistory(old=>old.slice(0,i));setEnded(false);setDrawer(null);}}><span>{String(h.index+1).padStart(3,"0")}</span><div><b>{h.step.speaker||"博士的选择"}</b><p>{h.step.text||"选择对话分支"}</p></div><ChevronRight size={15}/></button>)}</div>}
   {drawer==="settings"&&<div className="settings">
    <div className="setting-row"><div><b>逐字显示台词</b><p>点击补全，再点击推进剧情</p></div><button className={"switch "+(typing?"on":"")} aria-label="逐字显示台词" aria-pressed={typing} onClick={()=>setTyping(t=>!t)}><span/></button></div>
    <label className="slider-setting"><span>配音音量 <b>{Math.round(volume*100)}%</b></span><input type="range" min="0" max="1" step=".05" value={volume} onChange={e=>setVolume(+e.target.value)}/></label>
    <label className="slider-setting"><span>播放速度 <b>{rate.toFixed(1)}×</b></span><input type="range" min=".7" max="1.5" step=".1" value={rate} onChange={e=>setRate(+e.target.value)}/></label>
    <div className="info-box"><Keyboard size={18}/><div><b>键盘操作</b><p>空格 / → 推进台词<br/>A 开关自动播放 · H 打开回顾<br/>Esc 关闭面板</p></div></div>
    <div className="info-box"><Headphones size={18}/><div><b>{backend.connected?"角色语音服务已配置":"角色语音服务待连接"}</b><p>默认按角色配音；在录音室选用自己的声音后，所有台词与旁白统一朗读。随身听遇到选项或段落结束时等待确认。</p><button className="text-button" onClick={()=>setDrawer("studio")}>打开音色工作室 <ChevronRight size={14}/></button></div></div>
   </div>}
   {drawer==="studio"&&<><ReaderStudio backend={backend} selected={readerVoice} onSelect={selectReaderVoice}/>{backend.admin&&<details className="admin-voices"><summary>管理员 · 预设角色与默认声音</summary><Studio backend={backend} onPublished={()=>api("voices").then(j=>setVoices(j.voices||[]))}/></details>}</>}
  </aside></div>}
 </main>;
}
function Studio({backend,onPublished}:any){
 const [defaults,setDefaults]=useState<any>({female:null,male:null,narrator:null});
 const [characters,setCharacters]=useState<any[]>([]),[name,setName]=useState(""),[selected,setSelected]=useState<any>(null),[status,setStatus]=useState(""),[busy,setBusy]=useState(false),[job,setJob]=useState<any>(null),[preview,setPreview]=useState("博士，准备好继续我们的旅程了吗？"),[sampleTexts,setSampleTexts]=useState<Record<string,string>>({}),[mode,setMode]=useState("reference");
 const file=useRef<HTMLInputElement>(null),previewAudio=useRef<HTMLAudioElement|null>(null);
 const refresh=useCallback(async()=>{if(!backend.admin||!backend.connected)return;try{const [j,d]=await Promise.all([api("admin/characters"),api("admin/defaults")]);setCharacters(j.characters);setDefaults(d.defaults);setSelected((old:any)=>j.characters.find((x:any)=>x.id===old?.id)||j.characters[0]||null);}catch(e){setStatus((e as Error).message);}},[backend]);
 useEffect(()=>{refresh();return()=>{previewAudio.current?.pause();};},[refresh]);
 useEffect(()=>{if(!job||!["queued","running"].includes(job.state))return;const id=setInterval(()=>api("admin/jobs/"+job.id).then(j=>{setJob(j);if(["done","failed"].includes(j.state)){refresh();setStatus(j.state==="done"?"任务完成，可试听并发布音色":j.error||"任务失败");}}).catch(e=>setStatus(e.message)),1500);return()=>clearInterval(id);},[job,refresh]);
 async function run(action:()=>Promise<any>){setBusy(true);setStatus("");try{await action();}catch(e){setStatus((e as Error).message);}finally{setBusy(false);}}
 const post=(path:string,data:any)=>api(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
 return <div className="studio">
  <div className="studio-intro"><div className="studio-icon"><Mic2 size={25}/></div><div><h3>每一个角色，都有自己的声音</h3><p>导入游戏语音或上传短录音，即可建立免训练音色。</p></div></div>
  {!backend.connected?<div className="empty-state"><Cloud size={35}/><h3>连接语音服务器后，即可开始</h3><p>网站已准备好阅读与播放界面。免训练声音克隆也需要语音合成服务。使用一小段参考录音即可，无需逐个角色训练。</p><div className="studio-steps"><span>01 导入参考语音</span><span>02 免训练试听</span><span>03 发布音色</span></div><small>当前尚未连接，因此不会显示虚构的训练进度或角色音色。</small></div>:!backend.admin?<div className="empty-state"><Mic2 size={35}/><h3>音色由管理员统一维护</h3><p>普通读者可直接使用已经发布的音色，无需上传素材或训练。</p>{!backend.userId&&<a className="primary" style={{marginTop:20}} href="/signin-with-chatgpt?return_to=/" target="_top">管理员登录</a>}{backend.userId&&<details><summary>站点管理员配置</summary><p>将以下标识设置为服务端 STUDIO_ADMIN_USER_ID：</p><code>{backend.userId}</code></details>}</div>:<>
   <section className="default-voices"><h3>全站默认声音</h3><p>未设置专属音色的角色自动使用默认男女声，旁白单独指定。读者无需配置。</p>{[["female","默认女声"],["male","默认男声"],["narrator","旁白声音"]].map(([role,label])=><label key={role}><span>{label}</span><select aria-label={label} value={defaults[role]||""} onChange={e=>setDefaults((d:any)=>({...d,[role]:e.target.value||null}))}><option value="">{role==="narrator"?"跟随默认女声":"系统声音"}</option>{characters.filter(c=>c.published).map(c=><option key={c.id} value={c.id}>{c.speaker}</option>)}</select></label>)}<button className="primary" disabled={busy} onClick={()=>run(async()=>{await post("admin/defaults",defaults);onPublished();setStatus("站点默认音色已更新，读者自动使用。");})}><Check size={15}/>保存默认声音</button></section>
   <form className="new-character" onSubmit={e=>{e.preventDefault();run(async()=>{const j=await post("admin/characters",{speaker:name});setName("");await refresh();setSelected(j);});}}><input aria-label="角色名称" placeholder="输入角色名，如：阿米娅" value={name} onChange={e=>setName(e.target.value)} maxLength={40}/><button className="primary" type="button" disabled={busy||!name.trim()} onClick={()=>run(async()=>{setStatus("正在查找并导入参考语音…");const c=await post("admin/import-operator",{name:name.trim()});await refresh();setSelected(c);setMode("reference");setStatus("游戏参考语音已导入，文字已匹配，可直接试听。");})}>导入干员语音</button><button type="submit" disabled={busy||!name.trim()}>手动创建</button></form>
   <div className="character-tabs">{characters.map(c=><button key={c.id} className={selected?.id===c.id?"selected":""} onClick={()=>{setSelected(c);setSampleTexts({});}}>{c.speaker}<span>{c.published?"已发布":c.hasReference?"可直接试听":"待参考语音"}</span></button>)}</div>
   {selected&&<div className="character-workspace"><div className="character-title"><h3>{selected.speaker}</h3><span>{selected.clips?.length||0} 段录音 · {(selected.clips||[]).reduce((s:number,c:any)=>s+c.duration,0).toFixed(1)} 秒</span></div>
    <input type="file" ref={file} hidden multiple accept="audio/*,.wav,.mp3,.flac,.m4a" onChange={e=>{const files=Array.from(e.target.files||[]);run(async()=>{for(const f of files){if(f.size>50*1024*1024)throw Error("单个文件不能超过 50 MB");await api("admin/upload?character="+encodeURIComponent(selected.id)+"&filename="+encodeURIComponent(f.name),{method:"POST",headers:{"Content-Type":f.type||"application/octet-stream"},body:f});}await refresh();setStatus("上传完成，请转写并校对录音文本。");});e.target.value="";}}/>
    <button className="upload-zone" disabled={busy} onClick={()=>file.current?.click()}><Upload size={25}/><b>上传参考语音</b><span>WAV / MP3 / FLAC / M4A · 单文件最多 50 MB</span><small>准备一段 3–10 秒清晰语音及其文字，即可免训练试听。</small></button>
    <div className="studio-actions"><button disabled={busy||!selected.clips?.length} onClick={()=>run(async()=>setJob(await post("admin/transcribe",{id:selected.id})))}><RefreshCw size={15}/>自动转写</button></div>
    <div className="sample-list">{selected.clips?.map((c:any)=><div key={c.id}><span>{c.duration.toFixed(1)}s</span><input aria-label="录音转写文本" value={sampleTexts[c.id]??c.text??""} placeholder="录音对应的文字，请校对后保存" onChange={e=>setSampleTexts(s=>({...s,[c.id]:e.target.value}))}/><button disabled={busy} onClick={()=>run(async()=>{await post("admin/transcript",{id:selected.id,clipId:c.id,text:sampleTexts[c.id]??c.text});await refresh();})}>保存</button></div>)}</div>
    <label className="mode-setting">音色方式<select value={mode} onChange={e=>setMode(e.target.value)}><option value="reference">免训练 · 参考语音克隆（推荐）</option><option value="trained" disabled={!selected.models}>使用已训练的角色模型</option></select></label><label className="preview-input">试听台词<textarea value={preview} onChange={e=>setPreview(e.target.value)} maxLength={300}/></label>
    <div className="studio-actions"><button disabled={busy||!selected.hasReference||(mode==="trained"&&!selected.models)} onClick={()=>run(async()=>{const r=await fetch("/api/voice/admin/preview",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:selected.id,text:preview,mode})});if(!r.ok)throw Error((await r.json() as any).error);const url=URL.createObjectURL(await r.blob());previewAudio.current?.pause();const a=new Audio(url);previewAudio.current=a;a.onended=()=>URL.revokeObjectURL(url);await a.play();})}><Headphones size={15}/>试听</button><button className="primary" disabled={busy||!selected.hasReference||(mode==="trained"&&!selected.models)} onClick={()=>run(async()=>{await post("admin/publish",{id:selected.id,mode});await refresh();onPublished();setStatus("音色已发布，读者可以直接使用，无需自行训练。");})}><Check size={15}/>发布音色</button></div>
    <details className="optional-training"><summary>进阶音色优化 · 可选训练</summary><p>参考音色不够理想时，再考虑训练。需要至少 30 秒已校对的清晰素材。</p><button disabled={busy||!selected.clips?.length} onClick={()=>run(async()=>setJob(await post("admin/train",{id:selected.id,epochs:2})))}><Play size={15}/>开始训练</button></details>
   </div>}
  </>}
  {job&&<div className="job"><b>{job.message||job.state}</b><progress max="100" value={job.progress||0}/><small>{job.state==="failed"?job.error:"训练完成后，需要试听并手动发布。"} </small></div>}
  {busy&&<p className="status"><LoaderCircle className="spin" size={15}/>正在处理…</p>}{status&&<p className="status" role="status">{status}</p>}
 </div>;
}
