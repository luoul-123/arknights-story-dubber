# 泰拉之声 · 网页剧情剧场

用户入口是浏览器。网站直接解析剧情脚本，以背景、人物立绘、CG、对话框和选项呈现，不依赖 OCR 或桌面界面。

## 本机验证
已有本机环境可直接双击根目录的“启动网页版.bat”；“停止网页版.bat”只关闭启动器记录且启动时间一致的进程树。首次安装可按下面步骤配置。

1. 网站目录运行 npm run dev。
2. 使用项目已有 Python 运行 backend/run_local.py。首次启动前，.dev.vars 需包含 VOICE_BACKEND_URL、VOICE_BACKEND_TOKEN、STUDIO_ADMIN_USER_ID。
3. 浏览器访问 http://localhost:5173/signin-with-chatgpt?return_to=/，本地开发会登录为 local_seedy。
4. 音色工作室输入干员名，按需导入一段游戏普通话语音及匹配台词，直接免训练试听并发布。也可手动上传 3–10 秒参考语音并校对文本。训练是可选的进阶功能。发布后角色名自动匹配剧情说话人。

网站：npm run dev
GPU 服务：..\.venv\Scripts\python.exe backend/run_local.py

## 读者统一朗读声

录音室默认展示读者功能：上传 3–10 秒、最多 10 MB 的参考录音，自动转写后校对原话，确认即将全部台词和旁白改用该声音。可随时切回默认角色配音。参考音色使用共享基础模型，无需训练。未确认的新上传不会改变当前声音。

网站代理从已验证登录身份写入 X-Reader-Id，后端按用户哈希隔离录音与配置；不接受浏览器自行指定其他用户。私人音色不出现在公共角色列表。管理员角色库和少量可选训练收在折叠区。

## 语音服务
Python 标准库 HTTP 服务 + GPT-SoVITS v2。引擎安装脚本位于 backend/setup_engine.py，配置只读取环境变量和项目内默认路径，不依赖桌面端配置。录音使用 ffmpeg 转为 32 kHz 单声道并按静音附近切分；faster-whisper 负责转写。训练调用真实 GPT/SoVITS 脚本，不模拟训练。模型发布使用快照和版本号；修改训练样本不会改变已发布音色。

任务在独立线程中排队。训练与推理共用 GPU 锁，训练前停止本服务启动的推理进程释放显存。服务重启会终止未完成任务，需重新启动任务；已保存样本和已发布模型保留。取消前端请求并不保证中断已进入 GPU 的推理，但返回的旧结果不会播放。

配音优先匹配已发布角色及别名；无匹配角色自动使用通用音色，空说话人和“旁白”自动使用旁白音色。管理员可在工作室为女声、男声与旁白指定已发布音色，配置保存在 .voice-data/default-voices.json；重新发布模型或更改默认映射会改变缓存版本。默认角色声音优先读取干员档案性别，再识别明确男女称谓，未知性别使用默认女声。未设置默认模型时，Windows 后端使用系统中文语音生成并缓存 WAV。读者无需开关旁白或配置 NPC；未知称谓（例如“？？？”）不会猜测真实身份。系统声音数量取决于服务端已安装的中文语音，不代表每个角色都有独立音色。

随身听通过同一个 HTMLAudioElement 的结束事件推进，不依赖打字动画或后台计时器。支持暂停、继续、上一句、立即跳句；遇到剧情选项暂停等待用户选择，段落结束后等待确认进入下一段。打开目录、设置、回顾、工作室不会打断随身听；面板内提供暂停 / 继续 / 跳句及下一段确认。音量和语速直接更新当前音频，不重新合成或重播。接入 Media Session 元数据及播放控制。桌面 Edge 后台标签页已验证；手机锁屏和系统媒体控件尚未实机验证，浏览器或系统关闭网页后不能继续播放。

## 之后部署到服务器
网站与 GPU 服务分开部署。网站服务端设置：
- VOICE_BACKEND_URL：GPU 服务 HTTPS 地址
- VOICE_BACKEND_TOKEN：至少 24 字符随机密钥，与 GPU 服务一致
- STUDIO_ADMIN_USER_ID：管理员的站点登录 ID（工作室可显示该 ID）

