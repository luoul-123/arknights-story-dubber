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
 const nextLine=async()=>{if(await evaluate('document.querySelector(".dialogue-text")?.getAttribute("aria-label")==="显示完整台词"')){await evaluate('document.querySelector(".dialogue-text").click()');await pause(60);}await evaluate('document.querySelector(".dialogue-text").click()');};
 const screenshot=async name=>{const r=await send("Page.captureScreenshot",{format:"png"});await fs.writeFile(path.join(root,"work",name+".png"),Buffer.from(r.data,"base64"));};


 await send('Page.enable');await send('Runtime.enable');
 const until=async expression=>{for(let i=0;i<180;i++){if(await evaluate(expression))return;await pause(500);}throw Error('Timed out: '+expression);};
 await send('Emulation.setDeviceMetricsOverride',{width:1148,height:834,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:'http://127.0.0.1:5173/signin-with-chatgpt?return_to=/'});await until('Boolean(document.querySelector(".entry-actions .primary"))');
 await evaluate('localStorage.removeItem("terra-manual-save");localStorage.setItem("zhousheng-progress",JSON.stringify({chapter:{id:"obt/main/level_main_00-01_beg",title:"坍塌",code:"0-1",tag:"行动前"},index:3,choice:null,decisions:{}}));location.reload()');await until('Boolean(document.querySelector(".entry-actions .primary"))');
 await evaluate('document.querySelector("button[aria-label=静音]").click();document.querySelector(".entry-actions .primary").click()');await until('Boolean(document.querySelector(".line-number"))');
 assert.equal(parseInt(await evaluate('document.querySelector(".line-number").textContent')),4);
 await evaluate('document.querySelector("button[aria-label=上一句]").click()');await pause(100);assert.equal(parseInt(await evaluate('document.querySelector(".line-number").textContent')),3);
 assert.deepEqual(await evaluate('[...document.querySelectorAll(".chapter-nav-button small")].map(e=>e.textContent)'),['上一句','下一章']);
 await evaluate('document.querySelector("button[aria-label=下一章]").click()');await until('document.querySelector(".chapter-heading").textContent.includes("行动后")&&Boolean(document.querySelector(".dialogue-shell"))');assert.ok(await evaluate('document.querySelector(".chapter-heading").textContent.includes("0-1")'));
 assert.equal(await evaluate('document.querySelector("button[aria-label=上一句]").disabled'),true);
 await evaluate('document.querySelector("button[aria-label=下一章]").click()');await until('document.querySelector(".chapter-heading").textContent.includes("0-2")&&Boolean(document.querySelector(".dialogue-shell"))');console.log('BOTTOM_NEXT_ORDER','0-1 行动前 → 0-1 行动后 → 0-2 行动前');
 for(const width of [1148,640,390]){await send('Emulation.setDeviceMetricsOverride',{width,height:834,deviceScaleFactor:1,mobile:width<600});await pause(250);const layout=await evaluate('(()=>{const l=document.querySelector(".control-left").getBoundingClientRect(),c=document.querySelector(".control-center").getBoundingClientRect(),r=document.querySelector(".control-right").getBoundingClientRect();return {left:l.right,centerLeft:c.left,centerRight:c.right,right:r.left,overflow:document.documentElement.scrollWidth>innerWidth}})()');console.log('BOTTOM_LAYOUT',width,layout);assert.equal(layout.overflow,false);assert.ok(layout.left<=layout.centerLeft&&layout.centerRight<=layout.right,'Bottom controls overlap at '+width);await screenshot('bottom-navigation-'+width);}
 assert.equal(errors.length,0);await send('Browser.close').catch(()=>{});
}finally{socket?.close();child.kill();}
