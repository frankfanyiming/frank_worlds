# XLands小世界

[打开小世界](https://frankfanyiming.github.io/frank_worlds/)

[制作手记 · 飞书](https://xgenlabs.feishu.cn/docx/EHsmd08qGo3T7nxWKIMchlcGnvb) · [网页阅读](https://frankfanyiming.github.io/frank_worlds/resources/making-of.html) · [5 个制作 Skills](skills/README.md)

三个可探索的 3D 世界：

- **机器猫在等你回家** — 原哆啦A梦小镇，保留室内、神奇道具、四季和昼夜。
- **探索旅行蛙的小世界** — 青蛙与熊猫、两户住宅、串门、做饭、送礼、同行野餐与共同照片；进度保存在当前浏览器。
- **欢迎光临侦探事务所** — 最新 Blender 普通车流版本的米花町。

首页提供简体中文、繁體中文、日本語、한국어、English。留言板已下线，交流反馈请到作者的 X 账号。个人分支可改造、发布、复制，并提交主世界合并提案。

共创共享服务目前部分请求仍收到上游 403。首页、世界和本地朋友玩法不依赖该接口；问题可在 [X @FrankFYM001](https://x.com/FrankFYM001) 交流。抖音号：`frank001`；[小红书号：150015050](https://www.xiaohongshu.com/user/profile/55d96ee558944639c3ce03f1)。

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

纯热爱分享，不涉及任何商业组织，不涉及盈利。相关 IP 未取得授权，权利归各自权利人所有。希望大家基于热爱交流和使用；本声明不构成 IP 使用授权。

旅行蛙与柯南的完整源模型压缩包已整理，公开上传待确认；当前 Git 包含可读源码和清单，网页运行包单独发布在 gh-pages。确认公开后会更新清单并开放自动下载。

## 手机提示与代码出处

手机控制卡顿时建议用电脑打开，通常会更流畅。首页和三个世界的手机入口均有提示，游戏上方提示可在当前页签收起；这不代表手机性能问题已经解决。

本仓库已加入源码署名与构建来源标识：`xlands-frankfym001`。查看 [SOURCE.json](SOURCE.json)、[NOTICE](NOTICE) 和 [来源追溯说明](PROVENANCE.md)。发布包的 JS 保留作者、原始仓库和构建提交，`provenance.json` 可核对文件散列；无访客追踪，删除标识后的副本无法保证追溯。

```sh
python3 tools/stamp-source-provenance.py --check
node tools/verify-build-provenance.mjs worlds/doraemon/web/dist-pages
```

访问统计维护与指标说明见 [docs/analytics.md](docs/analytics.md)。Fork 后请替换为自己的 Umami 网站配置或关闭统计。
