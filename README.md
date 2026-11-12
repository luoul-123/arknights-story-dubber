# 舟声 · 明日方舟有声视觉小说

在浏览器里看剧情、听角色对话和旁白，也可以切换到「随身听」连续收听。

网站直接读取剧情脚本，呈现背景、人物立绘、CG、底部对话框和分支选项。用户无需截图识别、安装桌面插件、上传录音或训练角色。

## 已实现

| 功能 | 行为 |
| --- | --- |
| 视觉小说阅读 | 章节目录、背景 / 立绘 / CG、逐字显示、分支选择、对话回顾 |
| 自动配音 | 已发布角色使用专属音色；其余角色、NPC、未知说话人自动使用通用中文声音 |
| 有声旁白 | 旁白自动朗读，无需读者另行设置 |
| 随身听 | 每句播放完自动继续，支持暂停和继续；遇到分支等待选择 |
| 立即跳句 | 中断当前播放并进入下一句；旧合成请求晚到也不会串音 |
| 剧情缓存 | 目录和打开过的章节保存在本机；主来源失败时尝试备用来源，缓存过期也可先阅读 |
| 阅读进度 | 当前浏览器自动保存进度，可继续上次阅读 |
| 管理员工作室 | 按干员名导入一段游戏语音，或上传短录音，试听并统一发布音色 |
| 免训练优先 | GPT-SoVITS 预训练模型 + 参考语音；单独训练仅作为可选优化 |

普通读者只需选择章节。NPC 和旁白无需逐个配置；管理员可在以后补充或替换专属音色。通用声音不等于角色原声，游戏已有语音仅作为合成新台词的参考。

## 在这台电脑使用

1. 双击根目录的 **启动网页版.bat**。
2. 浏览器打开后进入剧情，或点击右上角 **随身听**。
3. 使用结束后双击 **停止网页版.bat**。

本机地址为 http://127.0.0.1:5173/ 。启动器自动准备本地服务密钥，并打开本地管理员会话；只监听本机，不需要购买服务器或域名。

阅读时点击可补全文字，再次点击推进；底部跳过按钮可以立即停止当前配音并跳到下一句。设置中可以关闭逐字显示。

## 从 GitHub 首次安装

当前验证环境为 Windows。需要 Node.js 22.13+、Python 3.11+ 和 Git。基础阅读、通用角色及旁白使用 Windows 已安装的中文语音，专属角色克隆另需 GPT-SoVITS 引擎与合适的 NVIDIA GPU。

在 PowerShell 中运行：

~~~powershell
git clone https://github.com/luoul-123/arknights-story-dubber.git
cd arknights-story-dubber
py -3 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
cd web
npm ci
cd ..
./启动网页版.bat
~~~

### 可选：专属角色音色

~~~powershell
./.venv/Scripts/python.exe web/backend/setup_engine.py
~~~

安装器将引擎、独立 Python 和预训练模型下载到本项目目录，首次需要下载数 GB 文件。仅准备录音转写模型可追加 --asr-only。

之后打开网站的「音色工作室」：输入干员名 → 导入干员语音 → 试听 → 发布。也可上传一段清晰的 3–10 秒参考录音并校对对应文字。无需给每个角色单独训练；未发布专属音色的角色仍然可以使用通用声音。

仓库不包含本机录音、角色模型、缓存或服务密钥。验证时使用过的阿米娅、杜宾音色也不会随 GitHub 克隆分发。

## 架构与目录

浏览器播放剧情 → 网站服务端代理 → 本机语音服务 → GPT-SoVITS 或 Windows 中文语音 → 音频缓存与浏览器播放。

- web/app：视觉小说界面、音色工作室、剧情与配音 API。
- web/lib：剧情脚本解析、分支场景和可中断音频播放器。
- web/backend：语音合成、默认旁白 / NPC 配音、素材导入、转写及可选训练。
- web/tests：剧情与音频测试、真实浏览器检查。
- engines/、models/、web/.voice-data/：本机引擎和语音数据，均不提交。

旧桌面 UI、屏幕采集、OCR、桌面启动入口及旧界面截图已移除。

## 开发与验证

~~~powershell
cd web
node --test tests/core.test.mjs
../.venv/Scripts/python.exe -m unittest discover -s backend -p "test_*.py"
npx tsc --noEmit
npm run build
~~~

本机网站启动后，可运行 node tests/browser-smoke.mjs，使用隐藏 Edge 验证真实页面、后台连续播放、暂停、跳句和分支等待，测试全程静音。

[详细运行与部署说明](web/IMPLEMENTATION.md) · [验证记录](web/VALIDATION.md) · [贡献指南](CONTRIBUTING.md)

## 当前范围

- 已验证桌面 Edge 切换到其他标签页后的连续播放；手机锁屏与系统媒体按钮尚未实机验证。
- 当前通用中文配音依赖 Windows 系统语音，Linux 部署还需接入相应 TTS 服务。
- 专属音色首次加载模型可能较慢，之后的预热请求及缓存命中更快；尚未实现整章预先生成。
- 已实现常用剧情演出；复杂动画、完整表情叠层、音乐资源映射及所有特殊脚本指令尚未完整支持。
- 剧情目录与首次打开的章节通过本机后端读取上游资源，支持系统代理、GitHub / jsDelivr 来源回退及磁盘缓存；缓存过期时先返回已有内容，再后台更新。图片仍按需联网读取。本机版本尚未作为公网服务部署；生产部署需配置真实身份认证、服务密钥及语音后端。

## 来源与许可

原创代码采用 [MIT](LICENSE) 许可证。剧情文本、立绘、CG、背景与角色录音归鹰角网络及相应权利人，独立于代码许可。

剧情数据来自 [ArknightsGamedata](https://github.com/ArknightsAssets/ArknightsGamedata)，图像与参考语音来自 [ArknightsAssets2](https://github.com/ArknightsAssets/ArknightsAssets2)，角色声音合成使用 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)。未使用泰拉文库的前端源码。

这是非官方同人项目，AI 合成台词不是官方剧情配音。
