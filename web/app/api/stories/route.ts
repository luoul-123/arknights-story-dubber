import {env} from "cloudflare:workers";
import {DATA_ROOT,catalogFrom,parseStory} from "../../../lib/story.mjs";
const MIRROR="https://cdn.jsdelivr.net/gh/ArknightsAssets/ArknightsGamedata@master/cn/gamedata/";
type Config={VOICE_BACKEND_URL?:string;VOICE_BACKEND_TOKEN?:string};
export async function GET(req:Request){
 const id=new URL(req.url).searchParams.get("id");
 if(id!==null&&(!/^[a-zA-Z0-9_/-]+$/.test(id)||id.includes("..")||id.startsWith("/")||id.length>180))return Response.json({error:"无效章节"},{status:400});
 const config=env as unknown as Config;
 try{
  let raw:any,cache="network";
  if(config.VOICE_BACKEND_URL&&config.VOICE_BACKEND_TOKEN){
   // The host service respects local network/proxy settings and keeps a disk cache.
   const url=new URL(config.VOICE_BACKEND_URL.replace(/\/$/,"")+"/stories");if(id)url.searchParams.set("id",id);
   const r=await fetch(url,{headers:{Authorization:"Bearer "+config.VOICE_BACKEND_TOKEN},signal:AbortSignal.timeout(16000)});
   const result:any=await r.json();if(!r.ok)throw Error(result.error||"剧情服务暂时无法连接");
   raw=result.data;cache=result.cached?(result.stale?"stale":"hit"):"miss";
  }else{
   // A separately deployed reader can still use public static sources.
   let loaded=false;
   for(const base of [DATA_ROOT,MIRROR]){
    try{const r=await fetch(base+(id?"story/"+id+".txt":"excel/story_review_table.json"),{signal:AbortSignal.timeout(6000)});if(!r.ok)continue;raw=id?await r.text():await r.json();if(typeof raw==="string"&&/^\s*</.test(raw))continue;loaded=true;break;}catch{}
   }
   if(!loaded)throw Error("剧情源暂时无法连接，请稍后重试");
  }
  const data=id?parseStory(raw,id):catalogFrom(raw);
  if(Array.isArray(data)?!data.length:!data.steps.length)throw Error("这一章暂时没有可用的剧情数据");
  return Response.json(data,{headers:{"Cache-Control":"public, max-age=3600","X-Story-Cache":cache}});
 }catch(e){const timeout=e instanceof Error&&["TimeoutError","AbortError"].includes(e.name);return Response.json({error:timeout?"剧情服务连接超时，请确认本机服务仍在运行后重试":e instanceof Error?e.message:"剧情加载失败"},{status:502,headers:{"Cache-Control":"no-store"}});}
}
