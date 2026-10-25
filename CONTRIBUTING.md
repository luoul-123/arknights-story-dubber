# 参与贡献

感谢帮助改进舟声。请先在 Issue 中说明较大的功能改动，避免重复工作；小型修复可以直接提交 Pull Request。

## 报告问题

请写明 Windows 和 Python 版本、复现步骤、预期与实际结果，以及相关错误信息。截图和日志在上传前请检查个人信息、游戏账号、录音和本机路径。涉及声音克隆的问题可以使用自制或已获授权的测试素材复现。

## 开发与提交

1. Fork 仓库，在自己的分支中修改代码。
2. 按 [README](README.md) 的“启动”步骤安装依赖。语音模型和独立运行环境由应用按需下载，不提交到 Git。
3. 运行相关测试：`.\.venv\Scripts\python.exe -m unittest test_app test_story_matcher`。
4. 提交 Pull Request，说明改动、验证方式及关联 Issue。界面改动可附前后截图。

不要提交 `.venv/`、`engines/`、`models/`、`voice_profiles/`、`.demo_cache/`、`app_settings.json`，也不要提交无权分发的剧情文本、游戏录音、训练模型或第三方软件。新增素材请在 `assets/SOURCES.md` 中说明来源和使用范围。

项目原创代码采用 MIT 许可证；第三方素材保留各自的权利。提交贡献即表示你有权提交相应内容，并同意该代码按项目的 MIT 许可证分发。
