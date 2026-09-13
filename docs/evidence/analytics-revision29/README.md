# 第 29 版：Umami 访问统计

用户在自己的 Umami Cloud 账号注册并登录，随后通过后台添加 XLands 小世界，站点 ID 为 `6adb4308-a6f6-484a-9bf2-efaffb380a25`。未创建公开分享链接。

首页和三个 Hash 世界规范化为四个页面；实际开始、引擎 ready、加载失败和运行故障分别记录。父子 iframe 排重、有限内存队列、超时放弃、来源/query 隐私过滤、DNT/GPC/排除本人访问已实现。统计默认只在正式 GitHub Pages 域名发送。

已通过类型检查、统计逻辑测试、移动输入与加载恢复检查、首页静态恢复检查。未进行新的 3D 浏览器视觉或物理手机性能测试；Umami 管理后台的创建与配置属于外部服务配置操作。

## 发布验证

- 源码提交：`2aad24e5ea7ab0b2cad7b56a1b90fa3f6f1dbf47`，已推送 main 与功能分支。
- Pages 提交：`29be3ee5d29d41aaa6bccce0f5a5f0ccffdbb9f3`；部署 34779947497 已成功。
- Sites 构建、Pages 构建通过；两份构建来源清单分别校验 24、15 个文件。发布目录另为独立采集脚本追加相同来源/提交注释，连同原生壳和配置合计核对 25 个文件。
- 33 个公开文件 HTTP 200，字节和 SHA-256 一致；四份 PC/手机世界包清单保持一致。未改世界模型、角色、手势或音乐。
- 首页核心文件由 899,567 B 到 906,077 B；这里不包括第三方 Umami 脚本，不是网络耗时或手机帧率实测。
- 独立脚本与配置直接从 dist-pages 拷贝；仅为 analytics.js 在发布时追加透明构建 banner，实际逻辑保持源码一致。保留旧哈希文件供未刷新的页面加载。
- 一次明确标记 integration_check 的命令行验证收到 HTTP 200，但仅返回 beep，没有 session/cache，不能据此宣称后台收数成功。该探测结果保存在 collector-check.json；随后通过打开已发布首页进行正常浏览器访问，由 Umami 后台实际数据确认。


## 后台实际收数

在正常浏览器中打开已发布的 `?v=29&utm_source=installation-check#` 首页后，Umami 管理界面显示 Visitors 1、Visits 1、Views 1，Pages 中出现 `/frank_worlds/`，确认真实浏览器采集通路连通。此前命令行事件没有记入该浏览量。未检查游戏 DOM、截图或模拟三世界成功游玩；三世界加载事件由代码测试覆盖，后续真实访问将陆续出现。此验证访问可通过 source 属性 installation-check 识别，不能当成推广新增用户。
