# Voice of Terra · 泰拉之声

## 功能

Voice of Terra 是在浏览器中阅读和收听《明日方舟》剧情的非官方同人项目。
由于经费有限，[在线体验版](https://luoul-123.github.io/voice-of-terra-for-arknights/)目前逐段开放 SideStory **《时间啊，向前！》** 的有声阅读（牢猫配音版）。已上线的段落会标出“凯尔希有声”；其他收录剧情也都能阅读。
感兴趣的博士可以安装本地完整版运行网页和语音服务，目前版本支持所有收录剧情5名角色声线朗读设置。

| 功能       | 在线体验版                                                      | 本地完整版                                                             |
| ---------- | --------------------------------------------------------------- | ---------------------------------------------------------------------- |
| 剧情剧场   | 阅读剧情，查看背景、角色立绘、表情与 CG，选择对话分支           | 同左                                                                   |
| 配音       | 《时间啊，向前！》逐段开放凯尔希配音；其他章节仅可阅读         | 目前有阿米娅、凯尔希、佩丽卡、男女管理员五种音色可选，按需生成台词配音 |
| 剧情档案   | 按主线、SideStory、故事集和个人密录浏览，支持搜索与时间线       | 同左                                                                   |
| 随身听     | 有声样例支持后台连续播放                                        | 同左                                                                   |
| 演出与阅读 | 跟随剧情播放背景音乐；可调逐字显示、音量、语速，回顾对话        | 同左                                                                   |
| 存档       | 进度保存在当前浏览器，刷新后接着读                              | 同左                                                                   |

## 用户安装教程

本地完整版支持 **Windows 10/11**，需要 NVIDIA GPU 及驱动、[Node.js 22.13 或更新版本](https://nodejs.org/)、[Python 3.11](https://www.python.org/downloads/) 和约 20 GB 可用磁盘空间。首次安装会联网下载依赖、语音引擎和五套音色，请给它一点时间。

1. [下载项目源码 ZIP](https://github.com/luoul-123/voice-of-terra-for-arknights/archive/refs/heads/main.zip)，解压到本地文件夹。五套音色放在 [GitHub Releases](https://github.com/luoul-123/voice-of-terra-for-arknights/releases/latest) 的 `voice-of-terra-voices.zip` 附件中，安装器会自动下载，不用手动解压。
2. 双击文件夹里的 **安装并启动.bat**。等环境和音色准备好后，浏览器会自动打开网站。
3. 如何启动：双击 **启动网页版.bat**；读完后双击 **停止网页版.bat**。本机地址是 `http://127.0.0.1:5173/`。

## 架构和目录

在线体验版由 GitHub Pages 托管静态网页。浏览器直接读取公开剧情和演出素材，凯尔希样例配音是提前生成的 MP3，因此打开网页时不需要 GPU 服务器。本地完整版则由网页服务与本机 Python 服务协作，调用 GPT-SoVITS 按需合成并缓存配音。

| 路径                                      | 内容                                                     |
| ----------------------------------------- | -------------------------------------------------------- |
| `web/pages/`                              | 在线体验版界面、静态剧情目录与样例音频                   |
| `web/app/`                                | 本地完整版界面与网页 API                                 |
| `web/lib/`                                | 两个版本共用的剧情解析、分支场景与音频播放逻辑           |
| `web/backend/`                            | 本机语音服务、音色准备和素材索引                         |
| `web/tests/`                              | 剧情、音频与浏览器检查                                   |
| `engines/`、`models/`、`web/.voice-data/` | 安装后生成的引擎、基础模型、音色与缓存；不提交到源码仓库 |

## 来源与许可

原创代码采用 [MIT 许可证](LICENSE)。剧情文本、立绘、CG、音乐和角色录音归鹰角网络及相应权利人所有，不受代码许可证覆盖。

剧情数据来自 [ArknightsGamedata](https://github.com/ArknightsAssets/ArknightsGamedata)；图片与《明日方舟》语音来自 [ArknightsAssets2](https://github.com/ArknightsAssets/ArknightsAssets2)；语音合成使用 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)。终末地相关素材来自社区 [Warfarin 佩丽卡语音页](https://warfarin.wiki/cn/operators/perlica)和[管理员语音页](https://warfarin.wiki/cn/operators/endministrator)。

注：泰拉之声是个人为爱发电制作的非官方作品。AI 合成的台词仅供同人体验，并非官方剧情配音。个人精力有限，开发进度缓慢还请理解，欢迎各位博士反馈与交流~
