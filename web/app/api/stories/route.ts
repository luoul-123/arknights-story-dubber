import {DATA_ROOT,catalogFrom,parseStory} from "../../../lib/story.mjs";
export async function GET(req:Request){
 const id=new URL(req.url).searchParams.get("id");
 if(id && (!/^[a-zA-Z0-9_\/-]+$/.test(id)||id.includes("..")||id.length>180))return Response.json({error:"无效章节"},{status:400});
 try{
 const r=await fetch(DATA_ROOT+(id?"story/"+id+".txt":"excel/story_review_table.json"),{signal:AbortSignal.timeout(20000)});
 if(!r.ok)throw Error("剧情源暂时无法访问（"+r.status+"）");
 const data=id?parseStory(await r.text(),id):catalogFrom(await r.json());
 return Response.json(data,{headers:{"Cache-Control":"public, max-age=3600"}});
 }catch(e){return Response.json({error:e instanceof Error?e.message:"剧情加载失败"},{status:502});}
}
