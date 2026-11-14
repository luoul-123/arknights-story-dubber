# 凯尔希音色与有声章节

当前公开网页只使用凯尔希音色。读者不用下载模型；有声台词已在维护者电脑上合成为 MP3，网页从 [音频分站](https://github.com/luoul-123/vot-audio-20261101)读取。未配音的章节仍可阅读，不会在读者电脑或服务器上临时合成。

## 音色来源

训练素材为凯尔希的 23 条普通话游戏录音，合计约 275.33 秒，来自 [ArknightsAssets2](https://github.com/ArknightsAssets/ArknightsAssets2) 的 voice 分支。对应台词和来源列在 [素材清单](../backend/curated-voice-sources.json)。凯尔希模型已完成 GPT 与 SoVITS 各 8 轮训练；推理使用约 4.5 秒的参考音频。声音相似度、情绪和自然度仍需人工逐段检查。

模型只保留在维护者本地，另有 [Releases](https://github.com/luoul-123/voice-of-terra-for-arknights/releases/latest) 中的 `voice-of-terra-kaltsit.zip` 作为备份。其他四种旧音色已经从本地角色库和公开备份包移除。原始游戏语音与模型不纳入 MIT 代码许可。

## 本地制作与发布

`../scripts/generate-pages-audio.py` 使用已发布的凯尔希模型合成台词，转为单声道 24 kHz、64 kb/s MP3，并跳过已有文件。`../scripts/publish-audio-sections.py` 按完整章节提交音频分站，确认公开地址可访问后再更新主站音频清单。具体前置条件和检查命令见 [运行与发布](../IMPLEMENTATION.md)。

若模型需要重新建立，`../backend/prepare_curated_voices.py` 和 `../backend/curated-voice-sources.json` 现只包含凯尔希；训练不是日常发布步骤。历史五音色实验与当时的实测保留在 [历史验证记录](../VALIDATION.md)，不代表当前网页提供五种音色。
