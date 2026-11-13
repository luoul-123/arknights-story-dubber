# 剧情立绘与音乐

立绘索引来自 ArknightsAssets/ArknightsAssets2 的 cn 分支（774d93398fc56df29b4f55e406edda1a9df451e9），只保存文件名与目录映射，不包含图片。新立绘 #表情$姿态标识完整保留并进行 URL 编码；旧立绘以文件索引定位，例如 char_002_amiya_10 实际位于 char_002_amiya_1 目录。

音乐逻辑名来自 ArknightsAssets/ArknightsGamedata 的 cn/gamedata/story/story_variables.json。公开参考站点泰拉文库使用的历史音频资源版本 2c7efe3c96ff8eb96af777ff7508144b4485654a 仍包含当前 cn 分支已不提供的曲目；音乐优先读取这一固定版本，再尝试 cn。已实际验证 babel_loop 与 EyjafjallaDream_loop。

媒体通过本机网络按需读取，缓存到 .voice-data/media；首次打开未缓存资源仍需联网。GitHub 与 jsDelivr 可回退；未知名称报错，不把用户输入拼成任意外部 URL。索引不会自动更新，新增角色/曲目需要维护索引。

支持按脚本播放前奏和循环、停止、音乐音量变化、分支后恢复音乐状态。设置中音乐音量与配音音量独立保存。已支持表情差分、左右中槽位、明暗焦点与最终位置/缩放/透明度；复杂跳跃、震动等连续动作尚未完整复刻。
