import fs from 'node:fs';
import path from 'node:path';
import {parseStory} from '../lib/story.mjs';

const root=path.resolve(import.meta.dirname,'../pages');
const catalog=JSON.parse(fs.readFileSync(path.join(root,'catalog.json'),'utf8'));
const manifest=JSON.parse(fs.readFileSync(path.join(root,'audio-manifest.json'),'utf8'));
const voiced=JSON.parse(fs.readFileSync(path.join(root,'voiced-chapters.json'),'utf8'));
const group=catalog.find(item=>item.id==='act55side');
if(!group||group.chapters.length!==24)throw Error('样例目录不完整');
const chapters=new Map(group.chapters.map(chapter=>[path.basename(chapter.id),chapter]));
if(!voiced.length||voiced.some(slug=>!chapters.has(slug)))throw Error('配音章节配置无效');
if(Object.keys(manifest).some(slug=>!voiced.includes(slug)))throw Error('配音清单包含未发布章节');
let count=0,bytes=0;
for(const chapter of group.chapters){
 const slug=path.basename(chapter.id);
 const source=fs.readFileSync(path.join(root,'public/sample',slug+'.txt'),'utf8');
 if(!voiced.includes(slug))continue;
 const lines=parseStory(source,chapter.id).steps.filter(step=>step.type==='line'&&step.text);
 const expected=lines.map(step=>Number(step.id.split(':').pop()));
 const actual=manifest[slug]||[];
 if(JSON.stringify(expected)!==JSON.stringify(actual))throw Error(`${slug}: 配音清单不完整 (${actual.length}/${expected.length})`);
 for(const index of actual){
  const audio=path.join(root,'public/audio',slug,index+'.mp3');
  const stat=fs.statSync(audio);
  if(stat.size<1000)throw Error(`${audio}: 音频为空`);
  bytes+=stat.size;
 }
 count+=lines.length;
}
const audioDirectories=fs.readdirSync(path.join(root,'public/audio'),{withFileTypes:true}).filter(entry=>entry.isDirectory()).map(entry=>entry.name);
if(audioDirectories.some(slug=>!voiced.includes(slug)))throw Error('音频目录包含未发布章节');
if(bytes>=1024*1024*1024)throw Error('音频超过 GitHub Pages 1 GB 限额');
console.log(`Pages sample verified: ${voiced.length} voiced section(s), ${count} lines, ${(bytes/1024/1024).toFixed(1)} MiB audio`);
