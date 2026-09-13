# 第 24 版：手机速度与 PC 视觉分开

用户反馈三个世界都卡、手机柯南打不开。此次按手机优先操作与进入速度、PC 保留视觉细节实施。没有把桌面模拟结果当作真手机帧率。

## 定位证据

- 旧青蛙、柯南在 DPR 3 手机视口仍分配 1170×2532 画布和 4× MSAA。改后 390×844、2× MSAA；UI 保持 CSS 尺寸，横竖屏和大平板总像素有上限。
- 旧柯南公开清单可访问，下载包 206,713,911 B，解包 210,271,740 B。没有在用户原设备上复现打不开，因此不能认定唯一原因；资源、解码内存和渲染成本确实过重。
- Godot 局部阴影会重复绘制场景，点光阴影有六个方向；柯南还在每帧重设光照与天空。现在手机关闭局部实时阴影、保留主要太阳阴影和室内原有补光/烘焙光。昼夜参数只在状态变化时更新，手机天空云层静止。
- 只缩贴图不够：第一轮柯南仍有约 2,500 次绘制。随后保留碰撞和动画，对手机模型减面，再缩减阴影通道和远处绘制。

## 最终变化

| 项目 | 旧手机资源 | 新手机资源 |
| --- | ---: | ---: |
| 柯南压缩世界包 | 206.7 MB | 96.8 MB |
| 青蛙压缩世界包 | 178.0 MB | 102.6 MB |
| 柯南解包空间 | 210.3 MB | 99.2 MB |
| 青蛙解包空间 | 239.3 MB | 113.7 MB |
| 哆啦角色/动物/车辆模型 | 9.57 MB | 4.02 MB |
| 哆啦上述模型三角面 | 742,462 | 283,775 |

MB 按十进制字节计算；原生包大小不包含各自复用的 Godot 引擎。全部分块解压、偏移、大小、SHA-256 已在 [完整性记录](asset-integrity.json) 检查。PC 两个原生包摘要与第 23 版相同，哆啦 PC 文件及资产版本不变。

手机以 30 帧为目标，持续负载高时渐进降低 3D 分辨率；稳定后缓慢恢复，离开页面暂停绘制。PC 继续使用原始模型、贴图、较高分辨率及完整光照。手机保留 MSAA 和 mipmap，减少细密材质的闪烁；没有用关闭抗锯齿换速度。

手机 GLB 减面有误差上限，原始节点变换、动画轨道和骨架保持；原生显式碰撞网格不减面。蛙家两份烘焙房间几何保持，每层 HDR 光照图从 512 缩到 256，分层处理以防楼层串色。原生字体只保留实际原生界面字符和常用字符，HTML 界面继续使用系统字体。

## 渲染测量

[修改前](before/report.json) 与 [最终配置](final/report.json)：桌面 Chrome Metal，390×844 / 844×390，DPR 3、触屏模拟、4 倍 CPU 限速。每个视角取约 8 秒实际 WebGL 绘制；FPS 为有绘制调用的帧，三角面包含阴影等附加通道。不是手机 GPU 测试。

| 场景 | 旧三角面/绘制帧 | 新三角面/绘制帧 | 旧调用/帧 | 新调用/帧 |
| --- | ---: | ---: | ---: | ---: |
| 青蛙竖屏 | 19,278,336 | 624,524 | 472 | 120 |
| 青蛙横屏 | 8,528,411 | 542,960 | 365 | 131 |
| 柯南竖屏 | 7,949,489 | 925,422 | 3,754 | 1,241 |
| 柯南横屏 | 10,792,196 | 1,341,363 | 4,671 | 1,523 |
| 柯南事务所 | 7,201,220 | 1,148,087 | 2,857 | 924 |
| 哆啦竖屏 | 1,199,172 | 1,077,309 | 488 | 573 |
| 哆啦横屏 | 1,849,665 | 1,555,604 | 793 | 872 |
| 哆啦二楼 | 1,364,261 | 1,085,932 | 655 | 577 |

哆啦有运动中的角色、车辆及间歇更新的阴影，两个街景的调用数没有下降；主要收益是模型减面、每秒绘制帧数限制和像素减少。不能宣称所有指标都改善。最终测试各场景约 28.4–30 绘制帧/秒；这是桌面限速环境对目标帧率的检查。

## 入口、操作和恢复

