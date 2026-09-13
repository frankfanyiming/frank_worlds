# 第 26 版：保留封面的漫画首页与分享资料

用户选择 A 漫画分镜后，明确保留现有三个世界封面。本轮只调整首页排版和表现，三张 WebP 的 SHA-256 与第 25 版相同；游戏模型、移动分档与四份原生世界包清单保留第 24 版。

## 本轮内容

- 品牌为 `XLands小世界`；分镜卡片、纸页式制作手记、轻量横幅，适应窄屏并保留五种语言。
- X 使用 `@FrankFYM001`；小红书采用用户提供的个人主页 URL。抖音 `/user/self` 会打开访问者自己，不作为公开作者链接，改为显示和复制 `frank001`。
- 飞书制作手记已创建并回读，分享设置核验为 `external_access_entity=open`、`link_share_entity=anyone_readable`；另提供无脚本网页副本及 5 个通过结构校验的 Skills。
- 首页加入纯热爱、非商业非盈利、IP 未获授权的说明。未将声明视作 IP 许可，未发布私聊截图或联系邮箱。
- 静态 HTML 具有品牌、原封面、世界入口、制作资料和三种联系方式。脚本未载入、React 渲染错误、运行时未捕获异常，均可展示联系引导。错误触发恢复时延后卸载，避免 React 提交期间同步卸载；重复错误只安排一次恢复。
- 留言上游故障仍存在，未改动或迁移后端。失败不清空输入；文案明确尚未保存，可主动复制正文或去 X 反馈，复制内容不含邮箱。

## 验证范围

- `npm run typecheck`、原有运行/延迟房间加载检查、126 项社区服务检查通过。
- `node tests/client-network.test.cjs`：配置重试、公共请求、403 HTML 与连接超时处理通过。
- `node tests/home-recovery.test.cjs`：模块失败、超时、React 兜底、运行时错误、延迟卸载与重复错误通过；在 Node 适配器内执行入口代码，没有启动浏览器。
- Sites 正式构建及 Pages 构建通过。构建入口没有静态依赖 Three.js 或世界引擎；原封面逐字节保留。详见 [构建审计](bundle-audit.json)。
- 核心 HTML、首页 JS/CSS、原封面与新增横幅合计 1,005,234 B。文本 gzip 后估计 617,412 B，排除 API、favicon、请求头；不是 CDN 实测压缩、下载时间或真实手机帧率。
- 本轮未做浏览器视觉或实体手机测试。完整浏览器进程崩溃、网络无法取得 HTML 不在页面脚本兜底范围内。

## 发布状态

- 运行时代码 `b6b8a0010a74107bf817b8d433dc99e152cf9f32` 已推送到 `main` 与 `feat/xlands-worlds-community`。
- Pages 提交 `9c0b0e2204a0f3bfdde9e93b5a84b15bcce97e5b`；[部署工作流](https://github.com/frankfanyiming/frank_worlds/actions/runs/34758137020) 成功，公开 `release.json` 对应第 26 版与上述源码。
- [公开首页](https://frankfanyiming.github.io/frank_worlds/?v=26#)、[飞书手记](https://xgenlabs.feishu.cn/docx/EHsmd08qGo3T7nxWKIMchlcGnvb)、[网页手记](https://frankfanyiming.github.io/frank_worlds/resources/making-of.html) 与 [Skills ZIP](https://frankfanyiming.github.io/frank_worlds/resources/xlands-skills.zip) 已提供。
- [公网校验](public-audit.json) 从正式域名读取 19 份首页相关文件与 4 份保留的世界清单，HTTP 200、长度与 SHA-256 均一致。本地结果另见 [本地 HTTP 校验](local-http-audit.json)，不混为公网或浏览器结果。
- 首次公网校验有一笔读取超时；第二次重新完整核验通过。没有修改发布字节来消除网络失败，也不因此承诺任意网络都无超时。
- 发布范围限首页 HTML、编译模块、横幅、文章及 Skills；旧哈希模块保留，供尚未关闭的旧页面使用。

另见 [原房屋恢复证据](../doraemon-house-recovery26/README.md)：已找回并单独保存，未把旧房屋或旧控制器上线。
