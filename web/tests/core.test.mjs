import test from "node:test";
import assert from "node:assert/strict";
import {parseStory,nextIndex,resolveScene,attrs,imageUrl,catalogFrom,timelineFrom,nextChapter,previousStep} from "../lib/story.mjs";
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
 const player=new DialogueAudio({debounceMs:0,fetcher,makeAudio:()=>{const a={played:false,pause(){},load(){},removeAttribute(){},async play(){this.played=true;}};audios.push(a);return a;}});
 const old=player.play({text:"old"},{id:"voice",version:"1"});
 await player.play({text:"new"},{id:"voice",version:"1"});
 resolveOld(new Response(new Blob(["old"])));await old;
 assert.equal(audios.length,1);assert.equal(audios[0].played,true);player.dispose();
});
test("stop invalidates pending playback and prior completion callback",async()=>{
 let finish;let ended=0;const a={pause(){},load(){},removeAttribute(){},async play(){},onended:null};
 const player=new DialogueAudio({debounceMs:0,fetcher:()=>Promise.resolve(new Response(new Blob(["x"]))),makeAudio:()=>a});
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
 let finish,played=0;const player=new DialogueAudio({debounceMs:0,fetcher:()=>new Promise(r=>finish=r),makeAudio:()=>({pause(){},removeAttribute(){},load(){},async play(){played++;}})});
 const task=player.play({text:"旁白"},{id:"n",version:"1"});player.pause();finish(new Response(new Blob(["x"])));await task;
 assert.equal(played,0);await player.resume();assert.equal(played,1);player.dispose();
});

test("archive categories and first release dates do not use rerun or archive dates",()=>{
 const raw={main:{id:"main_5",name:"靶向药物",entryType:"MAINLINE",startTime:-1,startShowTime:1591041600,infoUnlockDatas:[{storyTxt:"main/5",storyName:"一",storySort:1}]},side:{id:"side",name:"活动",entryType:"ACTIVITY",startTime:1559181600,remakeStartTime:1700000000,infoUnlockDatas:[{storyTxt:"act/1",storyName:"二"}]},personal:{id:"record",name:"密录",entryType:"NONE",startTime:0,infoUnlockDatas:[{storyTxt:"obt/memory/1",storyName:"三"}]}};
 const groups=catalogFrom(raw,{personal:{record:{operator:"黑角",releasedAt:1617091200}}});
 assert.equal(groups[0].category,"main");assert.equal(groups[0].date,"2019-07-09");assert.equal(groups[1].category,"side");assert.equal(groups[1].releasedAt,1559181600);assert.equal(groups[2].category,"personal");assert.equal(groups[2].operator,"黑角");
 assert.deepEqual(timelineFrom(groups).map(c=>c.id),["act/1","main/5","obt/memory/1"]);
});
test("next section keeps before/after stories before advancing to the next stage",()=>{
 const groups=[{id:"main_0",category:"main",releasedAt:1,groupSort:0,chapters:[{id:"0-1-beg"},{id:"0-1-end"},{id:"0-2-beg"}]},{id:"main_1",category:"main",releasedAt:1,groupSort:1,chapters:[{id:"1-1-beg"}]}];
 assert.equal(nextChapter(groups,"0-1-beg").id,"0-1-end");assert.equal(nextChapter(groups,"0-1-end").id,"0-2-beg");assert.equal(nextChapter(groups,"0-2-beg").id,"1-1-beg");assert.equal(nextChapter(groups,"1-1-beg"),null);
});
test("volume and speed changes preserve the active sentence and playback position",async()=>{
 let played=0;const audio={currentTime:2.1,pause(){},load(){},removeAttribute(){},async play(){played++;}};
 const player=new DialogueAudio({debounceMs:0,fetcher:async()=>new Response(new Blob(["x"])),makeAudio:()=>audio});
 await player.play({text:"当前台词"},{id:"v",version:"1"});const generation=player.generation;
 player.setOptions({volume:.4,rate:1.3});assert.equal(audio.volume,.4);assert.equal(audio.playbackRate,1.3);assert.equal(audio.currentTime,2.1);assert.equal(played,1);assert.equal(player.generation,generation);player.dispose();
});

test("selected preset overrides every speaker and narration",()=>{const personal={id:"kaltsit",version:"published",speaker:"凯尔希"};const voices=[{id:"amiya",speaker:"阿米娅"},{id:"__npc",kind:"fallback"},{id:"__narrator",kind:"narrator"}];for(const speaker of ["阿米娅","士兵","旁白",""])assert.equal(resolveVoice(voices,{speaker},personal),personal);assert.equal(resolveVoice(voices,{speaker:"阿米娅"},null).id,"amiya");});

test('new portrait expressions and action-only slots remain visible',()=>{const {steps}=parseStory('[charslot(slot="r",name="avg_180_amgoat_1#3$1")]\n[name="甲"] A\n[charslot(slot="r",posto="10,20",duration=1)]\n[name="甲"] B');const scene=resolveScene(steps,1);assert.equal(scene.actors.length,1);assert.equal(scene.actors[0].slot,'r');assert.match(scene.actors[0].url,/%233%241/);assert.deepEqual(scene.actors[0].offset,[10,20]);});
test('music state respects branches, volume and stop',()=>{const {steps}=parseStory('[PlayMusic(intro="$a_intro",key="$a_loop",volume=0.6)]\n[name="甲"] A\n[MusicVolume(volume=0.3)]\n[name="甲"] B\n[StopMusic]\n[name="甲"] C');assert.equal(resolveScene(steps,0).music.intro,'$a_intro');assert.equal(resolveScene(steps,1).musicVolume,.3);assert.equal(resolveScene(steps,2).music,null);});

test('rapid skipping submits only the final sentence after debounce',async()=>{let calls=[];const player=new DialogueAudio({fetcher:async(u,o)=>{calls.push(JSON.parse(o.body).text);return new Response(new Blob(['audio']));},makeAudio:()=>({play:async()=>{},pause(){},removeAttribute(){},load(){}})});const pending=[];for(let i=0;i<20;i++)pending.push(player.play({text:String(i)},{id:'v',version:'1'}));await Promise.all(pending);assert.deepEqual(calls,['19']);player.dispose();});

test('previous sentence can be restored from a save and respects selected branches',()=>{const steps=[{id:'a',type:'line',text:'开始'},{id:'choice',type:'choice'},{id:'b',type:'line',route:['1']},{id:'c',type:'line',route:['2']},{id:'d',type:'line'}];assert.equal(previousStep(steps,0),null);assert.equal(previousStep([],12),null);assert.equal(previousStep(steps,4,{choice:'1'}).index,2);assert.equal(previousStep(steps,4,{choice:'2'}).index,3);assert.equal(previousStep(steps,3,{choice:'2'}).step.type,'choice');});
