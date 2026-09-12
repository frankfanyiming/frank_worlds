# 手机端 3D 世界制作与验收

本轮范围：小世界门户、Three.js 哆啦 A 梦、Godot 青蛙与柯南的网页壳，以及独立的 XGEN 官网候选。代码、浏览器模拟、真手机和公开发布是不同状态；不能把桌面 Chromium 的手机模拟写成真机验收。

官网候选的四个文件已按逐文件 SHA 清单回写原 `2026-09-11/kan-x/outputs/xgen-site`，备份与回写后校验通过。公司公开域名尚未提供，此项是原项目更新，不代表另行公开部署。

## 画布与界面用同一尺寸

- 网页使用 `viewport-fit=cover`、`100dvh` 和 `env(safe-area-inset-*)`；游戏画布填满导航条下面的区域，不能按固定 1440×900 比例留黑边。
- Godot `canvas_items` + `aspect=expand` 只解决比例；手机上仍以 1440 个逻辑像素排版，会把 15px 字缩成约 4px。本轮桥接按 CSS `innerWidth/innerHeight` 设置 `Window.content_scale_size`，不乘 DPR，再调用世界的 `_mobile_layout(Vector2)`。
- 顶栏、菜单、相册用手机布局，动作与摇杆留在屏幕下部。横屏也必须走触屏规则，不能只用 `max-width:720px`：844×390 手机横屏仍需要 44px 目标。
- 独立顶部导航比游戏内弹窗层级高的旧 CSS 会压住弹窗标题和关闭按钮。本轮将浮层放到导航之上；关闭按钮固定在弹窗内并保留 44px 命中区域。

## 多指输入要逐个归属

- 摇杆、画布视角、跑步、跳跃各自保存 pointerId；不能把所有手指共用一个 `pointer.down`，也不能在任何一根手指松开时把移动全清零。
- `pointerup`、`pointercancel`、`lostpointercapture` 仅释放自己拥有的指针。窗口失焦、页面隐藏和尺寸变化则整体清零，避免回来后一直走。
- 原生壳通过 `xlandsMove(x,y)` 发送 [-1,1] 轴强度，由 bridge 分成四个 `Input.action_press(action,strength)`；世界控制器保留向量幅度。`xlandsLook(dx,dy)` 直接调用 `_touch_look`，不用假按鼠标右键或请求 pointer lock。
- 触屏不再模拟鼠标，避免 Godot 的合成鼠标运动又转一次镜头；真实鼠标/键盘仍沿用原有输入。
- 官网轮播从子卡片转交 pointer capture 给父容器时，旧卡片的 `lostpointercapture` 会冒泡。本轮误把它当作拖动结束，实测滑动不切换；仅处理 `event.target === carousel` 后恢复。

## 真正可点比看起来有按钮更重要

- 哆啦 A 梦时间按钮曾继承 `.topbar {pointer-events:none}`，只有 div 子项恢复命中，button 没恢复；截图看起来正确，实际点到背后的画布。本轮用真实点击发现并修正。
- 门户的通用表单 label 规则会把世界导航中的语言控件排成上下两行，横屏溢出。明确排除 `.world-language`，不能只再叠字号补丁。
- 表单保持至少 16px 输入字号，弹窗限制在有效视口内并可滚动。保留语言、音效、来访本、Agent 与保存功能。
- PopupMenu 文本需单独翻译。用节点 metadata 记录原文与上次显示文本；不要占用 item metadata，柯南的传送位置依赖它。菜单重建后检测文本变化，避免重复翻译丢失原文。

## 载入与手机成本

- 柯南 APTX-4869 胶囊只是视觉外观，填充使用原下载器的实际字节进度。仍保留 Range 续传、gzip 解压、SHA-256/长度校验、超时和重试；不要用定时器编造进度。
- 哆啦 A 梦初始街道约 28.6MB，原卧室模型与高精度材质合计约 244.7MB。旧逻辑在街道显示后 1.5 秒就后台载入卧室，手机模拟出现渲染竞争。本轮触屏仅在请求进屋时下载完整卧室，桌面保留预载；没有悄悄换低精度模型。
- CUA 无浏览器通道、截图不可用时，本轮使用独立无头 Chromium + Metal 做自有页面回归；初次软件渲染叠加大房间载入导致截图超时，不应当把超时当成 UI 已通过。

## 室内光照

哆啦 A 梦卧室原来单独压低半球光到 40%，封闭房间失去直射光后更暗。本轮增加室内间接光的最低值，保留昼夜变化；静香家补窗边面光和室内灯，不改室外曝光。最终视觉以实际房间截图判断，不能只根据灯的数值。

青蛙的静态房间已有 LightmapGI，直接调实时环境光不会重写烘焙结果。本轮保留既有阴影与日夜烘焙，在屋内启用低强度漫反射补光，不另加高光；与关闭补光的相同视角比较。Godot 的 LightmapGI 没有可直接设置的全局 `energy`，不能根据别的 GI 类猜属性。

