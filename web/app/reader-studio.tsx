"use client";
import {useEffect,useRef,useState} from "react";
import {Upload,Headphones,LoaderCircle,Check,Mic2} from "lucide-react";
async function request(path:string,options?:RequestInit){const response=await fetch("/api/voice/reader/"+path,options);const result:any=await response.json();if(!response.ok)throw Error(result.error||"操作失败");return result;}
export default function ReaderStudio({backend,selected,onSelect}:any){
 const [profile,setProfile]=useState<any>({voice:null,draft:null}),[text,setText]=useState(""),[busy,setBusy]=useState(false),[message,setMessage]=useState("");
 const input=useRef<HTMLInputElement>(null),audio=useRef<HTMLAudioElement|null>(null),objectUrl=useRef("");
 useEffect(()=>{if(backend.connected&&backend.userId)request("voice").then(p=>{setProfile(p);setText(p.draft?.text||"");}).catch(e=>setMessage(e.message));return()=>{audio.current?.pause();if(objectUrl.current)URL.revokeObjectURL(objectUrl.current);};},[backend.connected,backend.userId]);
 const run=async(action:()=>Promise<void>)=>{setBusy(true);setMessage("");try{await action();}catch(e){setMessage((e as Error).message);}finally{setBusy(false);}};
 return <section className="reader-studio">
  <div className="studio-intro"><div className="studio-icon"><Mic2 size={25}/></div><div><h3>让故事，用你选的声音讲述</h3><p>上传一段短录音，整篇台词与旁白都用这个声音朗读。</p></div></div>
  <div className="reading-modes" role="group" aria-label="朗读声音模式"><button className={!selected?"selected":""} aria-pressed={!selected} onClick={()=>onSelect(null)}><b>默认角色配音</b><span>重要角色使用预设声线，其他角色用默认男女声。</span></button><button className={selected?"selected":""} aria-pressed={!!selected} disabled={!profile.voice} onClick={()=>onSelect(profile.voice)}><b>我的统一朗读声</b><span>{profile.voice?"所有角色和旁白都用上传的声音。":"上传录音后即可选用。"}</span></button></div>
  {!backend.connected?<p className="info-box">朗读服务连接后即可上传录音。</p>:!backend.userId?<a className="primary" href="/signin-with-chatgpt?return_to=/">登录后设置我的声音</a>:<>
   <input ref={input} type="file" hidden accept="audio/*,.wav,.mp3,.m4a,.flac" onChange={e=>{const file=e.target.files?.[0];e.target.value="";if(!file)return;run(async()=>{if(file.size>10*1024*1024)throw Error("录音不能超过 10 MB");const p=await request("upload",{method:"POST",headers:{"Content-Type":file.type||"application/octet-stream"},body:file});setProfile(p);setText(p.draft?.text||"");setMessage(p.draft?.notice||"录音已识别，确认原话后即可选用。");});}}/>
   <button className="upload-zone" disabled={busy} onClick={()=>input.current?.click()}>{busy?<LoaderCircle size={25} className="spin"/>:<Upload size={25}/>}<b>{busy?"正在识别录音…":"上传我的参考录音"}</b><span>3–10 秒 · 清晰、完整的一句话 · 最大 10 MB</span><small>无需训练。只用于你的朗读设置，不改变其他读者的声音。</small></button>
   {profile.draft&&<div className="reader-transcript"><label>录音里说的原话<textarea aria-label="我的录音原话" value={text} onChange={e=>setText(e.target.value)} maxLength={500}/></label><p>已自动识别，若有错字请修正。无需填写剧情台词。</p><button className="primary" disabled={busy||!text.trim()} onClick={()=>run(async()=>{const p=await request("voice",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});setProfile(p);onSelect(p.voice);setMessage("已选用：全部角色和旁白统一使用这个声音。");})}><Check size={16}/>用这个声音朗读全部文本</button></div>}
   {profile.voice&&<button className="reader-preview" disabled={busy} onClick={()=>run(async()=>{const response=await fetch("/api/voice/speech",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({voiceId:profile.voice.id,version:profile.voice.version,text:"欢迎来到泰拉之声，让我们继续这段旅程。"})});if(!response.ok)throw Error((await response.json() as any).error);audio.current?.pause();if(objectUrl.current)URL.revokeObjectURL(objectUrl.current);objectUrl.current=URL.createObjectURL(await response.blob());audio.current=new Audio(objectUrl.current);await audio.current.play();})}><Headphones size={16}/>试听我的声音</button>}
  </>}
  {message&&<p className="status" role="status">{message}</p>}
 </section>;
}
