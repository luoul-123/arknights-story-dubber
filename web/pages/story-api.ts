import catalog from "./catalog.json";
import {parseStory} from "../lib/story.mjs";

export const CATALOG=catalog;
const SOURCES=[
  "https://cdn.jsdelivr.net/gh/ArknightsAssets/ArknightsGamedata@master/cn/gamedata/story/",
  "https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/master/cn/gamedata/story/",
];
export async function loadStory(id:string){
  if(!/^[a-zA-Z0-9_/-]{1,180}$/.test(id)||id.includes("..")||id.startsWith("/"))throw Error("无效章节");
  if(id.startsWith('activities/act55side/')){
    const response=await fetch(import.meta.env.BASE_URL+'sample/'+id.split('/').pop()+'.txt');
    if(!response.ok)throw Error('样例剧情暂时无法加载');
    return parseStory(await response.text(),id);
  }
  for(const base of SOURCES){
    try{
      const response=await fetch(base+id+".txt",{signal:AbortSignal.timeout(15000)});
      if(!response.ok)continue;
      const raw=await response.text();
      if(/^\s*</.test(raw))continue;
      const data=parseStory(raw,id);
      if(data.steps.length)return data;
    }catch{}
  }
  throw Error("剧情源暂时无法连接，请稍后重试");
}
