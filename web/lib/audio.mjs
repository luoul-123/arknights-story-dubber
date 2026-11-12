// Last selection wins, even if an older synthesis request completes late.
export class DialogueAudio {
 constructor({fetcher=(...args)=>globalThis.fetch(...args),makeAudio=()=>new Audio(),onState=()=>{}}={}){
  this.fetcher=fetcher;this.makeAudio=makeAudio;this.onState=onState;this.generation=0;this.cache=new Map();this.pending=new Map();this.current=null;this.element=null;this.paused=false;this.volume=1;this.rate=1;
 }
 stop(){this.paused=false;this.generation++;if(this.current){this.current.pause();this.current.removeAttribute?.("src");this.current.load?.();this.current=null;}this.controller?.abort();this.onState("idle");}
 key(line,voice){return [line.text,line.speaker,voice?.id,voice?.version].join("|");}
 async load(line,voice,signal){
  const key=this.key(line,voice);
  if(this.cache.has(key))return this.cache.get(key);
  const response=await this.fetcher("/api/voice/speech",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:line.text,speaker:line.speaker||"",voiceId:voice.id,version:voice.version}),signal});
  if(!response.ok){const j=await response.json().catch(()=>({}));throw Error(j.error||"配音生成失败");}
  const url=URL.createObjectURL(await response.blob());this.cache.set(key,url);
  if(this.cache.size>24){const first=this.cache.keys().next().value;if(first!==key){URL.revokeObjectURL(this.cache.get(first));this.cache.delete(first);}}
  return url;
 }
 setOptions({volume=this.volume,rate=this.rate}={}){this.volume=volume;this.rate=rate;if(this.current){this.current.volume=volume;this.current.playbackRate=rate;}}
 async play(line,voice,{volume=this.volume,rate=this.rate,onEnd=()=>{}}={}){
  this.setOptions({volume,rate});this.stop();const generation=this.generation;this.controller=new AbortController();this.onState("loading");
  try{
   const url=await this.load(line,voice,this.controller.signal);if(generation!==this.generation)return;
   const audio=this.element||(this.element=this.makeAudio());this.current=audio;audio.src=url;audio.volume=this.volume;audio.playbackRate=this.rate;
   audio.onended=()=>{if(generation===this.generation){this.onState("ended");onEnd();}};
   audio.onerror=()=>{if(generation===this.generation)this.onState("error","音频播放失败");};
   if(this.paused){this.onState("paused");return;}await audio.play();if(generation===this.generation)this.onState("playing");
  }catch(e){if(generation===this.generation&&e.name!=="AbortError")this.onState("error",e.message);}
 }
 pause(){this.paused=true;this.current?.pause();this.onState("paused");}
 async resume(){this.paused=false;if(this.current){try{await this.current.play();this.onState("playing");}catch(e){this.onState("error",e.message);}}}
 async prefetch(line,voice){if(!line||!voice)return;const key=this.key(line,voice);if(this.cache.has(key)||this.pending.has(key))return;this.pending.set(key,true);try{await this.load(line,voice);}catch{}finally{this.pending.delete(key);}}
 dispose(){this.stop();for(const url of this.cache.values())URL.revokeObjectURL(url);this.cache.clear();}
}

export function resolveVoice(voices,line,override=null){if(override)return override;const dedicated=voices.find(v=>!v.kind&&(v.speaker===line.speaker||v.aliases?.includes(line.speaker||"")));if(dedicated)return dedicated;return voices.find(v=>v.kind===(!line.speaker||line.speaker==="旁白"?"narrator":"fallback"));}
