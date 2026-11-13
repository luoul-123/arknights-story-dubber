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
 await send('Page.addScriptToEvaluateOnNewDocument',{source:'window.__speechRequests=[];window.__voicePlays=0;const origFetch=window.fetch;window.fetch=function(url,opts){if(String(url).endsWith("/api/voice/speech"))window.__speechRequests.push(JSON.parse(opts.body));return origFetch.apply(this,arguments)};const origPlay=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){if(!this.dataset.storyMusic){window.__lastVoice=this;window.__voicePlays++;}return origPlay.apply(this,arguments)};'});
 const until=async expression=>{for(let i=0;i<360;i++){if(await evaluate(expression))return;await pause(500);}throw Error('Timed out: '+expression);};
 await send('Page.navigate',{url:'http://127.0.0.1:5173/signin-with-chatgpt?return_to=/'});await until('Boolean(document.querySelector(".entry-actions .primary"))');
 await evaluate('localStorage.removeItem("terra-manual-save");localStorage.setItem("zhousheng-progress",JSON.stringify({chapter:{id:"obt/main/level_main_00-01_beg",title:"坍塌",code:"0-1",tag:"行动前"},index:2,choice:null,decisions:{}}));localStorage.setItem("zhousheng-settings",JSON.stringify({typing:false,volume:0,musicVolume:0}));location.reload()');await until('Boolean(document.querySelector(".entry-actions .primary"))');
 await evaluate('document.querySelector(".entry-actions .primary").click()');await until('Boolean(window.__lastVoice)');await pause(1000);
 await evaluate('document.activeElement.blur();window.__speechRequests=[];window.__voicePlays=0');
 const initial=await evaluate('parseInt(document.querySelector(".line-number").textContent)');
 for(let i=0;i<15;i++){await send('Input.dispatchKeyEvent',{type:'keyDown',key:' ',code:'Space',windowsVirtualKeyCode:32,autoRepeat:i>0});await pause(40);}
 await send('Input.dispatchKeyEvent',{type:'keyUp',key:' ',code:'Space',windowsVirtualKeyCode:32});
 const after=await evaluate('({line:parseInt(document.querySelector(".line-number").textContent),calls:window.__speechRequests.length,text:document.querySelector(".dialogue-text span").textContent})');assert.equal(after.line,initial+15);assert.equal(after.calls,0);
 await until('window.__speechRequests.length>0');const request=await evaluate('window.__speechRequests[0]');assert.equal(request.text,after.text);
 await until('window.__voicePlays>0 && navigator.mediaSession.playbackState==="playing"');
 console.log('RAPID_SKIP_LATEST_PLAYS',JSON.stringify({from:initial,to:after.line,callsDuringRepeat:after.calls,latestText:request.text,voiceId:request.voiceId}));assert.equal(errors.length,0);await screenshot('rapid-skip-resumed');await send('Browser.close').catch(()=>{});
}finally{socket?.close();child.kill();}
