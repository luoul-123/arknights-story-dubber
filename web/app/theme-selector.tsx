"use client";

export type Theme = "dark" | "light";

export default function ThemeSelector({value,onChange}:{value:Theme;onChange:(theme:Theme)=>void}){
 return <div className="setting-row theme-setting">
  <div><b>界面主题</b><p>切换后会保存在当前浏览器</p></div>
  <div className="theme-options" role="group" aria-label="界面主题">
   <button type="button" className={value==="dark"?"selected":""} aria-pressed={value==="dark"} onClick={()=>onChange("dark")}>黑色</button>
   <button type="button" className={value==="light"?"selected":""} aria-pressed={value==="light"} onClick={()=>onChange("light")}>白色</button>
  </div>
 </div>;
}
