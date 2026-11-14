import {useState} from "react";
import {Pause,Play,ExternalLink,Headphones,ChevronUp,Gauge} from "lucide-react";

type DesktopPetProps={
  chapter:string;
  line:string;
  status:string;
  rate:number;
  onToggle:()=>void;
  onRateChange:(rate:number)=>void;
  onReturn:()=>void;
};

const styles=`
  :root{color-scheme:light;font-family:"Microsoft YaHei","PingFang SC",sans-serif}
  *{box-sizing:border-box}
  html,body,#pet-root{width:100%;height:100%;margin:0}
  body{overflow:hidden;background:#e8f0e5;color:#254239}
  button,input{font:inherit}
  button{cursor:pointer}
  button:focus-visible,input:focus-visible{outline:2px solid #397d65;outline-offset:2px}
  .pet-shell{display:grid;grid-template-rows:minmax(0,1fr) auto;width:100%;height:100%;min-height:300px;overflow:hidden;background:#e8f0e5}
  .pet-stage{position:relative;display:flex;align-items:flex-end;justify-content:center;min-height:0;overflow:hidden;background:radial-gradient(ellipse at 50% 15%,#fffdf4 0,#f3f8eb 42%,transparent 73%),linear-gradient(180deg,#e7f2df 0%,#d9ebda 62%,#b5d1be 100%)}
  .pet-stage:before{content:"";position:absolute;inset:auto -14% -37px;height:42%;border-radius:50% 50% 0 0;background:#8cafab55;transform:rotate(-7deg)}
  .pet-stage:after{content:"";position:absolute;inset:auto -10% -55px;height:35%;border-radius:50% 50% 0 0;background:#7fb29b66;transform:rotate(8deg)}
  .pet-heading{position:absolute;top:15px;left:17px;right:17px;z-index:2;display:flex;align-items:center;justify-content:space-between;gap:8px;color:#32594c;font-size:10px;letter-spacing:.08em}
  .pet-heading strong{font-size:12px;font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .pet-heading span{font-size:10px;color:#587b6d}
  .pet-stage picture{z-index:1;display:flex;align-items:flex-end;justify-content:center;width:100%;height:calc(100% - 37px);pointer-events:none}
  .pet-figure{display:block;width:96%;height:100%;object-fit:contain;object-position:center bottom;filter:drop-shadow(0 10px 9px #395a4844)}
  .pet-dock{position:relative;z-index:3;display:grid;gap:8px;padding:12px 15px 15px;background:#f7fbf4ee;border-top:1px solid #fff;box-shadow:0 -8px 24px #638b7240}
  .pet-now{display:flex;align-items:center;gap:6px;min-width:0;font-size:10px;color:#547263}
  .pet-now svg{flex:none}
  .pet-now strong{font-weight:600;white-space:nowrap}
  .pet-line{margin:0;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#26493e;font-size:11px;line-height:1.45}
  .pet-actions{display:flex;align-items:center;justify-content:center;gap:10px}
  .pet-actions button{display:inline-flex;align-items:center;justify-content:center;gap:5px;min-width:37px;min-height:37px;padding:0 8px;border:1px solid #b9d0be;border-radius:999px;background:#e9f1e8;color:#365f4c;transition:transform .15s,background .15s}
  .pet-actions button:hover{background:#dbead9;transform:translateY(-1px)}
  .pet-actions button:disabled{opacity:.45;cursor:not-allowed;transform:none}
  .pet-actions .pet-play{min-width:85px;height:46px;gap:6px;border-color:#478f70;background:#478f70;color:white;font-weight:650;box-shadow:0 5px 12px #46866850}
  .pet-actions .pet-play:hover{background:#367e60}
  .pet-actions .pet-speed-button{font-size:11px;gap:3px;padding:0 8px}
  .pet-actions .pet-speed-button[aria-expanded="true"]{background:#d9eadb;border-color:#75aa87}
  .pet-actions .pet-return{min-width:37px;padding:0;color:#416953}
  .pet-speed-options{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:5px;padding:7px 0 3px;animation:pet-menu-in .16s ease-out}
  .pet-speed-options button{min-height:28px;padding:3px 0;border:1px solid #c6d8c6;border-radius:6px;background:#edf5eb;color:#436452;font-size:10px}
  .pet-speed-options button:hover,.pet-speed-options button[aria-checked="true"]{background:#478f70;border-color:#478f70;color:white}
  @keyframes pet-menu-in{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
`;

function KaltsitChibi(){
  const base=import.meta.env.BASE_URL+"pet/kaltsit-idle";
  return <picture>
    <source media="(prefers-reduced-motion: reduce)" srcSet={base+".png"}/>
    <img className="pet-figure" src={base+".webp"} alt="《明日方舟》游戏中的凯尔希战斗小人待机动画" draggable={false}/>
  </picture>;
}

export default function DesktopPet({chapter,line,status,rate,onToggle,onRateChange,onReturn}:DesktopPetProps){
  const [speedOpen,setSpeedOpen]=useState(false);
  const paused=status==="paused";
  const statusText=status==="paused"?"已暂停":status==="loading"?"正在准备下一句":status==="error"?"音频加载失败":status==="ended"?"本段已结束":status==="choice"?"等待剧情选择":status==="silent"?"配音已静音":"随身听中";
  const canToggle=!["choice","ended","silent"].includes(status);
  return <>
    <style>{styles}</style>
    <div id="pet-root" className="pet-shell">
      <div className="pet-stage">
        <div className="pet-heading"><strong>凯尔希 · 随身听</strong><span>{chapter}</span></div>
        <KaltsitChibi/>
      </div>
      <div className="pet-dock">
        <div className="pet-now"><Headphones size={12}/><strong>{statusText}</strong></div>
        <p className="pet-line" title={line}>{line||"博士，故事还在继续。"}</p>
        {speedOpen&&<div className="pet-speed-options" role="radiogroup" aria-label="播放速度">
          {[.7,.8,.9,1,1.1,1.2,1.3,1.4,1.5].map(option=><button key={option} type="button" role="radio" aria-checked={Math.abs(rate-option)<.05} onClick={()=>{onRateChange(option);setSpeedOpen(false);}}>{option.toFixed(1)}×</button>)}
        </div>}
        <div className="pet-actions">
          <button className="pet-play" type="button" disabled={!canToggle} onClick={onToggle} aria-label={paused?"继续播放":"暂停播放"}>{paused?<Play size={17} fill="currentColor"/>:<Pause size={17} fill="currentColor"/>}{paused?"播放":"暂停"}</button>
          <button className="pet-speed-button" type="button" onClick={()=>setSpeedOpen(value=>!value)} aria-expanded={speedOpen} aria-label={`播放速度 ${rate.toFixed(1)} 倍，选择速度`}><Gauge size={14}/>{rate.toFixed(1)}×<ChevronUp size={12}/></button>
          <button className="pet-return" type="button" onClick={onReturn} title="回到网页" aria-label="回到网页"><ExternalLink size={17}/></button>
        </div>
      </div>
    </div>
  </>;
}
