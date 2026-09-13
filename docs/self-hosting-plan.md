# 首页、留言本与服务器部署

更新：2026-09-13。首页轻量化与 X 账号入口已实现；下述 Ubuntu 迁移是部署方案，尚未连接截图中的服务器、修改 DNS 或迁移线上数据。

## 当前留言存在哪里

公开前端在 GitHub Pages，API 地址来自 `worlds/doraemon/web/public/community-config.json`：

`https://nobita-summer-neighborhood.frankfanyiming.chatgpt.site/api/community/`

此次使用 Sites 的数据库只读概览核实了线上 `DB` 绑定，实际存在 `notes`、`contacts`、`visitors` 等 11 张业务表。该数据库由 Sites 管理，底层为 Cloudflare D1；并非截图中的阿里云服务器数据库。没有为回答此问题读取留言正文或联系邮箱。

- `notes`：昵称、留言、所属世界、提交时间、留言所有者 ID。
- `contacts`：用户选择填写并同意保存的联系邮箱，与公开留言分表。公开留言接口不返回邮箱。
- `visitors`：匿名访客令牌的散列与限流信息。浏览器保存原始访客令牌，用于识别自己的留言。
- 旅行蛙进度、相册等属于浏览器本地存档，不能与上述共享留言数据库混为一谈。

公开 GitHub 仓库保存程序和数据库结构，不包含线上留言数据库。管理数据库可使用该 Sites 项目的设置/数据库查看器；当前配置中逻辑绑定为 `DB`。

## 与截图中的服务器怎么衔接

截图显示阿里云新加坡轻量应用服务器，Ubuntu 22.04、2 vCPU、4 GiB 内存、50 GiB 系统盘。它可作为轻量首页和留言 API 的初期部署候选；这是架构判断，尚未检查实际空闲内存、磁盘、原有服务、出口带宽与流量套餐，不能由配置推算并发人数。

GoDaddy 在这里负责域名注册或 DNS 管理；阿里云服务器负责运行程序。要先确认域名当前使用哪家的权威 DNS，再到对应平台修改解析。建议为小世界使用独立子域名，如 `worlds.xgenlabs.ai`，API 可同域放在 `/api/community/`，保留公司根域名和已有站点。

建议按以下顺序实施：

1. **连接与盘点**：通过已授权的 SSH 密钥连接服务器，检查现有 Nginx、端口、磁盘与站点配置，保留现有站点备份。当前没有 SSH 会话或访问授权结果，仅有截图，尚未执行这一步。
2. **准备可在 Ubuntu 运行的后端**：当前接口从 `cloudflare:workers` 读取 `env.DB`，维护者登录还依赖 Sites 的认证身份头。需提供 Node.js 服务与 SQLite 数据库适配，保留查询参数绑定、事务、留言限流与隐私分表；维护者改用可信的服务器认证，不允许客户端伪造原认证头。不能直接把现有 Worker 产物当普通 Node 服务运行。
3. **迁移数据**：通过当前 Sites 所有者可用的数据库导出能力取得备份，再导入新数据库；至少校验表结构、记录数量、时间、留言和联系信息的关联。D1 使用 SQLite SQL 语义，但 Sites 管理的真实 Cloudflare 数据库并不自动出现在用户自己的阿里云或 Cloudflare 账号中；未拿到受支持的导出权限前，不假定 `wrangler d1 export DB` 可直接导出线上数据。
4. **先验证新服务**：在临时地址测试读留言、提交、删除本人留言、管理权限、失败重试、请求限流与备份恢复。公开接口不得返回联系方式。旧数据库继续保留。
5. **接入域名与 HTTPS**：配置 Nginx 提供首页，反向代理 API 到本机服务；设置自动启动、HTTPS 和日志轮转。新域名与 API 同源可避免跨域依赖；若 GitHub Pages 也调用新 API，只允许实际前端来源。
6. **切换并保留回退**：完成校验后短暂冻结旧留言写入，导入最后差量，切换 `community-config.json.apiOrigin`；检查旧链接、新域名与手机访问。切换失败恢复原配置，避免两个服务各自写入造成留言分叉。

换域名时，浏览器本地存档和访客令牌不会自动跨域转移。必须明确支持的迁移方式；迁移了数据库不等于旧浏览器的相册、进度、删除留言权限也已迁移。备份和数据库文件放在网页公开目录之外，并建立定期备份。

## 大模型与首页的访问量分开安排

第 25 版首页只下载轻量封面与界面，用户选择世界后才加载游戏模型。X 模块为 `https://x.com/FrankFYM001` 普通链接，不加载第三方时间线组件。HTML 自带世界入口和作者链接，交互程序下载失败时仍有基本首页。

这提高首页加载独立性，但不承诺 GitHub Pages 不限流、所有地区网络都可达或任意并发。大模型如果继续占用同一个 Pages 站点的月度流量，仍可能影响站点整体。正式服务器部署时可将轻量首页/API 与模型下载分开托管；给大模型选对象存储和 CDN 前先核对预算、地域和实际流量。无需仅为了留言本先买更大的计算实例。

## 官方参考

- [Cloudflare D1：托管数据库与 SQLite SQL 语义](https://developers.cloudflare.com/d1/)
- [D1 数据导入导出](https://developers.cloudflare.com/d1/best-practices/import-export-data/)
- [阿里云轻量服务器域名解析](https://help.aliyun.com/zh/simple-application-server/user-guide/register-and-resolve-domain-names)
- [阿里云轻量服务器 HTTPS](https://help.aliyun.com/zh/simple-application-server/user-guide/quickly-configure-https)
- [GitHub Pages 使用限制](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
