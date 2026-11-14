import fs from 'node:fs';
import path from 'node:path';
import {parseStory} from '../lib/story.mjs';

const pages=path.resolve(import.meta.dirname,'../pages');
const catalog=JSON.parse(fs.readFileSync(path.join(pages,'catalog.json'),'utf8'));
const group=catalog.find(item=>item.id==='act55side');
if(!group||group.chapters.length!==24)throw Error('《时间啊，向前！》目录不完整');

const lines=[];
for(const chapter of group.chapters){
  const slug=path.basename(chapter.id);
  const file=path.join(pages,'public/sample',slug+'.txt');
  const raw=fs.readFileSync(file,'utf8');
  for(const step of parseStory(raw,chapter.id).steps){
    if(step.type!=='line'||!step.text)continue;
    if(step.text.length>600)throw Error('台词超过模型上限：'+step.id);
    lines.push({id:step.id,text:step.text});
  }
}
const target=path.resolve(import.meta.dirname,'../work/pages-lines.json');
fs.mkdirSync(path.dirname(target),{recursive:true});
fs.writeFileSync(target,JSON.stringify(lines));
console.log(`${lines.length} 句，${new Set(lines.map(line=>line.text)).size} 种文本，输出 ${target}`);
