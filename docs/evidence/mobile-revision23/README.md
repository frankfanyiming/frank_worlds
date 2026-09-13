# 哆啦A梦手机优化 · 第 23 版

2026-09-13。用户报告手机二楼打不开、严重摩尔纹和卡顿。原始模型与贴图没有覆盖；本轮生成 14 个独立移动派生 GLB 和房间材质，并修改实际 Three.js 运行逻辑。

## 可核对结果

| 项目 | 第 22 版 | 第 23 版 |
| --- | ---: | ---: |
| 触屏首屏实际模型/地图下载 | 28,727,242 B | 24,920,418 B |
| 首次上二楼新增实际下载 | 244,696,541 B | 11,646,005 B |
| 房间已下载后重新进入 | 复用场景 | 复用场景，无新增下载 |
| 手机抗锯齿 | 关闭 MSAA | 保留 MSAA，DPR 1–1.35 自适应 |
| 室外的室内灯 | 仍参加渲染 | 按房屋和楼层开启 |
| 曾访问的二楼 | 继续参与室外渲染 | 室外隐藏，进入复用 |

实际下载子集小于 `asset-sizes.json` 的全部材质文件总量；不能把未请求的可选材质都算作进屋流量。源/派生文件 SHA-256、节点变换合同、纹理分辨率和精确工具版本见 [mobile-assets.json](mobile-assets.json)。

[第 22 版基线](before/report.json)与[正式构建 Chrome 测试](production-chrome/report.json)使用 390×844 / 844×390、DPR 3 的桌面触屏模拟。后者另外使用 4 倍 CPU 限速，二楼竖屏/横屏每帧平均提交约 0.87M / 1.36M 三角形；6 秒采样的 p95 帧间隔为 16.7 / 16.8 ms。旧版同视角 p95 约 33.4 ms。旧版没有记录逐帧平均面数，仅有抽样帧计数，不能直接把其影子更新峰值与新版平均值相除。

这些测量不是手机 GPU 或真机帧率。真实 iPhone/Android 的浏览器、GPU、内存和发热表现仍需真机复核。

## 画面证据

- 改动前：[街区](before/street.png)、[二楼](before/bedroom.png)。
- 正式构建：[街区](production-chrome/street.png)、[二楼竖屏](production-chrome/bedroom.png)、[二楼横屏](production-chrome/bedroom-landscape.png)。
- [下载尚未结束的真实进度](recovery/download-progress.png)、[服务器故障后的重试入口](recovery/retry-ui.png)。
- [WebKit 正式构建记录](production-webkit/report.json)：街区、二楼、横竖屏、退出与重入均完成，场景着色器无报错。本地 `127.0.0.1` 对社区 API 的跨域拒绝独立保留在 `environmentErrors`；没有用这个测试宣称社区 API 通过。

## 恢复与交互

[正式构建恢复测试](recovery/report.json)使用真实模型解码和浏览器触屏输入。设置 6 Mbps 下载、150 ms 延迟、4 倍 CPU 限速后，下载中取消确实中止 HTTP；马上重试约 16.2 秒进入二楼。新引擎从已保存缓存断网进入二楼，新增 24 次缓存命中、没有新增下载。主动返回 503 后通过原重试按钮恢复。摇杆移动约 0.95m，同时原角色动画由 Idle → Walk → Idle。

验证命令：

```sh
cd worlds/doraemon/web
npm run typecheck
npm test
npm run test:mobile
npm run build:pages
```

`tools/test-doraemon-mobile-performance.mjs` 可通过 `WORLDS_URL` / `MOBILE_EVIDENCE` / `CPU_THROTTLE` 指定测试；`BROWSER=webkit` 与 `PLAYWRIGHT_BROWSERS_PATH` 选择已安装的 Playwright WebKit。`tools/test-doraemon-mobile-recovery.mjs` 测真实下载中断、冷/暖缓存、HTTP 错误恢复与触屏动作。Sites 构建脚本也已通过；公开门户继续使用原 GitHub Pages 架构。

[桌面回归](desktop/report.json)也已进入原始高精度二楼，确认没有请求任何 `mobile-v23` 资源，场景及着色器无报错。

[三世界组合检查](three-worlds/browser-report.json)已通过：青蛙与柯南都真正启动并显示正常横竖屏菜单，运行包摘要与第 22 版相同。

## 可重复生成

```sh
npm ci --prefix tools/mobile-assets
node tools/build-doraemon-mobile-assets.mjs
```

工具依赖独立固定在 `tools/mobile-assets/package-lock.json`，不会加入网页运行依赖。可用 `MOBILE_ASSET_TOOLS` 指向已安装同版本工具的目录。构建只写入 `public/models/mobile-v23/`、`public/bedroom-materials/mobile-v23/` 与本轮资产报告。必须重新校验生成结果和实际截图后发布。

## 状态区分

模型源文件保留；移动派生文件已生成；引擎验收为桌面 Chrome/WebKit 的真实 WebGL 场景及触屏模拟；网页已正式构建。公开发布以随后记录的 `release.json`、源代码提交及 Pages 工作流结果为准。青蛙、柯南原生包保留第 22 版摘要。


## 公开发布确认

第 23 版已发布至 [GitHub Pages](https://frankfanyiming.github.io/frank_worlds/?v=23#world/doraemon)。运行源码 `3f366d6d18fc6085f2e3b9d2f1a0ad2e4c8ef26a` 已推至 `main` 与 `feat/xlands-worlds-community`；Pages 为 `9db0ad7411f694e408eef9031d7b62c79a7a47d0`。[工作流 34747740476](https://github.com/frankfanyiming/frank_worlds/actions/runs/34747740476) 的构建与部署均成功。

[公开资源完整性](public-browser/release23-public-integrity.json)核对了 61 个入口、脚本、移动模型和材质的完整 SHA-256，28 个原生运行包分块可访问且大小一致。第一次验证遇到网络 `IncompleteRead`，完整重读后散列一致，没有使用收到的部分内容当作通过。

[公网场景复验摘要](public-runtime-summary.json)：Chrome 与 WebKit 都以手机尺寸真正进入二楼，新资源总下载 36,566,423 B，包含首屏 24,920,418 B。WebKit 另完成横竖屏、返回街道和重入。[Chrome 请求级跟踪](public-chrome-trace/trace.json)和[WebKit 原始报告](public-webkit/report.json)完整保留；Chrome 首次首屏等待超时也保存在 [初次报告](public-chrome/report.json)，重新运行时进度由 49% 到 100%、二楼正常完成，不将初次失败计作通过。

整页检查有一项明确限制：[社区 API 自动化请求](public-community-check.json)收到 Cloudflare 403 HTML 响应，缺少 CORS 头，WebKit 的全局错误断言因此未通过。没有绕过访问保护，也没有把这一项改成绿色。它与 GitHub Pages 场景资源分属不同服务；上述模型、材质和二楼状态校验已通过。本轮不能宣称社区服务或真手机全部验收通过。

后续仅提交这些验收文档，不改变 `release.json.sourceCommit` 对应的运行代码。
