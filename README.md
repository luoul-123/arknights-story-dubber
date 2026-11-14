# Voice of Terra · 泰拉之声 | 明日方舟有声视觉小说

## 功能

Voice of Terra 泰拉之声是在浏览器中阅读和收听《明日方舟》剧情的非官方同人项目。[点击此处打开网址](https://luoul-123.github.io/voice-of-terra-for-arknights/)即可阅读全部收录剧情。

目前正持续更新收录剧情的有声模式，还未上线有声模式的剧情仅可阅读、看立绘与 CG、听背景音乐。

| 功能               | 说明                                                                     |
| ------------------ | ------------------------------------------------------------------------ |
| 剧情剧场           | 阅读台词、选择分支，查看背景、角色立绘与 CG                              |
| 凯尔希声线剧情朗读 | 已上线的章节可逐句播放，也能开启随身听连续收听                           |
| 悬浮桌宠           | 支持的桌面浏览器可在随身听时打开游戏原版凯尔希小人，暂停、调速或返回网页 |
| 剧情目录           | 按剧情类型、实装时间浏览，支持搜索与跨故事跳转                           |
| 阅读设置           | 深色或浅色主题、逐字显示、配音与音乐音量、播放速度                       |
| 存档               | 进度保存在当前浏览器，网页更新后仍可继续阅读                             |

## 使用教程

在线阅读**无需安装**，直接打开 [Voice of Terra 网页](https://luoul-123.github.io/voice-of-terra-for-arknights/)。点右上角的目录选择故事；带“有声”标记的故事可选择已上线章节收听，其他章节可以阅读。在支持文档画中画的桌面浏览器中，开启随身听会打开凯尔希悬浮小窗；点击“回到网页”后小窗会继续陪着你，关闭原网页时小窗也会关闭。存档只保存在当前浏览器；换设备或清除网站数据后不会自动同步。

开发者可以从 [GitHub 下载源码 ZIP](https://github.com/luoul-123/voice-of-terra-for-arknights/archive/refs/heads/main.zip)。源码内保留语音模型和生成工具用于制作新音频。

## 更新日志

2026-11-14 sidestory《时间啊，向前！》的有声音频已上传。

## 架构和目录

主网页由 GitHub Pages 托管，浏览器读取剧情文本、立绘、CG 与音乐。凯尔希音频在本地提前生成 MP3，发布到独立的音频Pages分站；主网页依据音频索引读取对应分站。后续故事可以使用新的音频分站，每个分站须遵守 GitHub Pages 的 [1 GB 站点上限](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)。

| 路径                                      | 内容                                                 |
| ----------------------------------------- | ---------------------------------------------------- |
| `web/pages/`                              | 主网页、剧情目录、音频清单与分站映射                 |
| `web/lib/`                                | 剧情解析、分支场景与播放逻辑                         |
| `web/scripts/`                            | 静态站点检查、目录生成与音频生成脚本                 |
| `web/backend/`                            | 仅供本地制作配音的语音服务                           |
| `engines/`、`models/`、`web/.voice-data/` | 本地语音引擎、凯尔希模型与生成缓存；不提交到源码仓库 |

## 来源与许可

原创代码采用 [MIT 许可证](LICENSE)。剧情文本、立绘、CG、音乐和角色录音归鹰角网络及相应权利人所有，不受代码许可证覆盖。

剧情数据来自 [ArknightsGamedata](https://github.com/ArknightsAssets/ArknightsGamedata)；立绘与演出素材来自 [ArknightsAssets2](https://github.com/ArknightsAssets/ArknightsAssets2)；桌宠动画由[游戏原版凯尔希战斗小人素材](https://github.com/fexli/ArknightsResource/tree/main/spine/char_003_kalts/char_003_kalts/Front)导出；凯尔希配音使用 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 在本地生成。

注：泰拉之声是个人为爱发电制作的非官方作品。AI 合成的台词仅供同人体验，并非官方剧情配音。个人精力有限，更新缓慢还请理解，欢迎各位博士反馈与交流~
