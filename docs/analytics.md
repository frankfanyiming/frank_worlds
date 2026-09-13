# XLands 访问统计

2026-09-14：使用用户本人注册的 Umami Cloud 账号。后台只向登录的账号开放，没有启用公开分享链接。

- [统计总览](https://cloud.umami.is/analytics/us/websites/6adb4308-a6f6-484a-9bf2-efaffb380a25)
- [世界加载事件](https://cloud.umami.is/analytics/us/websites/6adb4308-a6f6-484a-9bf2-efaffb380a25/events)
- 统计站点：`frankfanyiming.github.io`；页面路径限定为本项目首页和三个世界。
- 网站 ID 和脚本地址是公开配置，不是 API 密钥。账号、密码、会话凭据均不写入仓库。

## 怎么看

在后台调整时间范围：总览看浏览次数、独立访客和设备；Pages 看 `/frank_worlds/`、`/frank_worlds/world/doraemon`、`/frank_worlds/world/frog`、`/frank_worlds/world/conan`；Events 看下列事件及其 `world` 属性。

| 事件 | 含义 |
| --- | --- |
| `world_enter` | 开始一次引擎加载，包含明确重试和更换语言后的重新加载 |
| `world_ready` | 引擎报告可进入世界，`load_ms` 为本次加载耗时 |
| `world_load_error` | 本次加载失败，`reason` 为有限分类，不上传错误原文 |
| `world_runtime_error` | 成功加载后发生运行故障，例如图形上下文丢失 |

`world_ready / world_enter` 可用于观察加载成功比例；时间范围边界、拦截器、离开前未完成和丢失请求都会造成偏差，不是严格的服务 SLA。进入次数是尝试次数，不等于人数。手机分类使用浏览器移动标记或粗指针信号，是设备类型近似值。内置设备报告还可参考浏览器解析结果。

分享时可加 `?utm_source=x#`、`?utm_source=xiaohongshu#`、`?utm_source=douyin#`；事件/页面属性的 `source` 保留这个有限渠道标签。普通来源只传来源站点，不上传来源页路径和查询串。社交 App 未提供 referrer 时，没有渠道参数就无法准确区分来源。

## 接入与边界

`worlds/doraemon/web/public/analytics.js` 独立于 React 和 3D 引擎，异步读取同目录 `analytics-config.json` 后加载 Umami 官方脚本。自动页面/点击跟踪关闭，由 XLands 明确发送规范化页面和四种加载事件。不加载会话录像、热力图或逐帧采样，不新增访客 ID 或调用 identify。

Hash 世界路由使用虚拟页面路径，版本号 `v`、任意 query/hash、共创分支 ID、邮箱、存档、错误原文不进入事件。Godot 嵌入首页时仅父页面发送；独立打开原生世界时由加载壳发送，避免同一访问计数两次。Doraemon 在真实快照 ready/error 信号上发送，不能以下载结束代替引擎成功。

尊重 DNT、GPC 与 `localStorage['umami.disabled']='1'`。关闭：将公开配置 `enabled` 设为 false。开发/预览域名不在 domains 中，默认不发送。统计请求失败不重试、不阻塞游戏；配置 4 秒、脚本 10 秒超时后放弃本页统计，队列最多 60 条，可能少计，不能为了统计拖慢游戏。

更换自己的部署时，创建自己的 Umami 网站，替换 websiteId、scriptUrl、domains；不要沿用 Frank 的统计 ID。此前未采集的数据不能补回，统计后台的数据起点是本次实际启用后。

## 验证

`npm run test:analytics` 使用实际采集脚本和加载事件模块验证 Hash 切换、排重、离线/超时、隐私字段过滤、嵌入与独立模式、异步过期回调。构建与公开文件检查另见本次发布记录。离线模拟验证不能代替后台实际收到事件；发布后分别记录公开文件上线与后台收数状态。

## 官方参考

- https://docs.umami.is/docs/tracker-functions
- https://docs.umami.is/docs/tracker-configuration
- https://docs.umami.is/docs/collect-data
