import test from "node:test";
import assert from "node:assert/strict";
import {parseStory,nextIndex,resolveScene,attrs,imageUrl} from "../lib/story.mjs";
import {DialogueAudio,resolveVoice} from "../lib/audio.mjs";
test("original script names, nickname and CG directory",()=>{
 const {steps}=parseStory('[Image(image="bg_0_am")]\n[name="阿米娅"] Dr.{@nickname}，你好。');
 assert.equal(steps[0].speaker,"阿米娅");assert.equal(steps[0].text,"Dr.博士，你好。");assert.match(steps[0].scene.cg,/images\/bg_0_am.png$/);
});
test("branch text and media follow selected option, including merged scene",()=>{
 const {steps}=parseStory('[Background(image="start")]\n[Decision(options="A;B",values="1;2")]\n[Predicate(references="1")]\n[Background(image="left")]\n[name="甲"] A\n[Predicate(references="2")]\n[Background(image="right")]\n[name="乙"] B\n[Predicate(references="1;2")]\n[name="丙"] C');
 assert.equal(nextIndex(steps,0,"1"),1);assert.equal(nextIndex(steps,1,"1"),3);
 assert.equal(nextIndex(steps,0,"2"),2);
 assert.match(resolveScene(steps,3,{[steps[0].id]:"1"}).background,/left.png$/);
 assert.match(resolveScene(steps,3,{[steps[0].id]:"2"}).background,/right.png$/);
});
test("clear media and portrait focus are interpreted",()=>{
 const {steps}=parseStory('[Character(name="one",name2="two",focus=2)]\n[name="甲"] A\n[Character]\n[Image]\n[Background]\n[name="乙"] B');
 assert.equal(steps[0].scene.focus,1);assert.equal(resolveScene(steps,1).actors.length,0);assert.equal(resolveScene(steps,1).cg,null);
});
test("input cannot create arbitrary media URLs",()=>{assert.equal(imageUrl("cg","../secret"),null);assert.equal(attrs('name="a,b", focus=2').name,"a,b");});
test("late audio response cannot play after player advances",async()=>{
 let resolveOld;const audios=[];let calls=0;
 const fetcher=()=>++calls===1?new Promise(r=>resolveOld=r):Promise.resolve(new Response(new Blob(["new"])));
 const player=new DialogueAudio({fetcher,makeAudio:()=>{const a={played:false,pause(){},load(){},removeAttribute(){},async play(){this.played=true;}};audios.push(a);return a;}});
 const old=player.play({text:"old"},{id:"voice",version:"1"});
 await player.play({text:"new"},{id:"voice",version:"1"});
 resolveOld(new Response(new Blob(["old"])));await old;
 assert.equal(audios.length,1);assert.equal(audios[0].played,true);player.dispose();
});
test("stop invalidates pending playback and prior completion callback",async()=>{
 let finish;let ended=0;const a={pause(){},load(){},removeAttribute(){},async play(){},onended:null};
 const player=new DialogueAudio({fetcher:()=>Promise.resolve(new Response(new Blob(["x"]))),makeAudio:()=>a});
 await player.play({text:"first"},{id:"v",version:"1"},{onEnd:()=>ended++});finish=a.onended;player.stop();finish();assert.equal(ended,0);player.dispose();
});

test("narration and every unmatched speaker receive a server voice automatically",()=>{
 const voices=[{id:"amiya",speaker:"阿米娅"},{id:"n",kind:"narrator"},{id:"f",kind:"fallback"}];
 assert.equal(resolveVoice(voices,{speaker:"阿米娅"}).id,"amiya");
 assert.equal(resolveVoice(voices,{speaker:"不知名的路人"}).id,"f");
 assert.equal(resolveVoice(voices,{speaker:"？？？"}).id,"f");
 assert.equal(resolveVoice(voices,{speaker:"旁白"}).id,"n");
 assert.equal(resolveVoice(voices,{speaker:""}).id,"n");
});
test("pause while synthesis is pending does not unexpectedly start playback",async()=>{
 let finish,played=0;const player=new DialogueAudio({fetcher:()=>new Promise(r=>finish=r),makeAudio:()=>({pause(){},removeAttribute(){},load(){},async play(){played++;}})});
 const task=player.play({text:"旁白"},{id:"n",version:"1"});player.pause();finish(new Response(new Blob(["x"])));await task;
 assert.equal(played,0);await player.resume();assert.equal(played,1);player.dispose();
});
