import fs from 'node:fs';
import path from 'node:path';
import {parseStory} from '../lib/story.mjs';

const pages=path.resolve(import.meta.dirname,'../pages');
const catalog=JSON.parse(fs.readFileSync(path.join(pages,'catalog.json'),'utf8'));
const groupId=process.argv[2]||'act55side';
const group=catalog.find(item=>item.id===groupId);
if(!group?.chapters.length)throw Error(`找不到故事组：${groupId}`);
const sourceDir=groupId==='act55side'?path.join(pages,'public/sample'):path.join(pages,'public/story',groupId);

const lines=[];
for(const chapter of group.chapters){
  const slug=path.basename(chapter.id);
  const file=path.join(sourceDir,slug+'.txt');
  const raw=fs.readFileSync(file,'utf8');
  for(const step of parseStory(raw,chapter.id).steps){
    if(step.type!=='line'||!step.text)continue;
    if(step.text.length>600)throw Error('台词超过模型上限：'+step.id);
    lines.push({id:step.id,text:step.text});
  }
}
const output=groupId==='act55side'?'pages-lines.json':`pages-lines-${groupId}.json`;
const target=path.resolve(import.meta.dirname,'../work',output);
fs.mkdirSync(path.dirname(target),{recursive:true});
fs.writeFileSync(target,JSON.stringify(lines));
console.log(`${lines.length} 句，${new Set(lines.map(line=>line.text)).size} 种文本，输出 ${target}`);
