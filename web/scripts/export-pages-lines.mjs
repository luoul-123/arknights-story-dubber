import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {catalogFrom,parseStory} from '../lib/story.mjs';

const root=path.resolve(import.meta.dirname,'../.voice-data/stories');
const catalog=JSON.parse(fs.readFileSync(path.join(root,'catalog.json'),'utf8'));
const group=catalogFrom(catalog).find(item=>item.id==='act55side');
if(!group)throw Error('没有找到《时间啊，向前！》');
const lines=[];
const sampleRoot=path.resolve(import.meta.dirname,'../pages/public/sample');
fs.mkdirSync(sampleRoot,{recursive:true});
for(const chapter of group.chapters){
  const file=path.join(root,crypto.createHash('sha256').update(chapter.id).digest('hex')+'.txt');
  if(!fs.existsSync(file))throw Error('缺少章节缓存：'+chapter.id);
  const raw=fs.readFileSync(file,'utf8');
  fs.writeFileSync(path.join(sampleRoot,path.basename(chapter.id)+'.txt'),raw.replace(/[ \t]+(?=\r?$)/gm,''));
  const steps=parseStory(raw,chapter.id).steps;
  for(const step of steps){
    if(step.type!=='line'||!step.text)continue;
    if(step.text.length>600)throw Error('台词超过模型上限：'+step.id);
    lines.push({id:step.id,text:step.text});
  }
}
const target=path.resolve(import.meta.dirname,'../work/pages-lines.json');
fs.mkdirSync(path.dirname(target),{recursive:true});
fs.writeFileSync(target,JSON.stringify(lines));
console.log(`${lines.length} 句，${new Set(lines.map(line=>line.text)).size} 种文本，输出 ${target}`);
