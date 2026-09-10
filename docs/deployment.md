# 运行与部署

公共入口保持为 https://frankfanyiming.github.io/frank_worlds/ 。GitHub Pages 承载首页与三套按需加载的世界资源；共享数据 API 由登记的 Sites Worker 与 D1 提供。

`worlds/doraemon/web/public/community-config.json` 的 `apiOrigin` 指向部署后的服务地址。Sites 的界面使用同一 GitHub 地址加载模型资源，避免重复保存大型文件。

## 数据

数据库结构由 `db/schema.ts` 和 `drizzle/` 中的追加迁移定义，不在请求期间创建表。留言和联系邮箱分表存储；公开接口仅投影留言字段。公开作品与提案保留不可变快照，主世界变更使用带版本条件的事务更新。

运行 `npm run test:community` 验证隐私、所有权、公开快照、合并、冲突、回退以及支付验签。`npm test` 保留原哆啦A梦世界的加载、室内、交通和恢复测试。

维护者通过 Sites 的登录入口登录。`OWNER_ACCOUNT_EMAIL` 必须在服务端设为密钥，并与平台提供的已认证邮箱匹配；不能从浏览器传入维护者身份。

## 付费 Agent 配置

这些值均在服务端配置，密钥不能放进 Git：

- `OPENAI_API_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `AGENT_CREDIT_PRICE_ID`：Stripe 中的余额商品价格
- `AGENT_CREDIT_MICROS`：每次购买获得的美元微单位额度
- `AGENT_MARKUP_BPS`：计费倍率的万分比，10000 表示按模型成本结算
- `PAID_AGENT_ENABLED=true`：所有配置验证完成后才打开

Stripe 通知地址是服务端 `/api/community/billing/webhook`。账户余额使用站点登录身份，不使用匿名访客浏览器凭证。配置后还需使用支付测试模式验证购买、重复通知、失败退款和余额恢复，再开放真实收款。

模型成本常量以 [OpenAI GPT‑6 Astra 官方模型页](https://developers.openai.com/api/docs/models/gpt-6-astra) 为依据；定价发生变化时更新计费常量后再开放服务。中断超过十分钟的预留请求会在账户下次查询余额或发起请求时自动退还；失败请求不能计为成功消费。

## 公司官网

设置服务端 `COMPANY_URL` 后，首页的“关于我们”会变成外链。未配置时不跳转到临时或无关页面。

## 原生世界的网页打包

Godot 4.7.2 使用 Compatibility 渲染和无多线程 Web 模板，以适配 GitHub Pages。柯南导入配置限制环境纹理尺寸并保留主角 4K 贴图，原版桌面模型单独归档。较大的资源包拆成小于 GitHub 单文件限制的片段，每段校验 SHA‑256，支持并行下载与重试。进入某个世界时才加载它的资源。

首页和共创界面为五语言；原有世界中的部分故事对话暂保留中文，新增的旅行蛙主要控制与网页操作提示已有对应翻译。

导出步骤：安装 Godot 4.7.2 及其官方 Web 导出模板，下载对应源资产后，执行 `python3 tools/export-native-web.py frog /absolute/output/worlds/frog --godot /absolute/path/to/godot`；柯南将 `frog` 换为 `conan`。`tools/test-native-web.mjs /absolute/output/worlds` 可以校验两套加载器与完整资源包。源码下载默认保留已存在文件，不覆盖本地改动。
