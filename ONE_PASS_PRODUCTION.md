# 龙虾日报 One-pass Production

本仓库沿用龙虾头条的播客仓库结构与命名方式：`episodes/` 保存口播 canonical text，`feed.xml` 是播客 RSS，`cover.jpg` 是节目封面，`publish/requests/` 保存发布请求，`scripts/` 与 `.github/workflows/` 负责 preview / publish / replace 流程。

龙虾日报的研究原文与 spoken 页面仍以 `tangkk/daily_brief` 为内容源；本仓库只承担 podcast distribution。新的 episode GUID 采用 `epNNN-daily-YYYY-MM-DD`，R2 prefix 使用 `daily`。
