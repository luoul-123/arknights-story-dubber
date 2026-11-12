# 参与贡献

较大的功能改动建议先通过 Issue 讨论；修复问题可直接提交 Pull Request。

## 报告问题

请写明系统、浏览器、Node.js 与 Python 版本，以及复现步骤、预期结果和实际结果。配音问题请注明是通用旁白 / NPC 声音，还是已发布的角色音色。

## 开发与提交

1. 按 [README](README.md) 安装网页版及后端依赖。
2. 在自己的分支中修改；用户入口和管理操作均在网页内，不再添加桌面 UI 或 OCR 依赖。
3. 在 web 目录运行 node --test tests/core.test.mjs、..\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py"、npx tsc --noEmit 和 npm run build。
4. 涉及播放流程时，启动本机服务后运行 node tests/browser-smoke.mjs；面板、目录或段落衔接改动同时运行 node tests/browser-navigation.mjs；录音室上传改动可运行 node tests/browser-reader-voice.mjs（需本机佩丽卡参考素材）。这些检查顺序执行，使用 Windows Edge 并静音。
5. 提交时说明改动、验证方式及尚未验证的范围。

不要提交 .venv/、engines/、models/、voice_profiles/、web/.voice-data/、web/work/、web/.dev.vars、环境密钥、录音或训练模型。日志和截图上传前应检查个人信息及本机路径。第三方剧情和素材不作为模型或代码附件分发。

原创代码采用 MIT 许可证；第三方素材保留各自权利。提交贡献即表示你有权提交相应内容，并同意原创代码按 MIT 许可证分发。
