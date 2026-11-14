# Voice of Terra · 泰拉之声

## 功能

Voice of Terra 是在浏览器中阅读和收听《明日方舟》剧情的非官方同人项目。

| 功能 | 说明 |
| --- | --- |
| 剧情剧场 | 展示背景、角色立绘及表情、CG、对话和分支选项；支持逐字显示与对话回顾 |
| 角色配音 | 阿米娅、凯尔希、佩丽卡、男管理员、女管理员五种音色可选，所选音色朗读台词和旁白 |
| 随身听 | 播放完一句后自动继续；遇到分支或段落结束时等待选择或确认 |
| 剧情档案 | 按主线、SideStory、故事集、个人密录等分类浏览，支持搜索和时间线 |
| 音乐与阅读设置 | 按剧情切换背景音乐，可分别调整音乐与配音音量、语速 |
| 本地存档 | 手动存档与自动进度保存在当前浏览器，刷新后可以继续阅读 |

## 用户安装教程

目前提供 **Windows 本地运行版**。电脑需要 Windows 10/11、NVIDIA GPU 及驱动、[Node.js 22.13 或更新版本](https://nodejs.org/)、[Python 3.11](https://www.python.org/downloads/) 和约 20 GB 可用磁盘空间。首次安装需要联网下载依赖、语音引擎和五套音色，可能需要较长时间。

1. 前往 [Voice of Terra 最新发布页](https://github.com/luoul-123/arknights-story-dubber/releases/latest)，下载页面底部的 **Source code (zip)**，解压到本地文件夹。五套音色在同一发布页的 voice-of-terra-voices.zip 附件中；安装器会自动下载，无需手动解压。
2. 双击解压后文件夹中的 **安装并启动.bat**。安装器会准备运行环境、下载音色，并在完成后打开浏览器。
3. 以后双击 **启动网页版.bat** 即可使用；结束时双击 **停止网页版.bat**。本机访问地址为 http://127.0.0.1:5173/。

安装仅在自己的电脑上启动网页和语音服务，不需要云服务器。已有本项目五套音色数据的用户可保留 web/.voice-data/characters.json，安装器会跳过音色包下载。

## 架构和目录

浏览器负责剧情展示与播放；网页服务读取剧情并将配音请求交给本机 Python 服务；Python 服务调用 GPT-SoVITS 生成音频并缓存结果。剧情、立绘和音乐按需从文末列出的公开素材源读取。

| 路径 | 内容 |
| --- | --- |
| web/app/ | 剧情剧场界面与网页 API |
| web/lib/ | 剧情解析、分支场景和音频播放器 |
| web/backend/ | 本机语音服务、音色准备与素材处理 |
| web/tests/ | 剧情、音频和浏览器检查 |
| engines/、models/、web/.voice-data/ | 安装后生成的引擎、基础模型、预设音色和缓存；不提交到源码仓库 |

## 来源与许可

原创代码采用 [MIT 许可证](LICENSE)。剧情文本、立绘、CG、音乐及角色录音归鹰角网络及相应权利人所有，不受代码许可证覆盖。

剧情数据来自 [ArknightsGamedata](https://github.com/ArknightsAssets/ArknightsGamedata)；图片及《明日方舟》语音来自 [ArknightsAssets2](https://github.com/ArknightsAssets/ArknightsAssets2)；语音合成使用 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)。终末地素材来自社区 [Warfarin 佩丽卡语音页](https://warfarin.wiki/cn/operators/perlica)和[管理员语音页](https://warfarin.wiki/cn/operators/endministrator)。

本项目并非官方作品，AI 合成台词不是官方剧情配音。
