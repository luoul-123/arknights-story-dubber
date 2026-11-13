# 五个预设朗读音色

读者在「朗读音色设置」选择阿米娅、凯尔希、佩丽卡、男管理员或女管理员，所选声音用于所有角色台词和旁白。首次默认阿米娅，不再提供读者录音上传。

## 网络素材（2026-11-13）

本次从网络游戏语音重新建立五个角色资料，不使用此前个人训练的声音。旧角色录音、旧训练权重、旧合成缓存和旧读者上传已删除，共享预训练基础模型保留。

| 角色 | 有效完整录音 | 训练素材时长 | 推理参考长度 |
| --- | ---: | ---: | ---: |
| 阿米娅 | 22 条 | 208.52 秒 | 6.09 秒 |
| 凯尔希 | 23 条 | 275.33 秒 | 4.50 秒 |
| 佩丽卡 | 26 条 | 182.50 秒 | 6.37 秒 |
| 男管理员 | 17 条 | 40.84 秒 | 5.20 秒 |
| 女管理员 | 16 条 | 39.34 秒 | 5.20 秒 |

阿米娅、凯尔希取自 [ArknightsAssets2](https://github.com/ArknightsAssets/ArknightsAssets2) voice 分支的普通话游戏录音，台词匹配游戏 charword_table。阿米娅去除皮肤重复素材，只保留原角色路径。

终末地素材来自 [Warfarin 佩丽卡](https://warfarin.wiki/cn/operators/perlica) 与 [Warfarin 管理员](https://warfarin.wiki/cn/operators/endministrator)：佩丽卡 chr_0004_pelica、男管理员 chr_0002_endminm、女管理员 chr_0003_endminf。素材是原始游戏语音，不是此前合成结果。管理员的 5.2 秒参考取自完整录音第一句，标为 referenceOnly，不重复计入训练。

逐条 URL、对应文字和参考标记见 [素材清单](../backend/curated-voice-sources.json)。原始语音与权重不进入 Git。素材归相应权利人，独立于代码许可。

## 管理员准备流程

在 web 目录执行。下载使用系统代理；本机既有五个新音色无需重复执行。

~~~powershell
../.venv/Scripts/python.exe backend/prepare_curated_voices.py prepare
~~~

生成 work/curated-network/manifest.json。导入是离线管理操作，先停止语音后端，避免与正在运行的训练、发布同时修改角色库；网站无需为此提供上传界面。

~~~powershell
../.venv/Scripts/python.exe backend/import_voice_dataset.py work/curated-network/manifest.json
~~~

重新启动语音服务后训练并发布：

~~~powershell
../.venv/Scripts/python.exe backend/prepare_curated_voices.py train --epochs 8
../.venv/Scripts/python.exe backend/prepare_curated_voices.py publish
~~~

训练调用真实 GPT-SoVITS v2，GPT 和 SoVITS 各 8 轮；不会模拟完成。train 对已有模型跳过，不重复训练。publish 要求五个角色都有模型，通过管理员 API 发布训练权重，并配置兼容回退的女声 / 旁白为佩丽卡、男声为男管理员；网页已选音色优先覆盖全部文本。

参考文本使用游戏原文，ASR 只辅助检查，不用同音错误覆盖专名。训练素材数量有限，尤其两个管理员只有约 40 秒；训练完成和成功合成不等于自然度、情绪与相似度经过人工验收。实测记录见 [验证记录](../VALIDATION.md)。

## 体积与响应

只维护五个预设模型，不按剧情角色增加模型数量。后端一次加载当前权重，浏览器不下载模型。一个角色的最终 GPT + SoVITS 权重约 229 MiB，训练中间文件另计。

浏览器音频缓存最多 24 条。连续跳句合并请求并淘汰后端过时任务，实际开始播放后才预取下一句。已进入 GPU 的一次合成不能立即中断；首次启动、音色切换和未缓存长句仍有等待。

本轮五个音色已全部完成各 8 轮训练并发布为 trained。清理优化器状态和中间特征后，五组最终权重共 1145.95 MiB，浏览器无需下载。
