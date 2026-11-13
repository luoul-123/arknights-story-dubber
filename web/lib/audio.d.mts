export class DialogueAudio {constructor(config?:{debounceMs?:number;fetcher?:typeof fetch;makeAudio?:()=>HTMLAudioElement;onState?:(state:string,message?:string)=>void});setOptions(options:{volume?:number;rate?:number}):void;stop():void;pause():void;resume():Promise<void>;dispose():void;play(line:any,voice:any,options?:any):Promise<void>;prefetch(line:any,voice:any):Promise<void>;}

export function resolveVoice(voices:any[],line:any,override?:any):any;
