export const DATA_ROOT:string;export const MEDIA_ROOT:string;
export function attrs(source?:string):Record<string,string>;
export function imageUrl(kind:string,name?:string):string|null;
export function parseStory(raw:string,id?:string):{id:string;steps:any[];warnings:string[]};
export function clean(text:string):string;
export function nextIndex(steps:any[],from:number,choice:string|null):number;
export function catalogFrom(raw:any):any[];
export function resolveScene(steps:any[],index:number,decisions?:Record<string,string>):{background:string|null;cg:string|null;actors:{key:string;url:string}[];focus:number};