GPU 服务器设置：
- GPT_SOVITS_ROOT：引擎目录
- GPT_SOVITS_PYTHON：安装引擎依赖的 Python
- WHISPER_MODEL_DIR：faster-whisper-small 模型目录
- ZHOU_DATA_DIR：持久化样本、任务模型与音频目录
- VOICE_BACKEND_TOKEN：上述密钥

GPU 服务默认仅监听 127.0.0.1:9881，推理进程使用 9882；使用 HTTPS 反向代理后供网站调用。密钥只放在服务端配置中，浏览器不接触 GPU 服务密钥。Windows 和 Linux 路径分别配置；Linux 尚未实机验证。未配置默认模型时，通用角色与旁白服务依赖 Windows 系统语音；配置并发布默认模型后走 GPT-SoVITS，迁移时也需迁移 .voice-data/ 和模型文件；普通读者的操作不变。当前启动器仅监听本机，尚未开放手机或公网访问。

## 当前演出范围
已实现背景、独立人物层、双人焦点、CG、文本、选项分支、回顾、逐字显示、自动播放、浏览器本地进度与手动存档入口、音频停止、下一句预取、自动 NPC/旁白配音与随身听。剧情目录按上游目录加载，提供主线、SideStory、故事集、个人密录等分类；支持国服实装时间线、年份筛选与升降序。个人密录显示所属干员。详见 [日期来源](docs/catalog-sources.md)。

这是网页视觉小说实现，不承诺逐帧复刻原游戏：音乐逻辑资源映射、复杂动画/镜头轨迹、特殊脚本指令和完整表情叠层尚未实现；未知指令由解析器记录。剧情目录和章节由本机后端通过系统网络设置读取，主来源不可用时使用备用来源；有效数据缓存至 .voice-data/stories，已缓存内容直接返回，过期内容后台刷新，网络失败不会覆盖缓存。未缓存章节仍需联网；图片资源仍按需联网读取。人物图片提供目录/单文件回退。

## 来源
原创网站与后端适配代码沿用本项目 MIT 许可。剧情、立绘、CG、背景属于鹰角网络及相应权利人，不纳入原创代码许可。网页运行时访问 ArknightsAssets/ArknightsGamedata 与 ArknightsAssets/ArknightsAssets2。

## 验证
node --test tests/core.test.mjs
..\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py"
npx tsc --noEmit
npm run build
node tests/browser-smoke.mjs（本机服务启动后，使用隐藏 Edge，测试声音静音）
node tests/browser-navigation.mjs（面板播放、分类时间线及下一段确认）
node tests/browser-reader-voice.mjs（真实上传识别、全篇覆盖与恢复默认，需本机佩丽卡参考素材）

work/ 中的研究样本、截图、.voice-data/、.dev.vars、录音和模型均不提交。

## 免训练优先
默认使用 GPT-SoVITS 预训练基础权重 + 干员参考语音与对应台词，不为每个角色单独训练。自动导入使用 charword_table.json 的 voiceAsset / voiceText 匹配 ArknightsAssets2 voice 分支的普通话文件，只下载候选短音频；已有干员样本、训练模型不会被覆盖。无对应干员语音的 NPC 自动使用通用声音；管理员以后可以统一覆盖其音色。此方式仍需要推理算力，效果不等同于官方配音或经过优化的角色模型。

## 站点默认模型

专属干员仍优先使用参考音色；全站通用女声、男声、旁白当前也使用共享基础模型 + 参考录音。已有训练模型保留为管理员可选项，不参与当前默认播放。当前本机素材及训练记录见 [default-voices.md](docs/default-voices.md)，不会随源码分发。

纯标点台词保留显示并播放半秒停顿；英文前处理数据可通过 ../.venv/Scripts/python.exe backend/setup_text_resources.py 补齐。时间线按章节 / 活动合集展示，展开后选择具体段落。
