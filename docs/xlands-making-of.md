# XLands 小世界制作手记：从参考图到可游玩的三个世界

Frank · 2026-09-13 · 公开分享版。写给想用 AI、3D 工具和代码，把喜欢的场景做成可进入网页的个人创作者。本文依据项目源码、资产来源记录和各轮验收报告整理；不是一键生成教程，也不把概念图当成实机。

我想做的是能走进去、能停下来、能和朋友过日常的小世界。三个世界分别是哆啦A梦小镇、旅行青蛙和柯南小镇。制作中最花时间的部分，是不断对照参考、进入游戏检查，再修正模型、动作、光照、手机体验和发布链路。

[进入 XLands 小世界](https://frankfanyiming.github.io/frank_worlds/)

[源码与工程目录](https://github.com/frankfanyiming/frank_worlds)

## 先讲清楚：现在做到了哪一步

| 对象 | 实际实现 | 边界 |
| --- | --- | --- |
| 哆啦A梦小镇 | Three.js 网页运行时，室内外、二楼、道具、昼夜与移动触控 | 手机派生资源保留 PC 原始视觉；现有性能报告属于桌面浏览器触屏模拟 |
| 旅行青蛙 | Godot 网页世界，青蛙与熊猫、两户住宅、串门、料理、送礼、同行野餐和共同照片 | 基础朋友玩法与存档在浏览器本地；尚无跨设备同步 |
| 柯南小镇 | Godot 网页世界，街区、事务所、博士住宅、角色与开放家具接入 | 按参考重建，制作尺寸有推定；并非官方完整米花町测绘还原 |
| 官网与来访本 | GitHub Pages 承载首页和世界资源；独立 Sites Worker/D1 承载共享数据 | 当前部分访问收到上游 403 保护页，留言未恢复；可去作者 X 留言 |
| 开源状态 | 可读源码、制作脚本、来源清单、网页运行资源已发布 | 完整原始模型归档仍标记 pending-publication；干净克隆不能直接恢复全部编辑模型 |

我把交付分为四个状态：设计提案、模型源文件、引擎实机、网页发布。一个状态成功，不会自动证明下一个也成功。照片、测试报告和公开 release.json 各自只证明自己的范围。

## 制作流程：先把一条路走通，再把它做细

- 整理参考：分别记录造型、空间布局、材质、光照与比例参考；用户指定的识别元素优先保留。
- 建立可走的空间：以角色身高为尺度，确定入口、楼层、功能区、街道邻接和家具净空。先从街上进门，再走楼梯、转身和退出。
- 制作角色：先核对正面、侧面和背面；图生单模型使用单人清晰参考。Tripo 生成基础网格，Blender 调整尺度、材质、骨骼和权重。
- 制作建筑与家具：在 Blender 中保留可编辑源文件，脚本从不可变输入构建；通用家具可用开放素材，标志性建筑按参考单独做。
- 接入引擎：重新导入最终 GLB，检查坐标、碰撞、动画、灯光、镜头和交互。人物必须用正常控制器运动。
- 做玩法与存档：把料理、送礼、同行等变成明确状态；在流程中间切场景、刷新并恢复，不能只测最后完成态。
- 分手机与 PC 资源：手机优先入口速度、显存与持续绘制成本，PC 保留较完整的原模型和光照。
- 公开发布：正式构建、检查发布清单、推源码与网页产物，再从公网重新下载核对；保留失败记录与测试条件。

## 踩坑一：看起来有家具，房间却像水泥罐子

第一轮把“空间更宽敞”误做成了装修替换，还把青蛙缩得过小、房间放得过大。后来锁定蛙家的树干、蘑菇台阶、睡铺、小圆桌和叶子元素；另一套中式竹木、茶具风格分配给熊猫。比例用角色身高 F 做基准，逐步试调，避免凭一次俯视图持续放大。

细节少也不是简单的面数不足。地面若只有大小接近的多边格，墙壁只是单一灰色，规则年轮和重复陶罐仍会显得生硬。之后按轮廓、厘米级碎边与木节、毫米级颗粒和纤维分层处理，同时检查真实游戏镜头中的桌面、脚部和遮挡。

Blender 中好看还不够。程序材质必须成为可导出的纹理或标准 glTF 参数，再看 Compatibility 引擎中的实际颜色。提亮房间要分清主光、环境光、窗边补光、烘焙光照和材质；一味增加亮度会把外墙和人物晒成纯白。

[住宅制作与细节方法](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/household-production-method.md)

[室内光照方法](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/house-lighting-method.md)

## 踩坑二：有 Walk 动画，角色却在平移或反向摆臂

旧蛙步态一周期为 28 帧 / 30 fps，量测出的步幅匹配速度约 0.313m/s，运行时却以 2.9m/s 前进。约九倍的差距，让腿在动、身体仍像滑过去。修正依据实际支撑脚位移和碰撞后的真实速度，而不是只调整动画名字或主观加快播放。

毛利手部异常还有另一层原因：肘部按错误的轴弯向身后，40 个手指顶点误绑到了大腿；一条约 4.9mm 的原始网格边，在 Read 动作里被拉到约 595mm。柯南原有同侧手脚摆动，衣袖权重过渡也出现硬切换。修复时只改变相应手臂与权重，逐值核对已经正确的腿脚和其他轨道保持。

更隐蔽的是引擎导入：Blender 的鞋底检查通过，Godot 导入优化删掉必要关键帧后仍可能穿地。本项目比对同一时刻原 GLB 与导入后的骨骼变换，定位后调整相应角色的动画导入设置，再跑正常走、跑、停、转、撞墙。

[角色动作复现与验收](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/character-motion-workflow.md)

[柯南角色与手臂修复记录](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/conan-character-workflow.md)

## 踩坑三：路上怪阴影、门上不去、车库前塌陷

蛙家路面的条带关闭太阳阴影后消失。进一步检查发现主路 1230 个三角面、支路 192 个三角面全部朝下，双面材质掩盖了错误。修正面绕序、平滑法线，并处理薄路面的自身投影，比模糊贴图或拉高亮度有效。

博士车库建在旧河床上，门外地形约 -1.55m，车库地板约 0.04m，旧护栏还穿过新建筑。需要整体清理占地、做有厚度的地基与连续车道。第一次补齐地面后，约 4cm 的倒角接缝仍能挡住角色；因此“射线打到地面”与“真实角色走得过去”必须分别测。

毛利家也不能只做一栋孤立建筑。资料中的咖啡店、事务所、住宅楼层和相邻店铺关系，先落实在街段和入口，再处理招牌字重、窗格、夜间冷暖光。博士家则先安排环形厨房、卧室、楼梯与后车库通道，不以随机堆仪器充当布局。

[建筑与街区还原方法](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/conan-architecture-workflow.md)

[道路、同行与建筑接地证据](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/evidence/revision22/README.md)

## 踩坑四：朋友玩法做好了，刷新却把进度弄丢

旅行青蛙的方向选的是朋友日常：串门、做饭、送礼、一起出游。机制本身需要连贯的反馈，例如礼物摆在朋友家、料理进入野餐准备、同行留下共同照片。

跟随检查一开始每走几步就等熊猫，掩盖了旧导航范围和目标更新的问题。后来的连续行走、跑步、过桥检查不再中途等伙伴；该路线最大间距记录为 1.976m。这是该测试路线结果，不是全地图永不卡住的保证。

浏览器存档还暴露出“引擎关闭文件”和“IndexedDB 完成持久化”之间的间隙。料理第二步后立即刷新会丢进度。最终小状态增加同步检查点，照片仍留在 IndexedDB，并检查新旧镜像、连续刷新、恢复位置和配额失败。该玩法不依赖留言 API，但跨设备同步尚未实现。

[朋友日常与存档证据](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/evidence/frog-friends/README.md)

## 踩坑五：PC 能跑，手机却二楼打不开、摩尔纹严重

手机优化必须分开看下载、解码、内存和持续绘制。延迟加载只是换了下载时机，不能把一个巨大房间变成小房间。高 DPR 的小屏幕也可能提交很大的绘制缓冲区。

| 工程记录 | 修改前 | 修改后 / 口径 |
| --- | --- | --- |
| 哆啦首次上二楼新增下载（第 23 版） | 244,696,541 B | 11,646,005 B；按实际请求统计，不是整个材质目录 |
| 首页三张封面（第 25 版） | 7,278,558 B PNG | 384,870 B WebP；不是世界模型包大小 |
| 青蛙竖屏平均三角面 / 绘制帧（第 24 版） | 19,278,336 | 624,524；包含附加通道，桌面 Chrome 触屏模拟 |
| 柯南竖屏平均绘制调用 / 帧（第 24 版） | 3,754 | 1,241；仍有优化空间，不承诺所有手机流畅 |

实施方式是独立生成手机模型与贴图，保留 PC 输入；调整实际绘制分辨率、灯光、阴影、可见范围和后台绘制。保留 mipmap 与抗锯齿，避免用新的闪烁换速度。测试记录区分 rAF 与实际绘制帧；桌面 CPU 限速和 WebKit 触屏模拟都不能代替真实手机 GPU、内存和发热测试。

[手机端制作与验收方法](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/mobile-world-method.md)

[第 23 版二楼优化](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/evidence/mobile-revision23/README.md)

[第 24 版手机 / PC 分档](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/evidence/performance-revision24/README.md)

## 踩坑六：首页、游戏和留言不是同一个服务

首页和世界运行包在 GitHub Pages；共享留言在独立的 Sites Worker / Cloudflare D1。留言正文、非公开联系信息、浏览器里的朋友进度和照片，属于不同数据边界。域名网站也不等于云服务器。

当前来访本故障的实测结果是上游返回 403、Content-Type 为 HTML、标题为 Cloudflare 保护页，缺少 CORS 响应头。这与应用自己返回的 JSON 权限错误不同。当前没有把留言迁到其他服务器，也没有把后端不可用改写成已经修复。

首页的处理原则是：HTML 先提供品牌、世界入口与作者联系方式，不依赖 3D 引擎或留言接口。脚本加载失败或 React 崩溃时回到这个基本页面。留言发送失败明确提示尚未保存，保留输入，允许用户主动去 X 留言。整个浏览器进程崩溃或网络完全无法获取 HTML，不是页面脚本能够兜住的范围。

Git 发布也要分状态：源码推送、网页产物推送、部署工作流、公网真实文件。大资源传输曾出现 curl 56；分批上传后比较最终 Git 树、文件长度与 SHA-256，再确认公开 release.json。保留旧哈希延迟模块，照顾尚未关闭的旧页面。

[部署与数据说明](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/deployment.md)

[自有服务器迁移方案（尚未执行）](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/self-hosting-plan.md)

## 用过哪些 MCP，哪些其实是 CLI 或引擎

下面按本项目主任务调用记录与仓库来源文件整理。只列可核实的工具与用途，不把“工具栏里可用”当成“实际调用过”，也不把某个 MCP 当成整个游戏引擎。工具名随客户端版本可能变化。

| 类别 | 可核实的工具 / 调用 | 在项目中承担的工作 |
| --- | --- | --- |
| Tripo MCP | tripo_make、tripo_task_get、tripo_task_wait、tripo_balance | 图生 3D 与生成任务状态；角色来源、转换结果另由资产清单记录 |
| Sites MCP | sites_get_site、sites_save_site_version、sites_deploy_site_version、sites_get_deployment_status | 现有网站服务版本、部署与状态核对；公开门户后来沿用 GitHub Pages |
| Sites 数据诊断 MCP | sites_read_database_overview、sites_get_site_worker_logs | 核对数据表绑定和服务错误；此次未读取访客私密邮箱内容 |
| Codex app MCP | open_in_codex、read_thread、load_workspace_dependencies 等 | 打开预览、读取本项目任务上下文、定位本地依赖 |
| 浏览器 / 电脑操作工具 | mcp__cua_repl.js；另外有历史 Playwright 脚本 | 界面操作及历史实机浏览器检查；不能把当前 HTTP 检查称为截图验收 |
| 图像生成工具（非 MCP 清单冒充） | 内置 image_gen / imagegen | 概念图、角色多视角与首页手绘插画 |
| 本地 CLI 与脚本 | Blender Python、Godot、Node / TypeScript、Python、Git / GitHub CLI | 建模、蒙皮、引擎逻辑、几何与存档检查、构建和 Pages 发布 |
| 飞书 CLI | lark-cli docs 与 drive | 本篇文档的创建、结构校验与分享设置；不是声称用飞书完成了 3D 建模 |

Blender 是主要模型加工工具；本次主任务可核实记录以本地 Blender 脚本为主，未据工具可用性宣称调用 Blender MCP。不同角色的 Tripo 任务与源文件见来源清单，本文不伪造一份覆盖所有历史子任务的精确调用次数表。

[青蛙角色来源记录](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/frog-asset-source.json)

[熊猫角色来源记录](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/panda-asset-source.json)

[柯南、博士和毛利角色来源记录](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/conan-character-source.json)

## 参考资料：区分已使用、候选与官方文档

用户提供的参考图决定了角色识别和室内风格。本公开版不转载私聊或含联系邮箱的截图。网页资料列出原链接；参考图片并未因此成为开放授权模型。

[建筑资料：Charmed Life 的米花地图、毛利家与博士家布局（实际用于结构参考）](https://felicia1012.pixnet.net/blog/posts/14219272223)

已下载并接入的开放家具来自 Poly Haven：Metal Office Desk、Desk Lamp Arm 01、Vintage Radio Transceiver、Modern Wooden Cabinet、Book Encyclopedia Set 01。工作台、台灯、收发设备、矮柜和整套书籍分别按房间尺寸改造；完整作者、下载摘要和使用位置见清单。

[Poly Haven 家具、作者与接入记录](https://github.com/frankfanyiming/frank_worlds/blob/main/docs/conan-open-furniture.md)

[Poly Haven 许可页](https://polyhaven.com/license)

[Metal Office Desk 原资产](https://polyhaven.com/a/metal_office_desk)

以下是核对过但尚未接入的候选：argonius 的 Anime Classroom 与 Japanese Vending Machine。此前下载入口需要登录，未将它们写成已下载素材。用户提出的 ambientCG、Kenney、Quaternius、其他 BlendSwap 场景与 BOOTH 住宅，也不能仅凭推荐列表就算作项目已用资产。

[候选：Anime Classroom](https://blendswap.com/blend/19436)

[候选：Japanese Vending Machine](https://blendswap.com/blend/19306)

下列官方文档在整理本篇时重新核对，用来继续复现与查证技术边界；不倒推为历史每一轮都访问过的页面。

[Godot：网页导出与 Compatibility / WebGL 2](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html)

[Blender：glTF 2.0 导入导出](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html)

[Three.js：响应式尺寸与绘制缓冲区](https://threejs.org/manual/en/responsive.html)

[GitHub Pages：使用限制](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)

## 整理成五个可带走的 Skills

这些是可复用的工作方法，不是自动获得素材、服务器或第三方账号权限的插件。将需要的文件夹复制到自己的 skills 目录，检查工具是否具备，再用自己的项目输入执行。公开包只含方法文本，不含角色模型或账号密钥。

[参考图 → 可进入的场景](https://github.com/frankfanyiming/frank_worlds/blob/main/skills/reference-to-playable-world/SKILL.md)

[角色步态与蒙皮修复](https://github.com/frankfanyiming/frank_worlds/blob/main/skills/repair-character-gait/SKILL.md)

[手机网页 3D 性能预算](https://github.com/frankfanyiming/frank_worlds/blob/main/skills/budget-mobile-web-3d/SKILL.md)

[朋友互动与浏览器存档](https://github.com/frankfanyiming/frank_worlds/blob/main/skills/persist-world-interactions/SKILL.md)

[首页兜底与可靠发布](https://github.com/frankfanyiming/frank_worlds/blob/main/skills/ship-resilient-world-home/SKILL.md)

[下载五个 Skills（ZIP）](https://frankfanyiming.github.io/frank_worlds/resources/xlands-skills.zip)

## 下一次制作，我会更早做这几件事

- 先固定参考与角色尺度；先走通一栋楼，不一次铺满一座城。
- 每轮只改变能说明原因的部分；把不可变模型与重新导入的结果都留下。
- 从第一间房就设手机资源预算，真实测新增下载和持续绘制。
- 从第一项多步玩法就测试中途退出、刷新与旧存档。
- 从第一个公开链接就准备无脚本首页和联系入口，独立报告社区服务故障。
- 把失败与有效修正沉淀成短方法，而不把某个模型的参数变成所有项目的硬规则。

纯热爱分享，不涉及任何商业组织，不涉及盈利。相关 IP 未取得授权，角色及原作内容的权利归各自权利人所有；希望大家基于热爱交流和使用。开源代码与第三方素材分别遵循各自许可，本声明不构成 IP 使用授权。

[在 X 交流：@FrankFYM001](https://x.com/FrankFYM001)

抖音号：frank001。请在抖音搜索该账号；/user/self 会指向访问者自己的主页，不作为作者公开链接。

[小红书号：150015050](https://www.xiaohongshu.com/user/profile/55d96ee558944639c3ce03f1)
