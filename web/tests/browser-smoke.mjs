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
 await send("Page.enable");await send("Runtime.enable");
 await send("Emulation.setDeviceMetricsOverride",{width:1440,height:960,deviceScaleFactor:1,mobile:false});
 await send("Page.navigate",{url:"http://127.0.0.1:5173/signin-with-chatgpt?return_to=/"});
 for(let i=0;i<45;i++){await pause(1000);if(await evaluate('Boolean(document.querySelector(".entry-actions .primary"))'))break;}
 await evaluate('localStorage.removeItem("terra-manual-save");localStorage.removeItem("zhousheng-progress");localStorage.removeItem("terra-preset-voice");location.reload()');
 for(let i=0;i<45;i++){await pause(1000);if(await evaluate('Boolean(document.querySelector(".entry-actions .primary"))'))break;}
 console.log("STATUS",JSON.stringify(await evaluate('({title:document.title,text:document.body.innerText.slice(0,350),overflow:document.documentElement.scrollWidth>innerWidth})')));
 await screenshot("desktop-entry");
 console.log("VOICE_RESPONSE",JSON.stringify(await evaluate('fetch("/api/voice/voices").then(async r=>({status:r.status,body:await r.text()}))')));
 console.log("AUTH",JSON.stringify(await evaluate('fetch("/api/voice/status").then(r=>r.json())')));
 console.log("ASSETS",JSON.stringify(await evaluate('[...document.images].map(i=>({src:i.src,loaded:i.complete&&i.naturalWidth>0}))')));
 await evaluate('document.querySelector(".entry-actions .primary").click()');await pause(2500);
 await screenshot("desktop-dialogue");
 const initial=await evaluate('document.querySelector(".line-number")?.textContent');
 await nextLine();await pause(200);await nextLine();await pause(2500);
 console.log("ADVANCE",JSON.stringify({initial,next:await evaluate('document.querySelector(".line-number")?.textContent'),cg:await evaluate('Boolean(document.querySelector(".cg"))')}));
 await screenshot("desktop-cg");
 await evaluate('document.querySelector(".listen-toggle").click()');
 const other=await send("Target.createTarget",{url:"about:blank"});
 for(let i=0;i<60;i++){await pause(500);if(await evaluate('parseInt(document.querySelector(".line-number")?.textContent)>3 && navigator.mediaSession.playbackState==="playing"'))break;}
 const background=await evaluate('({hidden:document.visibilityState,line:document.querySelector(".line-number")?.textContent,status:document.querySelector(".listen-badge")?.textContent,media:navigator.mediaSession?.playbackState,hint:document.querySelector(".click-hint")?.textContent})');
 console.log("BACKGROUND_LISTEN",JSON.stringify(background));assert.equal(background.hidden,"hidden");assert.ok(parseInt(background.line)>3,"Background playback must advance to next line");assert.equal(background.media,"playing");
 await send("Target.closeTarget",{targetId:other.targetId});await pause(200);
 await evaluate('document.querySelector(".auto-button").click()');const pausedLine=await evaluate('document.querySelector(".line-number").textContent');await pause(2200);
 const paused=await evaluate('({line:document.querySelector(".line-number").textContent,media:navigator.mediaSession.playbackState})');assert.equal(paused.line,pausedLine);assert.equal(paused.media,"paused");console.log("PAUSED",JSON.stringify(paused));
 await evaluate('document.querySelector(".auto-button").click()');await pause(150);assert.equal(await evaluate('navigator.mediaSession.playbackState'),"playing");
 await nextLine();await pause(200);assert.ok(parseInt(await evaluate('document.querySelector(".line-number").textContent'))>parseInt(pausedLine));
 await screenshot("desktop-listening");await evaluate('document.querySelector(".listen-toggle").click()');

 await evaluate('document.querySelector("button[aria-label=朗读音色设置]").click()');await pause(1000);
 console.log("STUDIO",await evaluate('document.querySelector(".studio-drawer")?.innerText.slice(0,600)'));await screenshot("desktop-studio");
 await evaluate('document.querySelector("button[aria-label=关闭面板]").click()');
 await send("Emulation.setDeviceMetricsOverride",{width:390,height:844,deviceScaleFactor:1,mobile:true});await pause(800);await screenshot("mobile-dialogue");
 console.log("MOBILE",JSON.stringify(await evaluate('({overflow:document.documentElement.scrollWidth>innerWidth,width:innerWidth})')));
 console.log("ERRORS",JSON.stringify(errors));assert.equal(errors.length,0);
 await evaluate('localStorage.setItem("zhousheng-progress",JSON.stringify({chapter:{id:"obt/main/level_main_00-01_beg",title:"坍塌",code:"0-1",tag:"行动前"},index:55,choice:null,decisions:{}}));location.reload()');
 for(let i=0;i<30;i++){await pause(500);if(await evaluate('Boolean(document.querySelector(".entry-actions .text-button"))'))break;}
 await evaluate('document.querySelector(".entry-actions .text-button").click()');
 for(let i=0;i<30;i++){await pause(500);if(await evaluate('Boolean(document.querySelector(".choice-panel"))'))break;}
 await evaluate('document.querySelector(".listen-toggle").click()');await pause(2200);
 assert.equal(await evaluate('Boolean(document.querySelector(".choice-panel"))'),true);assert.equal(await evaluate('document.querySelector(".listen-badge").textContent'),"等待你的选择");console.log("BRANCH_PAUSES",true);
 await evaluate('document.querySelector(".choice-panel button").click()');await pause(300);assert.equal(await evaluate('Boolean(document.querySelector(".dialogue-shell"))'),true);console.log("BRANCH_CONTINUES",true);

 await send("Browser.close").catch(()=>{});
}finally{socket?.close();child.kill();}
