# 共享服务只读检查

2026-09-12，从本次检查网络观察到：现有共享 API 在应用处理前被 Cloudflare 返回 403，并非仅本地 Origin 的 CORS 限制。本次未修改服务、访问控制或留言数据。

| 公开地址 | 请求 | 结果 |
|---|---|---|
| https://frankfanyiming.github.io/frank_worlds/community-config.json | GET | 200，JSON；apiOrigin 指向下列 Sites 域名 |
| https://nobita-summer-neighborhood.frankfanyiming.chatgpt.site/api/community/meta | GET | 403 |
| https://nobita-summer-neighborhood.frankfanyiming.chatgpt.site/api/community/notes | GET、OPTIONS | 403 |
| https://nobita-summer-neighborhood.frankfanyiming.chatgpt.site/api/community/branches | GET | 403 |
| https://nobita-summer-neighborhood.frankfanyiming.chatgpt.site/ | GET | 403 |

`meta`、`notes` 的 GET 分别使用无 Origin、GitHub 线上 Origin、本地 Origin，均返回相同类型的 403；OPTIONS 的线上与本地 Origin 也均失败。响应为 `text/html; charset=UTF-8`，Server 为 Cloudflare，页面标题为其访问拦截提示；没有应用 JSON 或 Access-Control-Allow-Origin。未保存响应 HTML、IP、Cookie 或其他隐私数据。

仓库 `worlds/doraemon/web/lib/community/server.ts` 已允许 GitHub 线上域及 localhost/127.0.0.1 来源；应用拒绝来源时返回 JSON 403，缺少数据库绑定时返回 JSON 503。上述 HTML 403 因此指向应用之前的平台或边缘访问限制，不能通过重复修改前端 CORS 解决。具体平台规则及其他网络是否同样受阻，本次没有验证。

本地带项目路径的配置与线上配置指向同一共享 API。来访本与共创分支依赖该接口；3D 世界的静态模型、Godot 运行包与加载器通过独立静态资源地址加载，不依赖共享接口成功。这项现有服务故障与本次 Godot 资产导出无关，也不代表三个世界的静态加载失败。

后续排查入口是仓库 `worlds/doraemon/web/.openai/hosting.json` 登记的 Sites 项目及其边缘访问规则。本次只记录证据，没有改变平台权限、部署或迁移数据。
