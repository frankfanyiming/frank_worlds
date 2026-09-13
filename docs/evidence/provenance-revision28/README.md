# 第 28 版：手机提示与项目出处

本轮增加提示，不宣称手机性能问题已经解决。首页保留现有三个封面、不恢复头图或留言板；场景模型和游戏包沿用第 27 版。

- 五种语言手机提示：静态首页、React 首页、三世界共享导航下方；可在页签内收起，不回传关闭事件。青蛙/柯南独立页面加载与菜单也有提示。
- 56 份项目自有源码加入 SPDX、作者和原始仓库注释；依赖与模型不批量改写。根目录 `SOURCE.json`、`NOTICE`、`PROVENANCE.md` 说明来源和适用范围。
- Vite 两条构建路径保留公开来源 banner 和 Git 提交；附带 `provenance.json`、`NOTICE.txt`、`LICENSE.txt`、`SOURCE.json`。文件散列不是签名，不保证恶意删除后的追溯。
- 类型检查、原有场景/加载/房间检查、首页失败恢复检查通过。触控检查最初只截取 UI 函数，缺少新加入的共享文案常量；改为从同一源文件加载该声明，再验证原始多指归属、菜单释放和恢复逻辑，均通过。

此处记录源码、构建与公开文件检查，未做新的浏览器或真实手机帧率测试。

首次产物校验发现 Vite 8 / Rolldown 的压缩会删除普通 banner，即使 `/*!` 注释也不保留。改为压缩后的 `postBanner`，并将提交标识纳入 chunk hash；文件清单在生成 HTML 后记录。不能以“构建通过”替代逐文件来源标识检查。

## 最终验证与上线

- 运行源码提交：`5a2d00919b67eab3ac8a042b52b5e479c43539eb`。
- Pages 提交：`d8ac34687a46a66390b5279ccf8686163eac5ad5`；[部署 34762822590](https://github.com/frankfanyiming/frank_worlds/actions/runs/34762822590) 于 2026-09-13 14:31:26 UTC 成功。
- 官方 Sites 构建和 Pages 构建均通过；分别校验 24、15 个构建文件。合并原生壳与声明后，发布目录的来源清单共校验 23 个文件；临时副本中修改文件后校验按预期拒绝。
- 线上 [第 28 版](https://frankfanyiming.github.io/frank_worlds/?v=28#) 的 33 个文件均返回 200，字节与 SHA-256 全部一致；四个既有 PC/手机世界包清单保持一致。首次 HTTP 核对遇到 TLS 握手超时，第二次完整核对通过；不把一次传输异常描述成应用崩溃。
- 首页核心静态资源从 895,535 B 到 899,567 B，增加 4,032 B。此数是文件总量，不是实测手机传输量或帧率；来源 JSON 不新增自动回传请求。
- 仅复制指定网页文件并保留旧哈希文件；模型、字体、Godot 引擎和世界包未重新导出。三个原封面、Nobita v27 房屋、卧室 v12 与其他住宅保留。

数据见 `build-audit.json`、`provenance.json`、`publish-files.json`、`public-audit.json`、`deployment.json`。源代码和证据已推送原仓库 `main` 与 `feat/xlands-worlds-community`。
