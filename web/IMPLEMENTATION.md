# Voice of Terra · 运行与发布

## 在线结构

读者只使用 [Voice of Terra 主网页](https://luoul-123.github.io/voice-of-terra-for-arknights/)。主仓库的 GitHub Pages 发布 React/Vite 静态网页、剧情目录和音频索引，不运行语音后端。剧情文本按需从 ArknightsGamedata 读取；立绘、CG 与音乐按需从公开素材源读取。

凯尔希台词先在维护者电脑上用 GPT-SoVITS 合成，再转为 MP3。音频存放在独立的 [vot-audio-20261101](https://github.com/luoul-123/vot-audio-20261101) Pages 分站。`pages/audio-manifest.json` 记录哪些台词已有配音，`pages/audio-sites.json` 把章节路径映射到音频分站。播放器读取映射后直接加载 MP3，浏览器地址仍停留在主站。以后增加分站时，在映射中配置章节或路径前缀即可；每个 Pages 站点不得超过 [1 GB](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)。

## 剧情目录与存档

当前目录收录 491 个故事组、2,061 个章节。网页内可按剧情分类和国服首次实装时间浏览；README 的两份目录由 `scripts/generate-readme-index.mjs` 从 `pages/catalog.json` 生成。`?group=故事组ID` 可直达对应章节目录，选择章节后继续留在主站。

阅读设置、自动进度和手动存档保存在浏览器 `localStorage`。同一个 `luoul-123.github.io` 主网址的每次更新会继续使用原存档；换设备、换浏览器或清除网站数据不会自动同步。音频分站不保存用户状态。

## 本地开发

本机只负责修改网页、维护目录、生成并发布凯尔希音频。无需启动旧版 `.bat` 网页或对外提供 GPU 服务。保留 `web/pages/`、`web/lib/`、`web/scripts/`、`web/backend/`，以及本地 GPT-SoVITS 引擎、基础模型与凯尔希音色。`web/app/globals.css` 和 `web/app/theme-selector.tsx` 仍供 Pages 界面使用；其余 `web/app/` 属早期本地网页代码。

网页改动在 `web` 目录检查：

~~~powershell
npm ci
node scripts/verify-pages.mjs
npx tsc --noEmit
npm run build:pages
~~~

主站由 `.github/workflows/pages.yml` 在推送 `main` 后构建。音频分站从其仓库 `main` 分支发布静态文件。发布顺序是：**先推送音频分站并确认 MP3 可访问，再更新主站音频清单**，避免网页指向尚未上线的声音。

当前《时间啊，向前！》的逐段发布脚本是 `scripts/publish-audio-sections.py`。它读取 `work/pages-lines.json`，从 `work/vot-audio-20261101/` 的独立 Git 检出中续传。`scripts/generate-pages-audio.py` 跳过已经生成的 MP3，并在完成一节后清理临时 WAV 缓存。首次在新电脑维护时，要先恢复凯尔希模型、准备 GPT-SoVITS 环境、检出音频仓库，并生成对应台词清单；读者无需这些文件。

凯尔希模型的备份在主仓库 [Releases](https://github.com/luoul-123/voice-of-terra-for-arknights/releases/latest) 的 `voice-of-terra-kaltsit.zip`。模型、生成缓存、令牌和工作目录均不提交到主仓库。音色来源见 [凯尔希音色说明](docs/default-voices.md)，素材来源见 [媒体说明](docs/media-sources.md)。
