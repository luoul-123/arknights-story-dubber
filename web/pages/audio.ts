import {DialogueAudio} from "../lib/audio.mjs";
import manifest from "./audio-manifest.json";
import audioSites from "./audio-sites.json";

const available=manifest as Record<string,number[]>;
const sites=audioSites as {chapters:Record<string,string>;prefixes:Record<string,string>};
export const VOICED_COUNT=Object.keys(available).length;
export const KALTSIT={id:"kaltsit",speaker:"凯尔希",version:"static"};
export function staticAudioPath(stepId:string){
  const match=/^([^:]+):(\d+)$/.exec(stepId);
  if(!match)return null;
  const chapterId=match[1],slug=chapterId.split("/").pop()||"";
  const indices=available[chapterId]??(chapterId.startsWith("activities/act55side/")?available[slug]:undefined);
  if(!indices?.includes(Number(match[2])))return null;
  const prefix=Object.keys(sites.prefixes).filter(key=>chapterId.startsWith(key)).sort((a,b)=>b.length-a.length)[0];
  const base=sites.chapters[chapterId]??(prefix?sites.prefixes[prefix]:undefined)??import.meta.env.BASE_URL;
  return base.replace(/\/?$/,"/")+"audio/"+slug+"/"+match[2]+".mp3";
}
export function isVoicedChapter(id:string){
  const slug=id.split("/").pop()||"";
  return Boolean(available[id]?.length||(id.startsWith("activities/act55side/")&&available[slug]?.length));
}
export class StaticDialogueAudio extends DialogueAudio{
  async load(line:any,voice:any,signal:AbortSignal){
    const key=this.key(line,voice);
    const cached=this.cache.get(key);
    if(cached)return cached;
    const url=staticAudioPath(line.id);
    if(!url||voice?.id!==KALTSIT.id)throw Error("这一句暂无凯尔希配音");
    const response=await fetch(url,{signal});
    if(!response.ok)throw Error("音频暂时无法加载");
    const objectUrl=URL.createObjectURL(await response.blob());
    this.cache.set(key,objectUrl);
    if(this.cache.size>24){const first=this.cache.keys().next().value;if(first!==undefined&&first!==key){URL.revokeObjectURL(this.cache.get(first)!);this.cache.delete(first);}}
    return objectUrl;
  }
}
