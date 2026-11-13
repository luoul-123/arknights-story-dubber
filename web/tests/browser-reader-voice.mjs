import {spawn} from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
const root=process.cwd();const edge="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const child=spawn(edge,["--headless=new","--disable-gpu","--no-first-run","--no-default-browser-check","--mute-audio","--remote-debugging-port=9224","--user-data-dir="+path.join(root,"work/qa-browser"),"about:blank"],{stdio:"ignore",windowsHide:true});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
let socket,readerFolder,readerBackup,priorFiles,testVersion;
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

 await send("Page.enable");await send("Runtime.enable");await send("Network.enable");
 const requests=[];const handle=socket.onmessage;socket.onmessage=e=>{handle(e);const m=JSON.parse(e.data);if(m.method==='Network.requestWillBeSent'&&m.params.request.url.endsWith('/api/voice/speech')){try{requests.push(JSON.parse(m.params.request.postData));}catch{}}};
 await send("Page.addScriptToEvaluateOnNewDocument",{source:'const orig=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){if(!this.dataset.storyMusic)window.__lastAudio=this;return orig.apply(this,arguments)};'});
 const until=async expression=>{for(let i=0;i<240;i++){if(await evaluate(expression))return;await pause(500);}throw Error('Timed out: '+expression);};
 await send("Emulation.setDeviceMetricsOverride",{width:1440,height:960,deviceScaleFactor:1,mobile:false});
 await send("Page.navigate",{url:"http://127.0.0.1:5173/signin-with-chatgpt?return_to=/"});
 await until('Boolean(document.querySelector(".entry-actions .primary"))');
 const identity=await evaluate('fetch("/api/voice/status").then(r=>r.json())');assert.ok(identity.userId);
 const {createHash}=await import('node:crypto');readerFolder=path.join(root,'.voice-data/readers',createHash('sha256').update(identity.userId).digest('hex'));
 readerBackup=await fs.readFile(path.join(readerFolder,'profile.json')).catch(()=>null);priorFiles=new Set(await fs.readdir(readerFolder).catch(()=>[]));
 const profiles=JSON.parse(await fs.readFile(path.join(root,'.voice-data/characters.json'),'utf8'));const reference=Object.values(profiles).find(c=>c.speaker==='佩丽卡').published.reference.path;
 await evaluate('document.querySelector("button[aria-label=音色工作室]").click()');await until('Boolean(document.querySelector(".reader-studio input[type=file]"))');
 const doc=await send('DOM.getDocument');const file=await send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'.reader-studio input[type=file]'});await send('DOM.setFileInputFiles',{nodeId:file.nodeId,files:[reference]});
 await until('Boolean(document.querySelector(".reader-transcript textarea")?.value) && !document.querySelector(".reader-transcript .primary").disabled');
 console.log('UPLOAD_TRANSCRIBED',await evaluate('document.querySelector(".reader-transcript textarea").value'));
 await evaluate('document.querySelector(".reader-transcript .primary").click()');await until('document.querySelectorAll(".reading-modes button")[1].getAttribute("aria-pressed")==="true"');
 const personal=await evaluate('fetch("/api/voice/reader/voice").then(r=>r.json())');testVersion=personal.voice.version;assert.equal(personal.voice.kind,'reader');await screenshot('reader-studio-desktop');
 await evaluate('document.querySelector("button[aria-label=关闭面板]").click();document.querySelector(".entry-actions .primary").click()');
 await until('window.__lastAudio && !window.__lastAudio.paused && window.__lastAudio.currentTime>0.1');
 for(let i=0;i<2;i++){await evaluate('document.querySelector("button[aria-label=立即跳过当前句]").click()');await pause(250);}
 await until('window.__lastAudio && !window.__lastAudio.paused && window.__lastAudio.currentTime>0.1');
 assert.ok(requests.length>=3);assert.ok(requests.every(r=>r.voiceId==='__reader'));console.log('UNIFIED_SPEAKERS',JSON.stringify([...new Set(requests.map(r=>r.speaker))]));
 await evaluate('document.querySelector("button[aria-label=音色工作室]").click()');await until('document.querySelectorAll(".reading-modes button")[1]?.getAttribute("aria-pressed")==="true"');
 await send("Emulation.setDeviceMetricsOverride",{width:390,height:844,deviceScaleFactor:1,mobile:true});await pause(300);await screenshot('reader-studio-mobile');assert.equal(await evaluate('document.documentElement.scrollWidth>innerWidth'),false);
 const count=requests.length;await evaluate('document.querySelector(".reading-modes button").click()');await until('document.querySelector(".reading-modes button").getAttribute("aria-pressed")==="true"');
 await pause(200);assert.ok(requests.slice(count).some(r=>r.voiceId==='__npc'));console.log('DEFAULT_RESTORED',true);
 assert.equal(errors.length,0);console.log('ERRORS',errors);await send('Browser.close').catch(()=>{});
}finally{
 socket?.close();child.kill();
 if(readerFolder){
  const current=JSON.parse(await fs.readFile(path.join(readerFolder,'profile.json'),'utf8').catch(()=>'{}'));
  if(!testVersion||current.published?.version===testVersion){
   if(readerBackup)await fs.writeFile(path.join(readerFolder,'profile.json'),readerBackup);else await fs.unlink(path.join(readerFolder,'profile.json')).catch(()=>{});
   for(const filename of await fs.readdir(readerFolder).catch(()=>[])){if(!priorFiles.has(filename)&&/^[a-f0-9]{32}.wav$/.test(filename))await fs.unlink(path.join(readerFolder,filename));}
  }
 }
}
