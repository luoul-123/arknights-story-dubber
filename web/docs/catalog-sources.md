# 剧情分类与实装时间来源

时间列表按国服首次实装日期排序，日期以 Asia/Shanghai 显示；同一活动内保留原剧情顺序。复刻日期不参与首次实装排序。数据缺失时标注“日期待补”，不拿档案收录日期冒充首发日期。

当前主站的 `pages/catalog.json` 收录 491 个故事组、2,061 个章节。根目录 README 的“按剧情分类”和“按实装顺序”两份目录由 `scripts/generate-readme-index.mjs` 从这个快照生成；点击故事标题会以 `?group=故事组ID` 在主网页打开该故事的章节目录。新增或修订目录数据后，应重新运行脚本并一同提交 README。

- 主线、SideStory、故事集：story_review_table.json 的 entryType / startTime。
- 个人密录：handbook_info_table.json 的 handbookAvgList.storyGetTime；角色名称来自 character_table.json。
- 主线 10 章以后优先使用 zone_table.json 的 mainlineAdditionInfo.zoneOpenTime；无对应字段时使用该主线的开放时间。
- 早期主线档案中 startShowTime 是剧情回顾功能收录时间，需要使用首发公告补正：
  - 0–4 章：2019-04-30 国服 iOS 首发：https://ak.hypergryph.com/news/201904391.html
  - 5 章：2019-07-09：https://ak.hypergryph.com/news/2019074439
  - 6 章：2019-12-24：https://ak.hypergryph.com/news/2019124194.html
  - 7 章：2020-05-01：https://ak.hypergryph.com/news/2020042016.html
  - 8 章：2020-11-01：https://ak.hypergryph.com/news/2020107970.html
  - 9 章：2021-09-17：https://ak.hypergryph.com/news/2021099183.html

早期主线显示的是公开运营首发日期，不包含此前测试服开放时间。活动中的章节默认归于所属活动首发日期；同活动分周开放的精确关卡日期尚未逐项补全。
