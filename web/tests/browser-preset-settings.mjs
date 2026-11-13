import {spawn} from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
const root=process.cwd();const edge="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const child=spawn(edge,["--headless=new","--disable-gpu","--no-first-run","--no-default-browser-check","--mute-audio","--remote-debugging-port=9224","--user-data-dir="+path.join(root,"work/qa-browser"),"about:blank"],{stdio:"ignore",windowsHide:true});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
let socket;
try{
 let tabs;
 for(let i=0;i<30;i++){try{tabs=await(await fetch("http://127.0.0.1:9224/json")).json();break;}catch{await pause(300);}}
 if(!tabs)throw Error("Browser did not start");
 socket=new WebSocket(tabs.find(t=>t.type==="page").webSocketDebuggerUrl);
 await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
 let seq=0;const pending=new Map(),errors=[];
 socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const [r,j]=pending.get(m.id)||[];pending.delete(m.id);if(m.error)j?.(Error(JSON.stringify(m.error)));else r?.(m.result);}if(m.method==="Runtime.exceptionThrown")errors.push(m.params.exceptionDetails.text);};
 const send=(method,params={})=>new Promise((r,j)=>{const id=++seq;pending.set(id,[r,j]);socket.send(JSON.stringify({id,method,params}));});
 const evaluate=async expression=>{const r=await send("Runtime.evaluate",{expression,userGesture:true,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text);return r.result.value;};
 const screenshot=async name=>{const r=await send("Page.captureScreenshot",{format:"png"});await fs.writeFile(path.join(root,"work",name+".png"),Buffer.from(r.data,"base64"));};


 await send('Page.enable');await send('Runtime.enable');
 const until=async expression=>{for(let i=0;i<180;i++){if(await evaluate(expression))return;await pause(500);}throw Error('Timed out: '+expression);};
 await send('Emulation.setDeviceMetricsOverride',{width:1440,height:960,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:'http://127.0.0.1:5173/signin-with-chatgpt?return_to=/'});
 await until('Boolean(document.querySelector(".entry-actions .primary"))');
 await evaluate('localStorage.removeItem("terra-manual-save");localStorage.removeItem("zhousheng-progress");localStorage.setItem("zhousheng-settings",JSON.stringify({typing:false,volume:0,musicVolume:0}));location.reload()');
 await until('Boolean(document.querySelector(".entry-actions .primary"))');
 await evaluate('document.querySelector("button[aria-label=静音]").click();document.querySelector(".entry-actions .primary").click()');
 await until('Boolean(document.querySelector(".line-number"))');
 assert.ok(await evaluate('!document.body.textContent.includes("EPISODE 00")&&!document.body.textContent.includes("非官方同人剧场")&&!document.querySelector(".voice-indicator")&&!document.querySelector(".voice-label")&&!document.body.textContent.includes("点击继续")'));
 assert.equal(await evaluate('document.querySelector("a[aria-label^=GitHub]").href'),'https://github.com/luoul-123/arknights-story-dubber');
 const heading=await evaluate('document.querySelector(".chapter-heading").textContent');assert.ok(heading.includes('黑暗时代'));console.log('COLLECTION_HEADER',heading);
 await evaluate('document.querySelector("button[aria-label=阅读设置]").click()');
 await until('Boolean(document.querySelector(".developer-log"))');await evaluate('document.querySelector(".developer-log").open=true');
 assert.equal(await evaluate('document.querySelector(".developer-log li p").textContent'),'新增阿米娅音色语音包');
 assert.ok(await evaluate('!document.querySelector(".drawer").textContent.includes("键盘操作")&&!document.querySelector(".drawer").textContent.includes("角色语音服务已配置")'));await screenshot('preset-reading-settings');
 await evaluate('document.querySelector("button[aria-label=关闭面板]").click();document.querySelector("button[aria-label=朗读音色设置]").click()');
 await until('Boolean(document.querySelector("[aria-label=朗读音色]"))');
 assert.deepEqual(await evaluate('[...document.querySelectorAll("[aria-label=朗读音色] button b")].map(x=>x.textContent)'),['阿米娅','凯尔希','佩丽卡','男管理员','女管理员']);
 assert.equal(await evaluate('document.querySelectorAll("input[type=file]").length'),0);assert.equal(await evaluate('fetch("/api/voice/reader/voice").then(r=>r.status)'),404);assert.equal(await evaluate('fetch("/api/voice/reader/upload",{method:"POST",body:""}).then(r=>r.status)'),404);await screenshot('preset-voice-settings');
 const ready=await evaluate('[...document.querySelectorAll("[aria-label=朗读音色] button")].every(b=>!b.disabled)');if(process.env.EXPECT_PRESETS_READY==='1')assert.ok(ready,'All five trained presets must be published');
 if(ready){
  await evaluate('[...document.querySelectorAll("[aria-label=朗读音色] button")].find(b=>b.textContent.includes("女管理员")).click()');
  const selected=await evaluate('localStorage.getItem("terra-preset-voice")');assert.ok(selected);
  await evaluate('location.reload()');await until('Boolean(document.querySelector(".entry-actions .primary"))');
  await evaluate('document.querySelector("button[aria-label=朗读音色设置]").click()');
  await until('Boolean(document.querySelector("[aria-label=朗读音色] [aria-pressed=true]"))');
  assert.ok(await evaluate('document.querySelector("[aria-label=朗读音色] [aria-pressed=true]").textContent.includes("女管理员")'));console.log('PRESET_PERSISTS',selected);
 }else console.log('PRESETS_WAITING_FOR_TRAINING');
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await pause(300);assert.equal(await evaluate('document.documentElement.scrollWidth>innerWidth'),false);await screenshot('preset-mobile');
 assert.equal(errors.length,0);console.log('ERRORS',errors);await send('Browser.close').catch(()=>{});
}finally{socket?.close();child.kill();}
