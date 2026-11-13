"use client";
import {useEffect,useRef,useState} from 'react';
export default function StoryMusic({music,volume,active}:any){
 const audio=useRef<HTMLAudioElement|null>(null),enabled=useRef(active);enabled.current=active;
 const [error,setError]=useState('');
 const key=music?.key||'',intro=music?.intro||'',event=music?.event||'';
 useEffect(()=>{const a=audio.current;if(!a)return;a.pause();setError('');if(!key&&!intro){a.removeAttribute('src');a.load();return;}
  const source=(name:string)=>'/api/media?kind=music&name='+encodeURIComponent(name);
  a.loop=!intro||intro===key;a.src=source(intro||key);
  a.onended=()=>{if(intro&&key&&intro!==key){a.src=source(key);a.loop=true;if(enabled.current)a.play().catch(()=>setError('点击重试背景音乐'));}};
  if(enabled.current)a.play().catch(()=>setError('点击重试背景音乐'));
  return()=>{a.pause();a.onended=null;};
 },[key,intro,event]);
 useEffect(()=>{if(audio.current)audio.current.volume=Math.max(0,Math.min(1,volume));},[volume]);
 useEffect(()=>{const a=audio.current;if(!a?.getAttribute('src'))return;if(active)a.play().catch(()=>setError('点击重试背景音乐'));else a.pause();},[active]);
 return <><audio ref={audio} data-story-music="true" preload="auto" onError={()=>setError('音乐暂时未加载，点击重试')}/>{error&&active&&<button className="music-retry" onClick={()=>{setError('');audio.current?.load();audio.current?.play().catch(()=>setError('音乐暂时未加载，点击重试'));}}>{error}</button>}</>;
}
