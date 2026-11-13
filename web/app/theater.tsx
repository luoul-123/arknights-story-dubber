"use client";
import {useCallback,useEffect,useRef,useState} from "react";
import {BookOpen,Settings2,Volume2,VolumeX,Play,Pause,History,ChevronLeft,ChevronRight,X,Maximize,Minimize,Headphones,Mic2,Check,RefreshCw,LoaderCircle,SkipForward,Triangle,Save} from "lucide-react";
import StoryArchive from "./story-archive";
import StoryMusic from "./story-music";
import ReadingVoiceSettings from "./reading-voice-settings";
import {DialogueAudio,resolveVoice} from "../lib/audio.mjs";
import {nextIndex,nextChapter,previousStep,resolveScene,MEDIA_ROOT} from "../lib/story.mjs";
type Scene={background:string|null;cg:string|null;actors:{key:string;url:string}[];focus:number};
type Step={id:string;type:string;text?:string;speaker?:string;route:string[]|null;choices?:{label:string;value:string}[];scene:Scene};
type Chapter={id:string;title:string;code:string;tag:string};
type Group={id:string;title:string;chapters:Chapter[]};
type Voice={id:string;speaker:string;version:string;aliases?:string[];kind?:string};
const FIRST:Chapter={id:"obt/main/level_main_00-01_beg",title:"坍塌",code:"0-1",tag:"行动前"};
const BG=MEDIA_ROOT+"backgrounds/bg_cher_1.png";
function IconButton({label,onClick,active=false,children}:any){return <button className={"icon-button "+(active?"active":"")} title={label} aria-label={label} onClick={onClick}>{children}</button>;}
async function api(path:string,options?:RequestInit):Promise<any>{const r=await fetch("/api/voice/"+path,options);const j:any=await r.json();if(!r.ok)throw Error(j.error||"操作失败");return j;}
function Actor({actor,focus,total}:any){const [failed,setFailed]=useState(false);useEffect(()=>setFailed(false),[actor.key]);if(failed)return null;return <img alt="" className={"actor "+(focus?"focused":"dimmed")+" "+(total===1?"solo":"")+" actor-slot-"+(actor.slot||"m")} style={{opacity:actor.opacity,translate:actor.offset?actor.offset[0]+"px "+(-actor.offset[1])+"px":undefined,scale:actor.scale}} src={actor.url} onError={()=>setFailed(true)}/>;}
export default function Theater(){
 const [chapter,setChapter]=useState<Chapter>(FIRST),[steps,setSteps]=useState<Step[]>([]),[index,setIndex]=useState(0),[choice,setChoice]=useState<string|null>(null),[decisions,setDecisions]=useState<Record<string,string>>({});
 const [catalog,setCatalog]=useState<Group[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState(""),[drawer,setDrawer]=useState<string|null>(null);
 const [history,setHistory]=useState<{index:number;step:Step;choice:string|null}[]>([]),[typing,setTyping]=useState(true),[shown,setShown]=useState(0);
 const [readerVoice,setReaderVoice]=useState<Voice|null>(null);
 const selectReaderVoice=(voice:Voice|null)=>{setReaderVoice(voice);localStorage.setItem("terra-preset-voice",voice?.id||"");};
 const [listening,setListening]=useState(false);const listeningRef=useRef(false),moveRef=useRef<()=>void>(()=>{}),backRef=useRef<()=>void>(()=>{});
 const [auto,setAuto]=useState(false),[muted,setMuted]=useState(false),[musicVolume,setMusicVolume]=useState(.35),[volume,setVolume]=useState(.85),[rate,setRate]=useState(1);
 const [voices,setVoices]=useState<Voice[]>([]),[voiceStatus,setVoiceStatus]=useState("idle"),[voiceError,setVoiceError]=useState("");
 const [started,setStarted]=useState(false),[ended,setEnded]=useState(false),[full,setFull]=useState(false),[saved,setSaved]=useState<any>(null),[toast,setToast]=useState("");
 const chapterEpoch=useRef(0);
 const player=useRef<any>(null),advanceRef=useRef<()=>void>(()=>{}),stage=useRef<HTMLDivElement>(null);
 const step=steps[index],text=step?.text||"",characters=Array.from(text),complete=!typing||shown>=characters.length;
 useEffect(()=>{player.current=new DialogueAudio({onState:(state:string,msg?:string)=>{setVoiceStatus(state);setVoiceError(msg||"");if("mediaSession" in navigator)navigator.mediaSession.playbackState=state==="playing"?"playing":state==="paused"?"paused":"none";}});return()=>{player.current?.dispose();window.speechSynthesis?.cancel();};},[]);
 useEffect(()=>{
  try{const s=JSON.parse(localStorage.getItem("terra-manual-save")||localStorage.getItem("zhousheng-progress")||"null");if(s)setSaved(s);const settings=JSON.parse(localStorage.getItem("zhousheng-settings")||"null");if(settings){setTyping(settings.typing??true);setVolume(settings.volume??.85);setMusicVolume(settings.musicVolume??.35);}}catch{}
  fetch("/api/stories?catalog=2").then(r=>{if(!r.ok)throw Error();return r.json() as Promise<Group[]>;}).then(setCatalog).catch(()=>{});
  api("voices").then(j=>{setVoices(j.voices||[]);const chosen=j.voices?.find((v:Voice)=>v.id===localStorage.getItem("terra-preset-voice"))||j.voices?.find((v:Voice)=>v.speaker==="阿米娅");if(chosen)setReaderVoice(chosen);}).catch(e=>setVoiceError(e.message));
 },[]);
 useEffect(()=>{localStorage.setItem("zhousheng-settings",JSON.stringify({typing,volume,musicVolume}));},[typing,volume,musicVolume]);
 const loadChapter=useCallback(async(c:Chapter,resume?:any)=>{
  const requestId=++chapterEpoch.current;player.current?.stop();window.speechSynthesis?.cancel();setStarted(false);setLoading(true);setError("");setEnded(false);setHistory([]);setChapter(c);setSteps([]);
  try{const r=await fetch("/api/stories?media=2&id="+encodeURIComponent(c.id));const j:any=await r.json();if(requestId!==chapterEpoch.current)return;if(!r.ok)throw Error(j.error);if(!j.steps.length)throw Error("本章暂时没有可读取的台词");setSteps(j.steps);setIndex(Math.min(resume?.index||0,j.steps.length-1));setChoice(resume?.choice||null);setDecisions(resume?.decisions||{});if(listeningRef.current)setStarted(true);}
  catch(e){if(requestId===chapterEpoch.current)setError((e as Error).message||"章节加载失败");}finally{if(requestId===chapterEpoch.current)setLoading(false);}
 },[]);
 useEffect(()=>{let resume=null;try{resume=JSON.parse(localStorage.getItem("terra-manual-save")||localStorage.getItem("zhousheng-progress")||"null");}catch{}loadChapter(resume?.chapter||FIRST,resume);},[loadChapter]);
 useEffect(()=>{setShown(0);if(!step||!typing)return;const timer=setInterval(()=>setShown(n=>Math.min(n+1,Array.from(step.text||"").length)),30);return()=>clearInterval(timer);},[step?.id,typing]);
 useEffect(()=>{if(!step||loading||!started)return;const data={chapter,index,choice,decisions,time:Date.now()};localStorage.setItem("zhousheng-progress",JSON.stringify(data));},[chapter,index,choice,decisions,step,loading,started]);
 useEffect(()=>{player.current?.setOptions({volume,rate});},[volume,rate]);
 const voiceFor=useCallback((line:Step)=>resolveVoice(voices,line,readerVoice),[voices,readerVoice]);
 const playCurrent=useCallback(()=>{
  if(!step||step.type!=="line"||ended)return;
  player.current?.stop();window.speechSynthesis?.cancel();setVoiceError("");
  if(!started||muted){setVoiceStatus("silent");return;}
  const voice=voiceFor(step);
  if(voice){const playback=player.current.play(step,voice,{onEnd:()=>{if(listeningRef.current)moveRef.current();}});const ni=nextIndex(steps,index,choice);if(ni>=0&&steps[ni].type==="line"){const nv=voiceFor(steps[ni]);if(nv){const active=player.current,generation=active.generation;playback.then(()=>setTimeout(()=>{if(active===player.current&&active.generation===generation&&active.current&&!active.paused)active.prefetch(steps[ni],nv);},800));}}return;}
  setVoiceStatus("unavailable");
 },[step,started,muted,voiceFor,steps,index,choice,ended]);
 useEffect(()=>{playCurrent();return()=>{player.current?.stop();window.speechSynthesis?.cancel();};},[playCurrent]);
 const move=useCallback((selected?:string)=>{
  if(!step)return;if(step.type==="choice"&&!selected)return;
  player.current?.stop();window.speechSynthesis?.cancel();
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
 const previous=history[history.length-1]||previousStep(steps,index,decisions);
 const back=()=>{const item=previous;if(!item)return;setHistory(h=>h.slice(0,-1));setIndex(item.index);setChoice(item.choice);setEnded(false);};
 backRef.current=back;
 const openDrawer=(name:string)=>{setDrawer(name);if(!listeningRef.current){setAuto(false);player.current?.pause();}};
 const scene=step?resolveScene(steps,index,decisions):null;
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
  <StoryMusic music={scene?.music} volume={musicVolume*(scene?.musicVolume??1)} active={started&&!loading&&!ended&&!(listening&&voiceStatus==="paused")}/>
  <div className="scene" onClick={advance} aria-hidden="true">
   <img key={scene?.background||"blank"} className="background" style={{opacity:started&&!scene?.background?0:undefined}} src={scene?.background||BG} alt="" onError={e=>{e.currentTarget.style.opacity="0";}}/>
   <div className="scene-shade"/>
   {!scene?.cg&&<div className="actors">{scene?.actors?.map((actor,i)=><Actor key={actor.key+i} actor={actor} focus={scene.focus<0||scene.focus===i} total={scene.actors.length}/>)}</div>}
   {scene?.cg&&<img key={scene.cg} className="cg" src={scene.cg} alt="剧情 CG" onError={e=>{e.currentTarget.style.opacity="0";}}/>}
   <div className="scene-grain"/><div className="vignette"/>
  </div>
  <header className="topbar">
   <button className="brand" onClick={()=>openDrawer("chapters")}><span className="brand-mark"><Triangle size={23}/><span/></span><b>泰拉之声</b><span className="brand-en">VOICES OF TERRA</span></button>
   <div className="chapter-heading"><span>{catalog.find(g=>g.chapters.some(c=>c.id===chapter.id))?.title||"剧情档案"}</span><span className="divider"/><b>{chapter.code} · {chapter.title}</b><span className="tag">{chapter.tag}</span></div>
   <div className="top-actions"><button className={"listen-toggle "+(listening?"active":"")} onClick={toggleListening}><Headphones size={16}/><span>{listening?"随身听中":"随身听"}</span></button><a className="icon-button" aria-label="GitHub 项目" href="https://github.com/luoul-123/arknights-story-dubber" target="_blank" rel="noreferrer"><svg width="19" height="19" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .5a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2.1c-3.3.7-4-1.4-4-1.4-.5-1.4-1.3-1.8-1.3-1.8-1.1-.8.1-.8.1-.8 1.2.1 1.8 1.2 1.8 1.2 1.1 1.9 2.8 1.4 3.5 1.1.1-.8.4-1.4.8-1.7-2.7-.3-5.5-1.4-5.5-6a4.7 4.7 0 0 1 1.2-3.2c-.1-.3-.5-1.6.1-3.3 0 0 1-.3 3.3 1.2a11.4 11.4 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.7.2 3 .1 3.3a4.7 4.7 0 0 1 1.2 3.2c0 4.6-2.8 5.7-5.5 6 .4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .5Z"/></svg></a><IconButton label="章节目录" onClick={()=>openDrawer("chapters")}><BookOpen size={19}/></IconButton><IconButton label="朗读音色设置" onClick={()=>openDrawer("studio")}><Mic2 size={19}/></IconButton><IconButton label="阅读设置" onClick={()=>openDrawer("settings")}><Settings2 size={19}/></IconButton></div>
  </header>
  <aside className="scene-meta"><span className="tiny-cross">+</span><span>RHODES ISLAND</span><div/><span>STORY ARCHIVE / {chapter.code}</span></aside>
  {loading&&<div className="center-card loading"><LoaderCircle className="spin" size={27}/><h2>正在打开泰拉的故事</h2><p>加载章节与演出资源</p></div>}
  {error&&<div className="center-card"><h2>这一页暂时没有打开</h2><p>{error}</p><button className="primary" onClick={()=>loadChapter(chapter)}><RefreshCw size={16}/>重新加载</button><button onClick={()=>openDrawer("chapters")}>选择其他章节</button></div>}
  {!loading&&!error&&!started&&<div className="entry-overlay"><div className="entry-copy"><span className="eyebrow">ARKNIGHTS · VOICED STORY THEATER</span><h1>让故事，<br/>有声而至<span>。</span></h1><p>重返泰拉。在每一次相遇里，听见他们的声音。</p><div className="entry-actions"><button className="primary" onClick={()=>setStarted(true)}><Play size={17} fill="currentColor"/>进入剧情<span>{chapter.code} / {chapter.title}</span></button>{saved&&<button className="text-button" onClick={()=>loadChapter(saved.chapter,saved).then(()=>setStarted(true))}>继续上次阅读 <ChevronRight size={15}/></button>}</div><span className="entry-foot"><Headphones size={14}/>角色、NPC 与旁白自动配音 · 无需配置</span></div><div className="entry-number">00<span>黑暗时代</span></div></div>}
  {started&&step?.type==="choice"&&!ended&&<div className="choice-panel"><span className="eyebrow">博士，你的选择</span>{step.choices?.map((c,i)=><button key={c.value+i} onClick={()=>move(c.value)}><span>0{i+1}</span>{c.label}<ChevronRight size={17}/></button>)}</div>}
  {ended&&<div className="center-card chapter-complete"><span className="eyebrow">TO BE CONTINUED</span><h2>本段故事已读完</h2>{nextSection?<><p>下一段：{nextSection.code} · {nextSection.title}<br/><span>{nextSection.tag}</span></p><button className="primary" onClick={continueSection}>继续下一段 <ChevronRight size={17}/></button></>:<p>这一系列暂时读完了，去探索其他故事吧。</p>}<button onClick={()=>openDrawer("chapters")}>打开剧情档案</button><button onClick={()=>{setEnded(false);back();}}>返回上一句</button></div>}
  {started&&!loading&&!error&&step?.type==="line"&&!ended&&<section className="dialogue-shell" aria-label="剧情对话">
   <div className="dialogue-header"><div className="speaker-rule"/><h2>{step.speaker||"旁白"}</h2></div>
   <button className="dialogue-text" onClick={advance} aria-label={complete?"下一句":"显示完整台词"}><span>{typing?characters.slice(0,shown).join(""):text}</span><span className="advance-glyph">{complete?<Triangle size={11} fill="currentColor"/>:<span className="typing-cursor"/>}</span></button>
   <div className="dialogue-bottom"><span className="line-number">{String(index+1).padStart(3,"0")} <span>/ {String(steps.length).padStart(3,"0")}</span></span>{voiceError&&<span className="click-hint" role="alert">{voiceError}</span>}</div>
  </section>}
  <footer className="controlbar">
   <div className="control-left"><button onClick={()=>openDrawer("chapters")}><BookOpen size={16}/>目录</button><span className="control-sep"/><button onClick={()=>openDrawer("history")}><History size={16}/>回顾</button><button disabled={loading||!step} onClick={()=>{const snapshot={chapter,index,choice,decisions,time:Date.now()};localStorage.setItem("terra-manual-save",JSON.stringify(snapshot));setSaved(snapshot);setToast("存档已保存在此浏览器，刷新后可继续");}}><Save size={16}/>存档</button></div>
   <div className="control-center"><button className="chapter-nav-button" aria-label="上一句" title="返回上一句" disabled={loading||!previous} onClick={back}><ChevronLeft size={21}/><small>上一句</small></button><button className={"auto-button "+(auto?"active":"")} onClick={()=>{if(listening){if(voiceStatus==="paused")player.current.resume();else player.current.pause();}else{if(!started)setStarted(true);setAuto(a=>!a);}}}>{(listening?voiceStatus!=="paused":auto)?<Pause size={14}/>:<Play size={14}/>}<span className="play-label">{listening?(voiceStatus==="paused"?"播放":"暂停"):"自动"}</span><span>{listening?"LISTEN":"AUTO"}</span></button><button className="chapter-nav-button" aria-label="下一章" title={nextSection?"下一章："+nextSection.code+" · "+nextSection.title+" · "+nextSection.tag:"没有下一章"} disabled={loading||!nextSection} onClick={continueSection}><small>下一章</small><SkipForward size={19}/></button></div>
   <div className="control-right"><IconButton label={muted?"开启配音":"静音"} active={!muted} onClick={()=>setMuted(m=>!m)}>{muted?<VolumeX size={18}/>:<Volume2 size={18}/>}</IconButton><span className="control-sep"/><IconButton label="全屏" onClick={fullScreen}>{full?<Minimize size={17}/>:<Maximize size={17}/>}</IconButton></div>
  </footer>
  <div className="progress-track"><div style={{width:steps.length?((index+1)/steps.length*100)+"%":"0"}}/></div>
  {listening&&started&&<div className="listen-badge"><Headphones size={13}/>{ended?"本节播放完毕":step?.type==="choice"?"等待你的选择":voiceStatus==="error"?"播放遇到问题，请重试":voiceStatus==="paused"?"已暂停":voiceStatus==="loading"?"正在准备下一句":"随身听 · 可切换到后台"}</div>}
  {toast&&<div className="toast"><Check size={16}/>{toast}</div>}
  {drawer&&<div className="drawer-backdrop" onClick={()=>setDrawer(null)}><aside className={"drawer "+(drawer==="studio"?"studio-drawer":"")} onClick={e=>e.stopPropagation()}>
   <div className="drawer-head"><div><span className="eyebrow">{drawer==="studio"?"READING VOICE":drawer==="chapters"?"STORY ARCHIVE":drawer==="history"?"BACKLOG":"PREFERENCES"}</span><h2>{{chapters:"剧情档案",studio:"朗读音色设置",history:"对话回顾",settings:"阅读设置"}[drawer]}</h2></div><IconButton label="关闭面板" onClick={()=>setDrawer(null)}><X size={21}/></IconButton></div>
   {listening&&started&&<div className="drawer-player"><Headphones size={17}/><div><b>{ended?"本段播放完毕":step?.type==="choice"?"等待剧情选择":voiceStatus==="paused"?"收听已暂停":"正在收听"} · {chapter.code}</b><span>{step?.speaker||"旁白"} · {text.slice(0,32)}</span></div><button aria-label={voiceStatus==="paused"?"继续随身听":"暂停随身听"} onClick={()=>voiceStatus==="paused"?player.current?.resume():player.current?.pause()}>{voiceStatus==="paused"?<Play size={16}/>:<Pause size={16}/>}</button>{ended&&nextSection&&<button aria-label="确认进入下一段" onClick={continueSection}><ChevronRight size={17}/></button>}<button aria-label="随身听下一句" onClick={()=>move()}><SkipForward size={17}/></button></div>}
   {drawer==="chapters"&&<StoryArchive groups={catalog} currentId={chapter.id} onSelect={(c:Chapter)=>{setDrawer(null);loadChapter(c);}} onRetry={()=>fetch("/api/stories?catalog=2").then(r=>r.json()).then(j=>Array.isArray(j)&&setCatalog(j))}/>}
   {drawer==="history"&&<div className="backlog">{!history.length?<p className="muted">读过的台词会出现在这里。</p>:history.map((h,i)=><button key={i} onClick={()=>{setIndex(h.index);setChoice(h.choice);setHistory(old=>old.slice(0,i));setEnded(false);setDrawer(null);}}><span>{String(h.index+1).padStart(3,"0")}</span><div><b>{h.step.speaker||"博士的选择"}</b><p>{h.step.text||"选择对话分支"}</p></div><ChevronRight size={15}/></button>)}</div>}
   {drawer==="settings"&&<div className="settings">
    <div className="setting-row"><div><b>逐字显示台词</b><p>点击补全，再点击推进剧情</p></div><button className={"switch "+(typing?"on":"")} aria-label="逐字显示台词" aria-pressed={typing} onClick={()=>setTyping(t=>!t)}><span/></button></div>
    <label className="slider-setting"><span>背景音乐音量 <b>{Math.round(musicVolume*100)}%</b></span><input aria-label="背景音乐音量" type="range" min="0" max="1" step=".05" value={musicVolume} onChange={e=>setMusicVolume(+e.target.value)}/></label>
    <label className="slider-setting"><span>配音音量 <b>{Math.round(volume*100)}%</b></span><input type="range" min="0" max="1" step=".05" aria-label="配音音量" value={volume} onChange={e=>setVolume(+e.target.value)}/></label>
    <label className="slider-setting"><span>播放速度 <b>{rate.toFixed(1)}×</b></span><input type="range" min=".7" max="1.5" step=".1" aria-label="播放速度" value={rate} onChange={e=>setRate(+e.target.value)}/></label>
    <details className="developer-log"><summary>开发者日志</summary><ol><li><time>2026-11-13</time><p>新增阿米娅音色语音包</p></li><li><time>2026-11-13</time><p>新增预设朗读音色选择，精简阅读界面。</p></li><li><time>2026-11-13</time><p>优化连续跳句请求，修复立绘差分、背景音乐及存档恢复。</p></li><li><time>2026-11-13</time><p>底部导航新增上一句、下一章说明，支持按目录顺序切换章节。</p></li></ol></details>
   </div>}
   {drawer==="studio"&&<><ReadingVoiceSettings voices={voices} selected={readerVoice} onSelect={selectReaderVoice}/></>}
  </aside></div>}
 </main>;
}
