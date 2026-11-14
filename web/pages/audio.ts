import {DialogueAudio} from "../lib/audio.mjs";
import manifest from "./audio-manifest.json";

const available=manifest as Record<string,number[]>;
export const VOICED_COUNT=Object.keys(available).length;
export const KALTSIT={id:"kaltsit",speaker:"凯尔希",version:"static"};
export function staticAudioPath(stepId:string){
  const match=/^activities\/act55side\/(level_act55side_[a-z0-9_]+):(\d+)$/.exec(stepId);
  if(!match||!available[match[1]]?.includes(Number(match[2])))return null;
  return import.meta.env.BASE_URL+"audio/"+match[1]+"/"+match[2]+".mp3";
}
export function isVoicedChapter(id:string){
  const slug=id.split("/").pop()||"";
  return id.startsWith("activities/act55side/")&&Boolean(available[slug]?.length);
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
