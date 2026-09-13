# 第 25 版：首页与作者入口

用户要求优先保障首页访问，增加作者 X 账号模块，并说明留言本现状与自有服务器部署方式。

- 作者卡片链接 `https://x.com/FrankFYM001`，保持现有首页色彩，支持五种界面语言。普通外链不引入 X 时间线脚本、iframe 或接口请求。
- 首页三张封面从合计 7,278,558 B PNG 改用 384,870 B WebP（960×720），原图片保留；不改变世界中的模型、材质或运行配置。
- 返回的 HTML 自带轻量首页、世界入口与作者外链；主程序下载失败时仍可显示。React 渲染错误时回退到同一份静态内容。基本首页不依赖留言接口、3D 引擎或 X 服务器响应。
- 构建清单中首页入口不静态依赖 Three.js/世界引擎；世界与共创界面仍为用户进入后按需加载。
- 已通过 `npm run typecheck`、已有 API 配置/超时/HTML 拦截错误恢复测试、Sites 正式构建和 Pages 构建。对实际构建 HTML、图片及动态依赖图的核对见 [构建审计](bundle-audit.json)。未额外开展浏览器视觉或真机性能测试。

核心 HTML、首页 JS/CSS 和三张封面合计 881,695 B；文本 gzip 后估计约 509,816 B。该数字不包含社区 API、favicon、HTTP 请求头，也不代表公共服务器实际压缩或下载时间。静态 HTML 约 4.3 KB，可在交互脚本未完成时提供入口。

## 数据核验

通过 Sites 只读接口核对现有公开项目仍处于 active 状态、版本 4；线上数据库绑定为 `DB`，存在 `notes`、`contacts`、`visitors` 等 11 张业务表。仅查表名，没有读取留言正文或联系方式。当前留言数据库仍由 Sites/Cloudflare D1 托管，没有迁至用户截图里的阿里云。

[自有服务器方案](../../self-hosting-plan.md) 区分域名解析、静态网页、API 与数据库，记录 Worker 到 Node/SQLite 适配、可信管理身份、数据导出权限、换域本地存档隔离和切换回退。方案已写出，服务器连接、DNS 修改与数据库迁移均未执行。

## 发布

保持既有 GitHub Pages 前端与 Sites API；仅发布首页 HTML、前端编译产物与新增封面，世界资源保持第 24 版。

- 运行时代码：`82ee053d8116f322f38db2ebe9a38aa1c5cdc032`，已推送至 `main` 与 `feat/xlands-worlds-community`。
- Pages 发布：`b0d0079cef80864684edda2938496f0469285cd6`；[部署工作流](https://github.com/frankfanyiming/frank_worlds/actions/runs/34754652849) 成功。
- [公开首页](https://frankfanyiming.github.io/frank_worlds/?v=25#) 与 `release.json` 已更新至第 25 版。
- 使用 [验证脚本](../../../tools/verify-homepage-release.py) 重新读取公开站点，16 份首页文件均返回 HTTP 200，长度及 SHA-256 与验收候选一致；另核对四份 PC/手机原生世界清单仍指向既有资源包：[公网校验](public-audit.json)。本地 HTTP 校验另存于 `local-http-audit.json`，不混为公网结果。
- 编译器会因主入口哈希变化重新命名延迟模块，发布时保留旧哈希文件以支持尚未关闭的旧页面；没有重新上传世界模型包或改动留言 API。
