# 小世界 · XLands

[打开小世界](https://frankfanyiming.github.io/frank_worlds/)

三个可探索的 3D 世界：

- **机器猫在等你回家** — 原哆啦A梦小镇，保留室内、神奇道具、四季和昼夜。
- **探索旅行蛙的小世界** — Tripo 青蛙与熊猫，Blender 自然场景、原作装修的蛙家和熊猫竹木茶室；可走动、跳跃、串门喝茶，带森林背景声音。
- **欢迎光临侦探事务所** — 最新 Blender 普通车流版本的米花町。

首页提供简体中文、繁體中文、日本語、한국어、English。来访本支持文字留言和非公开联系邮箱。个人分支可改造、发布、复制，并提交主世界合并提案。

## 共创

个人草稿 → 公开作品 → 合并提案 → 维护者审核 → 主世界拓展区。

分支使用稳定的物件 ID、基准版本与不可变公开快照。独立字段自动合并；同时修改同一字段、删除与修改冲突、空间重叠需要处理。主世界提交使用版本条件更新，避免并发覆盖，并支持保留历史的回退。

[产品与合并规则](docs/co-creation.md) · [运行与部署](docs/deployment.md)

[旅行蛙空间与伙伴概念](docs/design/frog-spatial-study/README.md) · [3D 世界制作方法与复盘](docs/3d-world-method.md)

## 项目

- `worlds/doraemon/web`：网页首页、哆啦A梦运行时、共创编辑器和服务端接口。
- `worlds/frog/source`：旅行蛙 Godot 项目。
- `worlds/conan/source`：柯南原桌面项目。
- `worlds/conan/web-project`：柯南网页项目。

大型模型归档通过各世界 `asset-manifest.json` 记录版本与校验和。当前完整原始资产仍为 `pending-publication`；网页运行包已单独发布，干净克隆暂不能直接下载完整原始模型。以下获取命令适用于清单中的归档正式发布后。

```bash
python3 tools/fetch-native-assets.py frog
python3 tools/fetch-native-assets.py conan
python3 tools/fetch-native-assets.py conan-web
cd worlds/doraemon/web
npm ci
npm run typecheck
npm test
npm run test:community
npm run build:pages
```

用户自己的 OpenAI API Key 只留在页面内存，请求直接发往 OpenAI。平台 Agent 默认 GPT‑6 Astra，支付及服务密钥配置齐备后启用；未配置时禁止调用与扣款。

代码授权与模型来源见 [LICENSE](LICENSE)、[CREDITS](CREDITS.md)。

旅行蛙与柯南的完整源模型压缩包已整理，公开上传待确认；当前 Git 包含可读源码和清单，网页运行包单独发布在 gh-pages。确认公开后会更新清单并开放自动下载。
