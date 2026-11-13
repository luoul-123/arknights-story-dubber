# 泰拉之声 · 明日方舟有声视觉小说

在浏览器里看剧情、听对话和旁白，也可以开启「随身听」连续收听。网站直接读取剧情脚本，呈现背景、立绘差分、CG、对话框和分支选项。

## 已实现

| 功能 | 行为 |
| --- | --- |
| 剧情阅读 | 逐字显示、分支选择、对话回顾、手动存档与自动进度 |
| 朗读音色 | 阿米娅、凯尔希、佩丽卡、男管理员、女管理员五选一；全部台词和旁白使用所选声音 |
| 随身听 | 播放结束自动继续；打开目录、回顾、设置仍持续播放，遇到分支或段落结束等待确认 |
| 连续跳句 | 合并快速跳过请求，后端丢弃尚未执行的旧台词；旧音频不会串音 |
| 剧情档案 | 主线、SideStory、故事集、个人密录等分类；国服实装时间线按章节或活动合集展示 |
| 底部导航 | 左侧“上一句”返回台词；右侧“下一章”按目录顺序进入下一段（行动前 → 行动后） |
| 段落衔接 | 读完后确认进入下一段，保持行动前 / 行动后及关卡顺序 |
| 音乐与演出 | 按剧情脚本切换背景音乐、立绘表情和姿态；音乐、配音音量独立调节 |
| 阅读设置 | 逐字显示、音量、语速及开发者日志 |
| 存档恢复 | 刷新优先恢复手动存档，没有手动存档时恢复自动进度 |
| 资源缓存 | 已读取的目录、章节和媒体缓存在本机，网络失败时保留已有内容 |

读者无需上传、录制或训练声音。音色选择保存在浏览器中，首次默认阿米娅。只在服务器保存五个预设模型，浏览器按需接收音频，不下载模型。

## 在这台电脑使用

1. 双击根目录的 **启动网页版.bat**。
2. 浏览器打开后进入剧情，或点击右上角 **随身听**。
3. 在 **朗读音色设置** 选择声音；阅读设置可分别调节音乐和配音。
4. 使用结束后双击 **停止网页版.bat**。

本机地址为 http://127.0.0.1:5173/ 。启动器准备本地服务密钥并打开本地会话，只监听本机。网页需要本地服务提供剧情和语音，不能直接双击 HTML 完成全部功能。

## 从 GitHub 首次安装

当前验证环境为 Windows，需要 Node.js 22.13+、Python 3.11+ 和 Git。GPT-SoVITS 音色合成另需引擎及合适的 NVIDIA GPU。

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

引擎安装：

~~~powershell
./.venv/Scripts/python.exe web/backend/setup_engine.py
~~~

首次安装引擎需要下载数 GB 文件。仓库包含音色素材来源清单和准备工具；录音、训练权重、缓存及密钥不随源码分发。首次克隆时五个预设显示“音色准备中”，管理员需在后端准备并发布音色；没有预设时本机可用 Windows 中文系统声音阅读。详见 [音色准备说明](web/docs/default-voices.md)。

## 架构与目录

浏览器阅读 / 播放 → 网站服务端代理 → 本机语音服务 → GPT-SoVITS → 音频缓存。

- web/app：视觉小说界面、朗读音色设置、剧情与配音 API。
- web/lib：剧情脚本解析、分支场景和可中断播放器。
- web/backend：素材下载、训练、发布、语音合成与媒体读取。
- web/tests：剧情、音频与真实浏览器回归检查。
- engines/、models/、web/.voice-data/：本机运行数据，均不提交。

旧桌面 UI、OCR、录音室上传入口已移除。五个音色全部使用网络游戏语音重新准备；此前个人录音、旧角色模型、陈和杜宾等旧预设已从本机角色库删除。

## 开发与验证

~~~powershell
cd web
node --test tests/core.test.mjs
../.venv/Scripts/python.exe -m unittest discover -s backend -p "test_*.py"
npx tsc --noEmit
npm run build
~~~

本机服务启动后，可顺序运行 tests/browser-smoke.mjs、tests/browser-navigation.mjs、tests/browser-media-save.mjs、tests/browser-preset-settings.mjs、tests/browser-rapid-skip.mjs、tests/browser-bottom-navigation.mjs。浏览器检查使用隐藏 Edge 并静音，覆盖后台播放、面板操作、下一段确认、立绘音乐、存档及预设选择。

[运行与部署说明](web/IMPLEMENTATION.md) · [验证记录](web/VALIDATION.md) · [贡献指南](CONTRIBUTING.md)

## 当前范围

- 桌面 Edge 后台播放已验证；手机锁屏和系统媒体按钮尚未实机验证。
- 首次加载模型、切换音色仍有等待时间。连续跳句会丢弃旧排队任务，但已经进入 GPU 的一次合成仍需结束；尚未实现整章预生成。
- 当前目录 491 组 / 2,061 段。活动分周开放日期未逐关补齐，默认按活动首发日期归组。见 [日期来源](web/docs/catalog-sources.md)。
- 支持常用剧情演出、立绘差分和音乐；复杂连续动画及部分特殊脚本指令尚未完整支持。
- 未缓存资源需联网；本机版本未作为公网服务部署。生产部署需真实身份认证、服务密钥及语音后端，Linux 尚未实机验证。

## 来源与许可

原创代码采用 [MIT](LICENSE) 许可证。剧情文本、立绘、CG、音乐及角色录音归鹰角网络及相应权利人，独立于代码许可。

剧情数据来自 [ArknightsGamedata](https://github.com/ArknightsAssets/ArknightsGamedata)，图片和《明日方舟》语音来自 [ArknightsAssets2](https://github.com/ArknightsAssets/ArknightsAssets2)，声音合成使用 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)。终末地素材来自社区 [Warfarin 佩丽卡语音页](https://warfarin.wiki/cn/operators/perlica) 和 [管理员语音页](https://warfarin.wiki/cn/operators/endministrator)。

这是非官方同人项目，AI 合成台词不是官方剧情配音。
