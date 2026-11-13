# 泰拉之声运行说明

## 本机运行

根目录「启动网页版.bat」启动网站 5173 与语音服务 9881。GPT-SoVITS 推理服务使用 9882，按需启动。停止脚本只关闭记录中进程 ID 与启动时间一致的服务。

手动启动：在 web 目录运行 npm run dev 和 ../.venv/Scripts/python.exe backend/run_local.py。.dev.vars 包含 VOICE_BACKEND_URL、VOICE_BACKEND_TOKEN、STUDIO_ADMIN_USER_ID；密钥只在服务端读取。

## 朗读音色

网站仅提供阿米娅、凯尔希、佩丽卡、男管理员、女管理员五个选项，全部台词和旁白统一使用所选声音。浏览器键 terra-preset-voice 保存音色 ID，旧 ID 失效时回退到阿米娅。没有读者上传入口，网站代理也不开放 reader/upload 与 reader/voice。

音色由管理员通过后端工具准备；素材来源、样本时长和操作见 [default-voices.md](docs/default-voices.md)。五个角色使用网络游戏语音重新训练，旧个人录音、旧角色模型与旧合成缓存已删除。共享基础模型仍是训练和推理所需依赖。

## 播放与排队

同一 HTMLAudioElement 播放全部剧情。音频 ended 驱动随身听推进，打开面板不中断；音量与语速更新现有音频。分支与段落结束等待用户确认。已验证桌面 Edge 后台标签，手机锁屏尚未实机验证。

连续跳句等候 220 ms 稳定后才发送当前台词，实际开始播放后才延迟预取下一句。每个播放器使用独立 streamId 和递增 sequence；后端在获得 GPU 锁后检查是否已过时，旧排队任务不再合成。已经进入 GPU 的推理完成后结果会被前端忽略，不会播放旧句。

浏览器最多缓存 24 条音频。训练与推理共用 GPU 锁；训练时停止本服务启动的推理进程释放显存。服务重启会终止未完成任务，保存的素材与模型保留。模型发布带版本号，重新发布不会命中旧音频缓存。

## 剧情与存档

剧情目录按需读取，提供分类、搜索及国服实装时间线。时间线按章节 / 活动合集折叠，展开后选具体段落。当前目录 491 组 / 2,061 段。见 [目录来源](docs/catalog-sources.md)。

手动存档 terra-manual-save 与自动进度 zhousheng-progress 独立保存，刷新优先手动；启动页不写自动进度。选择其他章节不会覆盖手动存档。

立绘保留表情 / 姿态标识，支持左右中人物槽位。音乐按脚本执行前奏、循环、停止，音乐与配音分别调节。复杂连续动画仍未完整复刻。见 [媒体来源](docs/media-sources.md)。

## 部署

网站与 GPU 后端分开运行。网站设置 VOICE_BACKEND_URL（GPU 服务 HTTPS 地址）、VOICE_BACKEND_TOKEN、STUDIO_ADMIN_USER_ID。GPU 服务设置相同密钥，以及 GPT_SOVITS_ROOT、GPT_SOVITS_PYTHON、WHISPER_MODEL_DIR 和持久化 ZHOU_DATA_DIR。

默认只监听 127.0.0.1。公开部署需真实身份认证与 HTTPS 反向代理，服务密钥不可发给浏览器。Windows 已验证，Linux 尚未实机验证；无预设时的系统声音回退依赖 Windows。迁移语音服务需同时迁移模型、素材及 .voice-data，并修正其中本机绝对路径。

## 验证

~~~powershell
node --test tests/core.test.mjs
../.venv/Scripts/python.exe -m unittest discover -s backend -p "test_*.py"
npx tsc --noEmit
npm run build
node tests/browser-preset-settings.mjs
~~~

其他回归脚本见根 README。work/、.voice-data/、录音、模型、.dev.vars 均不提交 Git。
