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

 await send("Page.enable");await send("Runtime.enable");
 await send("Page.addScriptToEvaluateOnNewDocument",{source:'window.__audioPlays=0;const orig=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){if(!this.dataset.storyMusic){window.__audioPlays++;window.__lastAudio=this;}return orig.apply(this,arguments)};'});
 await send("Emulation.setDeviceMetricsOverride",{width:1440,height:960,deviceScaleFactor:1,mobile:false});
 const until=async expression=>{for(let i=0;i<400;i++){if(await evaluate(expression))return;await pause(300);}throw Error("Timed out: "+expression);};
 await send("Page.navigate",{url:"http://127.0.0.1:5173/signin-with-chatgpt?return_to=/"});
 await until('Boolean(document.querySelector(".entry-actions .primary"))');
 await evaluate('localStorage.setItem("zhousheng-progress",JSON.stringify({chapter:{id:"obt/main/level_main_00-01_beg",title:"坍塌",code:"0-1",tag:"行动前"},index:2,choice:null,decisions:{}}));location.reload()');
 await until('Boolean(document.querySelector(".entry-actions .text-button"))');
 await evaluate('document.querySelector(".entry-actions .text-button").click()');
 await until('Boolean(document.querySelector(".dialogue-shell"))');
 await evaluate('document.querySelector(".listen-toggle").click()');
 await until('window.__lastAudio && !window.__lastAudio.paused && window.__lastAudio.currentTime>0.2');
 const snapshot=()=>evaluate('({line:document.querySelector(".line-number")?.textContent,plays:window.__audioPlays,paused:window.__lastAudio.paused,time:window.__lastAudio.currentTime,src:window.__lastAudio.src,media:navigator.mediaSession.playbackState})');
 for(const label of ["章节目录","音色工作室","阅读设置"]){
   const before=await snapshot();
   await evaluate('document.querySelector('+JSON.stringify('button[aria-label="'+label+'"]')+').click()');await pause(150);
   const after=await snapshot();assert.equal(after.paused,false,label+" must keep playing");
   if(before.line===after.line){assert.equal(after.plays,before.plays,label+" must not restart");assert.ok(after.time>=before.time);}
   console.log("DRAWER_CONTINUES",JSON.stringify({label,before:before.line,after:after.line,time:after.time}));
   if(label==="阅读设置"){
    const pre=await snapshot();
    await evaluate('const sliders=[document.querySelector("input[aria-label=配音音量]"),document.querySelector("input[aria-label=播放速度]")];const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;setter.call(sliders[0],"0.6");sliders[0].dispatchEvent(new Event("input",{bubbles:true}));setter.call(sliders[1],"0.8");sliders[1].dispatchEvent(new Event("input",{bubbles:true}));');await pause(100);
    const post=await snapshot();assert.equal(post.paused,false);if(pre.line===post.line){assert.equal(post.plays,pre.plays);assert.ok(post.time>=pre.time);}
    const options=await evaluate('({volume:window.__lastAudio.volume,rate:window.__lastAudio.playbackRate})');assert.equal(options.volume,.6);assert.equal(options.rate,.8);console.log("OPTIONS_WITHOUT_RESTART",JSON.stringify(options));
   }
   await evaluate('document.querySelector("button[aria-label=关闭面板]").click()');
 }
 await evaluate('[...document.querySelectorAll(".control-left button")].find(b=>b.textContent.includes("回顾")).click()');await pause(150);assert.equal((await snapshot()).paused,false);console.log("HISTORY_CONTINUES",true);
 await evaluate('document.querySelector("button[aria-label=关闭面板]").click();document.querySelector("button[aria-label=章节目录]").click()');
 await until('document.querySelectorAll(".archive-categories button").length>4');
 const archive=await evaluate('({categories:document.querySelector(".archive-categories").innerText,groups:document.querySelectorAll(".catalog details").length,title:document.title})');console.log("ARCHIVE",JSON.stringify(archive));assert.ok(archive.title.includes("泰拉之声"));assert.ok(archive.groups>100);
 await evaluate('[...document.querySelectorAll(".archive-categories button")].find(b=>b.textContent.includes("个人密录")).click()');
 assert.ok(await evaluate('document.querySelector(".catalog summary").textContent.includes("12F")'));await screenshot("archive-personal");
 await evaluate('document.querySelector(".archive-categories button").click();document.querySelectorAll(".archive-views button")[1].click()');
 const releases=await evaluate('[...document.querySelectorAll(".timeline-collection")].map(b=>Number(b.dataset.release))');assert.equal(releases.length,80);assert.deepEqual(releases,[...releases].sort((a,b)=>a-b));assert.equal(await evaluate('document.querySelector(".timeline-date").textContent'),"2019-04-30");assert.equal(await evaluate('document.querySelector(".timeline-collection").open'),false);assert.ok(await evaluate('document.querySelector(".timeline-collection summary").textContent.includes("第 0 章")'));await evaluate('document.querySelector(".timeline-collection summary").click()');assert.equal(await evaluate('document.querySelector(".timeline-collection").open'),true);await screenshot("archive-timeline");
 await evaluate('document.querySelector("button[aria-label=关闭面板]").click();document.querySelector(".auto-button").click()');
 const chapterData=await evaluate('fetch("/api/stories?id=obt%2Fmain%2Flevel_main_00-01_end").then(r=>r.json())');assert.ok(chapterData.steps?.length>0);
 await evaluate('localStorage.setItem("zhousheng-progress",JSON.stringify({chapter:{id:"obt/main/level_main_00-01_end",title:"坍塌",code:"0-1",tag:"行动后"},index:'+String(chapterData.steps.length-1)+',choice:"1",decisions:{}}));location.reload()');
 await until('Boolean(document.querySelector(".entry-actions .text-button"))');
 await evaluate('document.querySelector(".entry-actions .text-button").click()');await until('Boolean(document.querySelector(".dialogue-shell"))');
 await evaluate('document.querySelector(".listen-toggle").click();document.querySelector("button[aria-label=立即跳过当前句]").click()');await until('Boolean(document.querySelector(".chapter-complete"))');
 const endText=await evaluate('document.querySelector(".chapter-complete").innerText');assert.ok(endText.includes("0-2"));await pause(1200);assert.equal(await evaluate('Boolean(document.querySelector(".chapter-complete"))'),true);console.log("NEXT_CONFIRMATION",endText);await screenshot("next-section-confirmation");
 await evaluate('document.querySelector("button[aria-label=章节目录]").click()');assert.ok(await evaluate('Boolean(document.querySelector("button[aria-label=确认进入下一段]"))'));
 await evaluate('document.querySelector("button[aria-label=确认进入下一段]").click()');await until('Boolean(document.querySelector(".dialogue-shell")) && document.querySelector(".chapter-heading").textContent.includes("0-2")');console.log("NEXT_SECTION_LOADED",await evaluate('document.querySelector(".chapter-heading").textContent'));
 await evaluate('document.querySelector(".auto-button").click()');
 await send("Emulation.setDeviceMetricsOverride",{width:390,height:844,deviceScaleFactor:1,mobile:true});await pause(400);await screenshot("mobile-terra-voice");assert.equal(await evaluate('document.documentElement.scrollWidth>innerWidth'),false);
 await evaluate('document.querySelector("button[aria-label=章节目录]").click()');await pause(200);await screenshot("mobile-archive");assert.equal(await evaluate('document.documentElement.scrollWidth>innerWidth'),false);
 console.log("ERRORS",JSON.stringify(errors));assert.equal(errors.length,0);
 await send("Browser.close").catch(()=>{});
}finally{socket?.close();child.kill();}
