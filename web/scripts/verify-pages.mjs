import fs from 'node:fs';
import path from 'node:path';
import {parseStory} from '../lib/story.mjs';

const root=path.resolve(import.meta.dirname,'../pages');
const catalog=JSON.parse(fs.readFileSync(path.join(root,'catalog.json'),'utf8'));
const manifest=JSON.parse(fs.readFileSync(path.join(root,'audio-manifest.json'),'utf8'));
const audioSites=JSON.parse(fs.readFileSync(path.join(root,'audio-sites.json'),'utf8'));
const voiced=JSON.parse(fs.readFileSync(path.join(root,'voiced-chapters.json'),'utf8'));
const chapters=new Map(catalog.flatMap(group=>group.chapters.map(chapter=>[chapter.id,chapter])));
const sample=catalog.find(group=>group.id==='act55side');
if(!sample||sample.chapters.length!==24)throw Error('《时间啊，向前！》目录不完整');
const legacy=new Map(sample.chapters.map(chapter=>[path.basename(chapter.id),chapter]));
if(!Array.isArray(voiced)||!voiced.length||new Set(voiced).size!==voiced.length)throw Error('配音章节配置无效');
if(Object.keys(manifest).some(key=>!voiced.includes(key)))throw Error('配音清单包含未发布章节');

let count=0,bytes=0,remoteCount=0;
for(const key of voiced){
 const chapter=chapters.get(key)||legacy.get(key);
 if(!chapter)throw Error(`${key}: 章节不在目录中`);
 const slug=path.basename(chapter.id);
 const sourceDir=chapter.groupId==='act55side'?'sample':`story/${chapter.groupId}`;
 const sourcePath=path.join(root,'public',sourceDir,slug+'.txt');
 if(!fs.existsSync(sourcePath))throw Error(`${key}: 本地剧情文本缺失`);
 const source=fs.readFileSync(sourcePath,'utf8');
 const lines=parseStory(source,chapter.id).steps.filter(step=>step.type==='line'&&step.text);
 const expected=lines.map(step=>Number(step.id.split(':').pop()));
 const actual=manifest[key]||[];
 if(JSON.stringify(expected)!==JSON.stringify(actual))throw Error(`${key}: 配音清单不完整 (${actual.length}/${expected.length})`);
 const prefix=Object.keys(audioSites.prefixes).filter(part=>chapter.id.startsWith(part)).sort((a,b)=>b.length-a.length)[0];
 const remoteBase=audioSites.chapters[chapter.id]||(prefix&&audioSites.prefixes[prefix]);
 if(remoteBase&&!/^https:\/\/luoul-123\.github\.io\/vot-audio-\d{8}\/$/.test(remoteBase))throw Error(`${key}: 音频分站地址无效`);
 for(const index of actual){
  if(remoteBase){remoteCount++;continue;}
  const audio=path.join(root,'public/audio',slug,index+'.mp3');
  const stat=fs.statSync(audio);
  if(stat.size<1000)throw Error(`${audio}: 音频为空`);
  bytes+=stat.size;
 }
 count+=lines.length;
}
const audioRoot=path.join(root,'public/audio');
const audioDirectories=fs.existsSync(audioRoot)?fs.readdirSync(audioRoot,{withFileTypes:true}).filter(entry=>entry.isDirectory()).map(entry=>entry.name):[];
if(!process.argv.includes('--allow-extra-local-audio')&&audioDirectories.length)throw Error('主站仍包含音频目录，请迁移到分站');
if(bytes>=1024*1024*1024)throw Error('音频超过 GitHub Pages 1 GB 限额');
console.log(`Pages verified: ${voiced.length} voiced section(s), ${count} lines, ${remoteCount} remote MP3, ${(bytes/1024/1024).toFixed(1)} MiB local audio`);
