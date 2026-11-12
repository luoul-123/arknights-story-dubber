import {env} from "cloudflare:workers";
import {headers} from "next/headers";
type Config={VOICE_BACKEND_URL?:string;VOICE_BACKEND_TOKEN?:string;STUDIO_ADMIN_USER_ID?:string};
async function proxy(req:Request,{params}:{params:Promise<{path:string[]}>}){
 const config=env as unknown as Config;const {path}=await params;const route=path.join("/");
 const h=await headers();const userId=h.get("oai-authenticated-user-id");
 const isAdmin=route.startsWith("admin/");
 if(route==="status")return Response.json({connected:!!config.VOICE_BACKEND_URL,admin:!!userId&&userId===config.STUDIO_ADMIN_USER_ID,userId:userId||null});
 if(isAdmin&&(!userId||userId!==config.STUDIO_ADMIN_USER_ID))return Response.json({error:"此操作仅限管理员。请在服务端配置管理员标识。"}, {status:403});
 if(!["voices","speech"].includes(route)&&!isAdmin)return Response.json({error:"接口不存在"},{status:404});
 if(!config.VOICE_BACKEND_URL||!config.VOICE_BACKEND_TOKEN)return Response.json({error:"角色配音服务尚未连接。阅读功能可正常使用。",code:"BACKEND_NOT_CONFIGURED"},{status:503});
 if(!userId)return Response.json({error:"请先登录后使用配音服务"},{status:401});
 const size=Number(req.headers.get("content-length")||0);if(size>50*1024*1024)return Response.json({error:"文件不能超过 50 MB"},{status:413});
 const body=req.method==="GET"?undefined:await req.arrayBuffer();
 if(body && body.byteLength>50*1024*1024)return Response.json({error:"文件不能超过 50 MB"},{status:413});
 try{
 const url=new URL(config.VOICE_BACKEND_URL.replace(/\/$/,"")+"/"+route);url.search=new URL(req.url).search;
 const r=await fetch(url,{method:req.method,body,headers:{"Authorization":"Bearer "+config.VOICE_BACKEND_TOKEN,"Content-Type":req.headers.get("content-type")||"application/json"},signal:AbortSignal.timeout(180000)});
 return new Response(r.body,{status:r.status,headers:{"Content-Type":r.headers.get("content-type")||"application/json","Cache-Control":route==="voices"?"private, max-age=30":"no-store"}});
 }catch{return Response.json({error:"配音服务连接失败，请稍后重试"},{status:502});}
}
export const GET=proxy;export const POST=proxy;export const PUT=proxy;
