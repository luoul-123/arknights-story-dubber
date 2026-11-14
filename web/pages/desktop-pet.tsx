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
  .pet-figure{position:absolute;inset:24px 8px 19px;width:calc(100% - 16px);height:calc(100% - 43px);filter:drop-shadow(0 8px 13px #071311aa)}
  .pet-character{transform-origin:100px 180px;animation:pet-bob 3s ease-in-out infinite}
  .pet-tail{transform-origin:145px 151px;animation:pet-tail 2.5s ease-in-out infinite}
  .pet-ear-left{transform-origin:66px 44px;animation:pet-ear 6s ease-in-out infinite}
  .pet-ear-right{transform-origin:135px 44px;animation:pet-ear 6s ease-in-out 1.2s infinite}
  .pet-eyes{transform-origin:100px 91px;animation:pet-blink 5.5s infinite}
  .pet-arm{transform-origin:143px 131px;animation:pet-wave 3.5s ease-in-out infinite}
  .pet-shell:hover .pet-character{animation-duration:2.1s}
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
  @keyframes pet-bob{0%,100%{transform:translateY(0) rotate(-1deg)}50%{transform:translateY(-5px) rotate(1deg)}}
  @keyframes pet-tail{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(7deg)}}
  @keyframes pet-ear{0%,88%,100%{transform:rotate(0)}92%{transform:rotate(-6deg)}96%{transform:rotate(2deg)}}
  @keyframes pet-blink{0%,45%,48%,100%{transform:scaleY(1)}46%,47%{transform:scaleY(.12)}}
  @keyframes pet-wave{0%,100%{transform:rotate(-2deg)}50%{transform:rotate(7deg)}}
  @media(prefers-reduced-motion:reduce){.pet-character,.pet-tail,.pet-ear-left,.pet-ear-right,.pet-eyes,.pet-arm{animation:none}}
`;

function KaltsitChibi(){
  return <svg className="pet-figure" viewBox="0 0 200 205" role="img" aria-label="会轻晃和眨眼的凯尔希 Q 版小人">
    <defs>
      <linearGradient id="pet-hair" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#eef1e7"/><stop offset=".55" stopColor="#bfc9bf"/><stop offset="1" stopColor="#889d96"/></linearGradient>
      <linearGradient id="pet-coat" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#314748"/><stop offset="1" stopColor="#142728"/></linearGradient>
      <linearGradient id="pet-accent" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#cce4bd"/><stop offset="1" stopColor="#78b8a1"/></linearGradient>
    </defs>
    <ellipse cx="100" cy="194" rx="55" ry="8" fill="#071512" opacity=".55"/>
    <g className="pet-tail"><path d="M139 151c24-8 42 7 30 19-7 8-20 3-21-5" fill="none" stroke="#263a3b" strokeWidth="17" strokeLinecap="round"/><path d="M139 151c24-8 42 7 30 19" fill="none" stroke="#aabdb2" strokeWidth="5" strokeLinecap="round"/></g>
    <g className="pet-character">
      <path d="M62 67c-19 12-22 54-14 87l18 6 16-28h38l18 28 18-5c7-33 2-70-18-88Z" fill="url(#pet-hair)" stroke="#6e8580" strokeWidth="2"/>
      <path d="M70 139l-16 34 20 17 26-8 28 8 19-17-17-34Z" fill="#1b2c2e" stroke="#0d1d1d" strokeWidth="3"/>
      <path d="M74 176l-3 18 21 4 6-18m30-4 3 18-21 4-7-18" fill="#162528" stroke="#0c1a1c" strokeWidth="3"/>
      <path d="M55 121c-17 9-19 34-20 48l22 5 17-31m71-21c17 9 19 34 20 48l-22 5-17-31" fill="url(#pet-coat)" stroke="#0e2122" strokeWidth="3"/>
      <path d="M50 164l-10 8 17 8 10-7m87-9 10 8-17 8-10-7" fill="#d3d7ca" stroke="#758d82" strokeWidth="2"/>
      <g className="pet-arm"><path d="M139 129c14-2 22 7 22 20l-14 7-15-15Z" fill="#2f4744" stroke="#0e2221" strokeWidth="3"/><path d="M155 145l11-4 7 13-11 6Z" fill="#d2d9c8" stroke="#738c81" strokeWidth="2"/></g>
      <path d="M73 120c14-11 40-14 55 0l14 51-22 17-20-11-21 11-21-17Z" fill="url(#pet-coat)" stroke="#0c2021" strokeWidth="3"/>
      <path d="M85 122l15 15 15-15-2 52-13 7-13-7Z" fill="#e5e9dd"/>
      <path d="M84 120l16 17-16 22-10-28m42-11-16 17 16 22 10-28" fill="#799d91" stroke="#426d63" strokeWidth="2"/>
      <path d="M98 137h5l3 20-6 8-6-8Z" fill="#4b776b"/>
      <path d="M70 167c20 10 42 10 61 0" fill="none" stroke="#b2d3b6" strokeWidth="3"/>
      <path d="M94 165h12v9H94Z" fill="#cddcc4" stroke="#577369" strokeWidth="2"/>
      <g className="pet-ear-left"><path d="M58 58 56 21q0-8 7-6l28 24Z" fill="url(#pet-hair)" stroke="#6b817d" strokeWidth="3"/><path d="m64 47-2-23 19 17Z" fill="#d9b4ae"/></g>
      <g className="pet-ear-right"><path d="m111 39 28-24q7-2 7 6l-2 37Z" fill="url(#pet-hair)" stroke="#6b817d" strokeWidth="3"/><path d="m120 41 19-17-2 23Z" fill="#d9b4ae"/></g>
      <path d="M54 66c2-31 22-45 47-45 27 0 47 15 48 45l-7 35c-10 20-25 29-42 29s-33-9-42-29Z" fill="url(#pet-hair)" stroke="#718982" strokeWidth="2"/>
      <path d="M66 73c-3-24 14-38 35-38s38 14 35 38v23c-7 18-20 29-35 29S73 114 66 96Z" fill="#f4e5d7" stroke="#a99e93" strokeWidth="2"/>
      <path d="M66 72c11-19 18-19 28-22l7 17 8-18c13 6 21 10 27 24l9 5c1-31-16-50-44-50S56 47 57 78Z" fill="url(#pet-hair)" stroke="#789087" strokeWidth="2"/>
      <path d="M56 74c-2 21 2 35 12 44l7-27-3-24m72 7c2 21-2 35-12 44l-7-27 3-24" fill="url(#pet-hair)" stroke="#718982" strokeWidth="2"/>
      <g className="pet-eyes"><path d="M77 88c5-4 10-4 15 0m17 0c5-4 10-4 15 0" fill="none" stroke="#43645d" strokeWidth="3" strokeLinecap="round"/><ellipse cx="85" cy="94" rx="5" ry="6" fill="#6fa58c"/><ellipse cx="117" cy="94" rx="5" ry="6" fill="#6fa58c"/><circle cx="86" cy="92" r="1.8" fill="#f6fff2"/><circle cx="118" cy="92" r="1.8" fill="#f6fff2"/></g>
      <path d="M99 101q2 2 4 0" fill="none" stroke="#a98580" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M95 110q6 4 12 0" fill="none" stroke="#9a706d" strokeWidth="1.7" strokeLinecap="round"/>
      <path d="M82 108q-4 3-8 1m52-1q4 3 8 1" fill="none" stroke="#dea9a0" strokeWidth="2" strokeLinecap="round" opacity=".65"/>
      <path d="M66 66c-7-11-2-23 8-30m65 30c7-11 2-23-8-30" fill="none" stroke="#f5f6ed" strokeWidth="4" strokeLinecap="round" opacity=".75"/>
      <path d="M63 72c-6 27-5 43 2 53m74-53c6 27 5 43-2 53" fill="none" stroke="#dce4d8" strokeWidth="4" strokeLinecap="round"/>
    </g>
  </svg>;
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
