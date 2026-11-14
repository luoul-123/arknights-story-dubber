# 参与贡献

泰拉之声的公开入口是 [GitHub Pages 主网页](https://luoul-123.github.io/voice-of-terra-for-arknights/)。较大的功能改动建议先开 Issue；明确的问题可直接提交 Pull Request。

## 报告问题

请给出故事标题、章节、台词位置、浏览器与复现步骤。配音问题请附“有声”标记是否出现、是否开启随身听，以及对应的音频请求状态。立绘、CG、音乐和剧情文本由外部公开素材源提供，网络故障也请注明。

## 修改网页

网页代码在 `web/pages/`，共用剧情逻辑在 `web/lib/`，样式在 `web/app/globals.css`。README 双目录由 `web/scripts/generate-readme-index.mjs` 生成。提交前在 `web` 目录执行：

~~~powershell
npm ci
node scripts/verify-pages.mjs
npx tsc --noEmit
npm run build:pages
~~~

目录数据变化时，另运行 `node scripts/generate-readme-index.mjs` 并提交更新后的 README。当前在线站点只播放预生成的凯尔希配音；网页改动不应要求读者运行 Python、GPU 服务或本地 `.bat`。

## 音频发布

新音频先进入独立的 [音频分站](https://github.com/luoul-123/vot-audio-20261101)，确认公开 MP3 可访问后，再更新主站的 `web/pages/audio-manifest.json` 与 `web/pages/audio-sites.json`。详细流程见 [运行与发布](web/IMPLEMENTATION.md)。不要将模型、训练样本、生成缓存、令牌或 `web/work/` 提交到主仓库。

原创代码按 [MIT 许可证](LICENSE)分发；剧情、音乐、立绘、CG 和角色录音属于相应权利人。提交贡献前请确认自己有权提供相应内容。
