import fs from 'node:fs';
import path from 'node:path';
import {CATEGORIES} from '../lib/story.mjs';

const repo=path.resolve(import.meta.dirname,'../..');
const readme=path.join(repo,'README.md');
const catalog=JSON.parse(fs.readFileSync(path.join(repo,'web/pages/catalog.json'),'utf8'));
const page='https://luoul-123.github.io/voice-of-terra-for-arknights/';
const start='<!-- story-index:start -->';
const end='<!-- story-index:end -->';
const dateOf=group=>group.date&&group.date!=='日期待补'?group.date:'日期待补';
const ordered=[...catalog].sort((a,b)=>(a.releasedAt||Infinity)-(b.releasedAt||Infinity)||a.groupSort-b.groupSort||a.id.localeCompare(b.id));
const escaped=text=>String(text).replace(/([\\`*_[\]])/g,'\\$1');
const row=group=>`- ${dateOf(group)} · [${escaped(group.operator?group.operator+' · '+group.title:group.title)}](${page}?group=${encodeURIComponent(group.id)})（${group.chapters.length} 段）`;
const lines=['### 按剧情分类',''];
for(const category of CATEGORIES){
  const groups=ordered.filter(group=>group.category===category.id);
  if(!groups.length)continue;
  lines.push(`<details><summary>${category.label} · ${groups.length} 部</summary>`,'',...groups.map(row),'','</details>','');
}
lines.push('### 按实装顺序','');
const years=new Map();
for(const group of ordered){
  const year=dateOf(group).slice(0,4);
  if(!years.has(year))years.set(year,[]);
  years.get(year).push(group);
}
for(const [year,groups] of years){
  lines.push(`<details><summary>${year} · ${groups.length} 部</summary>`,'',...groups.map(group=>`- ${row(group).slice(2)} · ${CATEGORIES.find(category=>category.id===group.category)?.label||'其他'}`),'','</details>','');
}
const source=fs.readFileSync(readme,'utf8');
const left=source.indexOf(start),right=source.indexOf(end);
if(left<0||right<left||source.indexOf(start,left+start.length)>=0||source.indexOf(end,right+end.length)>=0)throw Error('README index markers are missing or duplicated');
fs.writeFileSync(readme,source.slice(0,left+start.length)+'\n\n'+lines.join('\n').trimEnd()+'\n\n'+source.slice(right),'utf8');
console.log(`README story indexes: ${catalog.length} groups, ${years.size} date buckets`);
