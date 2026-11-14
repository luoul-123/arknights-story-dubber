import {Pause,Play,ExternalLink} from "lucide-react";

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
  :root{color-scheme:dark;font-family:"Microsoft YaHei","PingFang SC",sans-serif}
  *{box-sizing:border-box}
  html,body,#pet-root{width:100%;height:100%;margin:0}
  body{overflow:hidden;background:#101b1d;color:#eaf2e9}
  button,input{font:inherit}
  button{cursor:pointer}
  button:focus-visible,input:focus-visible{outline:2px solid #c6e5bd;outline-offset:2px}
  .pet-shell{position:relative;width:100%;height:100%;min-height:230px;overflow:hidden;background:radial-gradient(circle at 50% 42%,#34514b 0,#182d2c 52%,#101b1d 100%)}
  .pet-shell:before{content:"";position:absolute;inset:7px;border:1px solid #b9dab222;border-radius:13px;pointer-events:none}
  .pet-heading{position:absolute;top:15px;left:18px;right:18px;z-index:2;display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:10px;letter-spacing:.12em;color:#bcd5bd}
  .pet-heading strong{font-size:11px;font-weight:600;color:#ecf5e8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .pet-status{position:absolute;left:15px;right:15px;bottom:18px;z-index:2;text-align:center;font-size:11px;color:#dcead7;text-shadow:0 1px 8px #071311;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:opacity .2s}
  .pet-figure{position:absolute;top:27px;left:9px;width:calc(100% - 18px);height:calc(100% - 53px);object-fit:contain;filter:drop-shadow(0 8px 13px #071311aa)}
  .pet-shell:hover .pet-status,.pet-shell:focus-within .pet-status{opacity:0}
  .pet-controls{position:absolute;left:9px;right:9px;bottom:9px;z-index:3;padding:11px;border:1px solid #c6e7bf55;border-radius:10px;background:#0c1b1dec;box-shadow:0 8px 24px #0008;opacity:0;pointer-events:none;transform:translateY(8px);transition:opacity .2s,transform .2s}
  .pet-shell:hover .pet-controls,.pet-shell:focus-within .pet-controls{opacity:1;pointer-events:auto;transform:translateY(0)}
  .pet-controls .pet-line{font-size:10px;line-height:1.4;color:#bed5bc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:0 0 8px}
  .pet-actions{display:flex;align-items:center;gap:7px}
  .pet-actions button{display:inline-flex;align-items:center;justify-content:center;gap:5px;min-height:32px;padding:5px 9px;border:1px solid #aecba852;border-radius:6px;background:#203832;color:#eaf5e7;font-size:11px;white-space:nowrap}
  .pet-actions button:hover{background:#345747}
  .pet-actions button:disabled{opacity:.5;cursor:not-allowed}
  .pet-actions .pet-play{background:#c8e7bb;color:#19352c;border-color:#c8e7bb;font-weight:700}
  .pet-actions .pet-play:hover{background:#def3d5}
  .pet-actions .pet-return{margin-left:auto}
  .pet-speed{display:flex;align-items:center;gap:7px;margin-top:8px;font-size:10px;color:#c5d9c3}
  .pet-speed input{flex:1;min-width:0;accent-color:#c8e7bb}
  .pet-speed b{min-width:28px;text-align:right;font-weight:600;color:#eaf5e7}
`;

function KaltsitChibi(){
  const base=import.meta.env.BASE_URL+"pet/kaltsit-idle";
  return <picture>
    <source media="(prefers-reduced-motion: reduce)" srcSet={base+".png"}/>
    <img className="pet-figure" src={base+".webp"} alt="《明日方舟》游戏中的凯尔希战斗小人待机动画" draggable={false}/>
  </picture>;
}

export default function DesktopPet({chapter,line,status,rate,onToggle,onRateChange,onReturn}:DesktopPetProps){
  const paused=status==="paused";
  const statusText=status==="paused"?"已暂停":status==="loading"?"正在准备下一句":status==="error"?"音频加载失败":status==="ended"?"本段已结束":status==="choice"?"等待剧情选择":status==="silent"?"配音已静音":"随身听中";
  const canToggle=!["choice","ended","silent"].includes(status);
  return <>
    <style>{styles}</style>
    <div id="pet-root" className="pet-shell">
      <div className="pet-heading"><strong>凯尔希 · 随身听</strong><span>{chapter}</span></div>
      <KaltsitChibi/>
      <div className="pet-status">{statusText} · 鼠标悬浮可操作</div>
      <div className="pet-controls">
        <p className="pet-line" title={line}>{line||"博士，故事还在继续。"}</p>
        <div className="pet-actions">
          <button className="pet-play" type="button" disabled={!canToggle} onClick={onToggle} aria-label={paused?"继续播放":"暂停播放"}>{paused?<Play size={14} fill="currentColor"/>:<Pause size={14} fill="currentColor"/>}{paused?"播放":"暂停"}</button>
          <button className="pet-return" type="button" onClick={onReturn} aria-label="回到网页"><ExternalLink size={13}/>回到网页</button>
        </div>
        <label className="pet-speed"><span>速度</span><input aria-label="桌宠播放速度" type="range" min=".7" max="1.5" step=".1" value={rate} onChange={event=>onRateChange(Number(event.target.value))}/><b>{rate.toFixed(1)}×</b></label>
      </div>
    </div>
  </>;
}