- [Chrome 手机配置](chrome-entry/report.json)：从官网进入柯南，事务所、博士环形厨房、后车库、横屏均完成；真实触发 WebGL context loss 后出现重试并恢复。
- [WebKit 手机配置](webkit-entry/report.json)：上述房间与横屏完成。社区 API 跨域错误在 `environmentErrors` 单列，不混为场景错误。
- [PC 配置](desktop-entry/report.json)：从官网进入，读取原始根目录清单，画布仍为 DPR 2，无手机降级策略。
- [青蛙室内](frog-entry/report.json)：通过原有输入从出生点走入树干小屋，光照图、家具、横屏可显示。
- [哆啦慢网恢复](doraemon-recovery/report.json)：6 Mbps、150 ms 延迟、4 倍 CPU 限速，取消实际下载后重试进入二楼，离线缓存重入、503 重试、触屏行走/停止均通过。
- [哆啦 WebKit](doraemon-webkit/report.json)：通过实际“去二楼”按钮进入，横竖屏、返回街道及重入完成，场景着色器无错误。首屏实际模型下载 19,372,938 B，首次进入二楼增加 11,646,005 B；清单中的全部贴图大小与实际引用下载大小分开记录。
- `npm run typecheck`、`npm test`、`npm run test:mobile` 通过，覆盖两条楼梯、二楼原门口、房间下载取消重试、缓存与多指操作。Sites 正式构建和 Pages 构建通过。

原生错误处理会将图形错误与连接错误分开；运行后丢失图形上下文，也重新显示错误面板。父页面重试重新建立引擎。错误后的晚到 READY 消息不能覆盖失败状态。

## 重建方式

工具依赖沿用 `tools/mobile-assets` 固定版本；另需 Python fontTools、Godot 4.7.2。原生派生项目必须放在独立目录，当前脚本保护条件为路径包含 `native-mobile24`。

```sh
node tools/prepare-native-mobile.mjs conan ../native-mobile24/conan
node tools/simplify-native-mobile.mjs ../native-mobile24/conan
python3 tools/subset-native-mobile-font.py ../native-mobile24/conan
python3 tools/export-native-web.py conan OUTPUT/worlds/conan/mobile --project ../native-mobile24/conan --mobile --godot GODOT_PATH
node tools/build-doraemon-mobile-actors.mjs
```

青蛙对应执行同一流程，并在导出前用 Godot 的 `--script tools/resize-mobile-lightmaps.gd` 按层处理四份 EXR；脚本是离线素材加工，不在导出游戏中执行。不要在减面后再运行复制准备步骤，否则会覆盖派生加工结果。手机目录只需发布分块、清单和字体许可证，复用世界根目录的引擎。

模型与字体逐文件记录：[柯南减面](conan-mobile-geometry-report.json)、[青蛙减面](frog-mobile-geometry-report.json)、[哆啦角色](doraemon-mobile-actors.json)、[柯南字体](conan-mobile-font-report.json)、[青蛙字体](frog-mobile-font-report.json)。图像缩减阶段报告单独记录，不能把该阶段的“几何不变”误解为后续未做减面。

## 状态

设计取舍已实施；PC 模型源文件保留，手机派生文件已生成；浏览器引擎验证及网页发布完成，真实手机仍未测。

## 公开发布与复验

- 运行时代码：`e9955b0344e8989fee1b419af86a09fd186f1fca`，已同步到 `main` 与 `feat/xlands-worlds-community`。本记录后续的文档提交不改变公开资源的 `sourceCommit`。
- Pages 发布：`cb7e644f3ad88ec69f08843b1d28be6aabdb1d18`，文件树 `89b3f354c44fa5d413b9685d8031ebd306fcc94b`；[部署工作流](https://github.com/frankfanyiming/frank_worlds/actions/runs/34751340259) 成功。
- [公开 release.json](https://frankfanyiming.github.io/frank_worlds/release.json?v=24) 为第 24 版。重新下载两个手机世界全部 35 个分块，检查压缩长度、解压长度、逐块 SHA-256 和完整包 SHA-256；另核对 12 个手机角色、动物、车辆 GLB 摘要，均通过：[公网资源完整性](public-integrity.json)。
- [公网柯南 Chrome 入口](public-conan/report.json)：从门户进入后实际请求 `/worlds/conan/mobile/world-pack.json`，事务所、博士厨房、后车库及横屏均正常显示；真实触发图形上下文丢失后，通过门户“重试”重新进入。该次 Chrome 检查没有场景或社区 API 错误。
- [公网柯南 WebKit 入口](public-conan-webkit/report.json)：同样读取手机资源，事务所、博士厨房、后车库及横屏均正常显示，无场景错误；三个社区 API 错误在 `environmentErrors` 保留。
- [公网哆啦 WebKit 原始记录](public-doraemon-webkit/report.json)：实际点击“去二楼”后房间进入完成，横屏、返回街道与缓存重入均完成，着色器错误为空。不过总检查为失败，原因是三个社区 API 跨域错误；原始结果保留，不能改写成全通过。[独立判读](public-doraemon-webkit/assessment.json) 记录场景成功与社区失败的边界。

社区 API 的独立 HTTP 探测得到 Cloudflare `403` HTML 保护页（`Attention Required!`），并非应用 JSON 响应；请求使用的是公开 GitHub Pages 的 Origin。此轮没有修改后端或绕过访问保护。该问题影响此次 WebKit 环境中的社区列表/来访本，实测未阻止柯南和哆啦场景进入。

公开入口检查只在进入后短暂读取渲染诊断，初始和重试后的 FPS 包含启动期，不能作为稳定性能结果。稳定绘制测量见上文 `final/report.json`；全部浏览器验证仍为桌面触屏模拟。
