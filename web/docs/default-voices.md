## 音色来源

训练素材为凯尔希的 23 条普通话游戏录音，合计约 275.33 秒，来自 [ArknightsAssets2](https://github.com/ArknightsAssets/ArknightsAssets2) 的 voice 分支。对应台词和来源列在 [素材清单](../backend/curated-voice-sources.json)。凯尔希模型已完成 GPT 与 SoVITS 各 8 轮训练；推理使用约 4.5 秒的参考音频。

模型只保留在维护者本地，另有 [Releases](https://github.com/luoul-123/voice-of-terra-for-arknights/releases/latest) 中的 `voice-of-terra-kaltsit.zip` 作为备份。

## 本地制作与发布

`../scripts/generate-pages-audio.py` 使用已发布的凯尔希模型合成台词，转为单声道 24 kHz、64 kb/s MP3，并跳过已有文件。`../scripts/publish-audio-sections.py` 按完整章节提交音频分站，确认公开地址可访问后再更新主站音频清单。具体前置条件和检查命令见 [运行与发布](../IMPLEMENTATION.md)。
