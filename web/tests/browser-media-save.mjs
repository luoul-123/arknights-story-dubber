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
 await send('Page.navigate',{url:'http://127.0.0.1:5173/signin-with-chatgpt?return_to=/'});await until('Boolean(document.querySelector(".entry-actions .primary"))');
 const chapter={id:'activities/act27side/level_act27side_01_end',title:'你的耳朵长不长？',code:'SL-1',tag:'行动后'};
 await evaluate('localStorage.removeItem("terra-manual-save");localStorage.setItem("zhousheng-progress",JSON.stringify({chapter:'+JSON.stringify(chapter)+',index:0,choice:null,decisions:{}}));location.reload()');
 await until('Boolean(document.querySelector(".entry-actions .primary"))');await evaluate('document.querySelector("button[aria-label=静音]").click();document.querySelector(".entry-actions .primary").click()');
 await until('Boolean(document.querySelector(".actor")?.naturalWidth)');
 await until('document.querySelector("audio[data-story-music]").currentTime>0.2');
 const initial=await evaluate('({src:document.querySelector(".actor").src,music:document.querySelector("audio[data-story-music]").src,time:document.querySelector("audio[data-story-music]").currentTime})');console.log('REAL_MEDIA',initial);await screenshot('media-expression');
 await evaluate('document.querySelector("button[aria-label=阅读设置]").click()');
 const before=await evaluate('document.querySelector("audio[data-story-music]").currentTime');
 await evaluate('const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;for(const [label,value] of [["背景音乐音量","0.2"],["配音音量","0.6"]]){const e=document.querySelector("input[aria-label="+label+"]");setter.call(e,value);e.dispatchEvent(new Event("input",{bubbles:true}));}');await pause(250);
 const volume=await evaluate('({time:document.querySelector("audio[data-story-music]").currentTime,volume:document.querySelector("audio[data-story-music]").volume,settings:JSON.parse(localStorage.getItem("zhousheng-settings"))})');assert.ok(volume.time>before);assert.equal(volume.settings.volume,.6);assert.equal(volume.settings.musicVolume,.2);assert.ok(volume.volume<=.2);console.log('SEPARATE_VOLUMES',volume);await screenshot('media-volume-settings');
 await evaluate('document.querySelector("button[aria-label=关闭面板]").click()');
 for(let i=0;i<8;i++){await evaluate('document.querySelector("button[aria-label=立即跳过当前句]").click()');await pause(80);if(await evaluate('document.querySelector(".actor") && document.querySelector(".actor").src!=='+JSON.stringify(initial.src)))break;}
 await until('Boolean(document.querySelector(".actor")?.naturalWidth)');const changed=await evaluate('document.querySelector(".actor").src');assert.notEqual(changed,initial.src);console.log('EXPRESSION_CHANGED',changed);
 await evaluate('[...document.querySelectorAll(".control-left button")].find(b=>b.textContent.includes("存档")).click()');const saved=await evaluate('JSON.parse(localStorage.getItem("terra-manual-save"))');
 await evaluate('document.querySelector("button[aria-label=立即跳过当前句]").click()');
 for(let pass=0;pass<2;pass++){await evaluate('location.reload()');await until('Boolean(document.querySelector(".entry-actions .primary"))');const restored=await evaluate('JSON.parse(localStorage.getItem("terra-manual-save"))');assert.deepEqual(restored,saved);assert.ok(await evaluate('document.querySelector(".chapter-heading").textContent.includes("SL-1")'));await evaluate('document.querySelector("button[aria-label=静音]").click();document.querySelector(".entry-actions .primary").click()');await until('Boolean(document.querySelector(".line-number"))');assert.equal(parseInt(await evaluate('document.querySelector(".line-number").textContent')),saved.index+1);}
 console.log('MANUAL_SAVE_SURVIVES_TWO_RELOADS',saved.chapter.id,saved.index);await screenshot('media-restored-save');
 await evaluate('localStorage.removeItem("terra-manual-save")');assert.equal(errors.length,0);console.log('ERRORS',errors);await send('Browser.close').catch(()=>{});
}finally{socket?.close();child.kill();}