柯南新建筑的材质值经运行时核对与 Blender 色号一致，发白来自强直射光、环境光与窗边补光叠加。Compatibility 实机同机位比较了日光 .82/.50/.32，最终 .42、环境 .40，并将窗光乘 .65。各室继续使用有范围的局部光；不要为了提亮一个房间把所有外墙夹成纯白。新阿笠几何不可继续读取旧形体的 VoxelGI 缓存，缓存名称包含本轮版本。

地下室吊顶即使存在，也可能在旧地形实体上方，从下方先看到草坪底面。必须在真实视角核对最近可见表面，本轮把实际吊顶下表面移到 -.56m，保留楼梯孔；不是把户外地形全部隐藏。

## 可复验入口

- `worlds/doraemon/web`: `npm run typecheck`、`npm test`、`npm run test:mobile`。
- `tools/test-mobile-browser.mjs`：独立 Chromium，门户/哆啦本地 8784、官网候选 8785；浏览器包和 Chrome 路径可用环境变量覆盖。截图及报告在 `docs/evidence/mobile/`。
- `docs/evidence/mobile/bridge-unit.gd`：隔离 Godot 项目，`XLANDS_REPO` 指向本仓库；验证 bridge 解析、PopupMenu 原数据保留、重复翻译、摇杆强度和释放。此次使用 Godot 4.4.1 做这些独立检查，不替代主任务的 4.7 场景导出验证。
- `tools/test-mobile-world.gd`：Godot 4.7.2 实场景布局与正常物理移动；隐藏容器子项后必须延迟重设 `size`，否则原桌面最小宽度会残留。
- `tools/test-native-mobile-browser.mjs frog|conan`：实际导出 WebGL2 包，检查横竖屏、三指同时移动/转视角/跑步及全部释放。`native-frog/`、`native-conan/` 保存运行报告，不能把本地缓存下载秒数当作公网或真手机速度。

## 内嵌手机菜单必须实际点到目的地

门户外层与独立游戏页都要测试。最后一轮发现 Godot PopupMenu 在触屏只打开、不接收列表行点击/拖动；HTML 摇杆还盖住下方项目，canvas 的转视角回调绕过引擎 UI 消费事件。鼠标滚轮能滚不代表手机能用。

本轮手机菜单使用同一 Godot 条目 ID 和位置 metadata，由网页滚动面板承接显示与触摸，点选回调原 `id_pressed`。条目逐项显式翻译；MenuButton 的内部 PopupMenu 不在普通子节点遍历中，不能假设已翻译。菜单及相册/行囊打开时隐藏触控、清空所有轴并暂停视角，关闭恢复。引擎碰撞与物理控制不变。


## 2026-09-13：网页界面只能由一层负责绘制

用户截图出现原生 Godot PopupMenu 与 HTML 菜单同时展开、原生相册盖住整屏、外层又叠键盘帮助。逐个加 z-index 不能解决双重拥有者。本轮网页由 `native-loader.js` 的同一个 HUD 和同一个 sheet 绘制；Godot CanvasLayer 保留节点与动作回调但在 Web 隐藏。相册、行囊、朋友日记和目的地共用面板；切换时关闭上一面板，遮罩、Esc、焦点循环、滚动区与输入锁共享。非网页的引擎检查仍可用原生 UI。

桥接读取世界的源状态再渲染，不再每隔 0.4 秒递归改写整棵场景的 Label。动态相册数字、行囊计数、照片地点、区域和 NPC 对话均按固定源词条/格式模板翻译；朋友模块直接提供指定语言的语义卡片。仅补静态按钮词表仍会漏掉互动提示。

### 实际画布还会改变浏览器的 CSS 视口

隔离 HTML 的五语言 × 三尺寸测试通过后，真实 Godot 导出包从 1440px 改到 390px 时，引擎保留了 `canvas style="width:1440px"`。移动 Chromium 因此把 `innerWidth` 扩到1440、`innerHeight`扩到3117，UI整体缩小；`document.scrollWidth == innerWidth` 此时仍然为真。通过检查实际 canvas 内联样式定位，最后给 canvas 施加视口内的 CSS 宽高与尺寸包含约束，保持绘图 buffer 独立，才恢复390×844。测试必须断言 CSS 视口等于目标设备尺寸，并真的做横竖屏切换；只看截图能打开或文档不横滚不能算通过。

### 长弹窗要把关闭与内容滚动分开

哆啦A梦使用 Base UI 的 `data-open`，不是 Radix 的 `data-state=open`。首次检查误用后者得到超时，修正选择器后才验证真实弹窗。口袋、设置、交谈和帮助采用统一暂停状态，打开新面板前关闭已有对话；固定关闭按钮放在独立滚动内容外。逐项测量发现旧按钮只有35–42px，已统一44px，再滚到底检查关闭按钮仍在视口内。滚动区域中未滚到的项目可以在可见边界外；关键是可滚达、命中尺寸正确，且关闭入口不被卷走。

本轮可复验入口：`tools/test-native-ui-bridge.gd`、`tools/test-native-interface-browser.mjs`、`tools/test-doraemon-interface-browser.mjs`。`--shell-only` 只是隔离 HTML 布局检查，不能当世界运行证据。实际记录见 `docs/evidence/ui-revision21/`，设备均为桌面 Chrome 触屏模拟，尚未覆盖真机 Safari。
