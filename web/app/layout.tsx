import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "舟声 · 剧情剧场", description: "在泰拉的故事里，听见每一个声音。视觉小说式剧情阅读与角色配音。", icons: {icon:"/favicon.svg"} };
export default function Layout({children}:Readonly<{children:React.ReactNode}>){return <html lang="zh-CN"><body>{children}</body></html>;}
