# 柯南与小五郎手臂修复 · 2026-09-13

状态：真实 Tripo 模型修正完成，Blender 正侧面已核对，Godot 4.7.2 Compatibility 连续实机与导入检查通过。网页发布另外验收，不能以本报告替代公网加载。

| 项目 | 结果 |
|---|---|
| 柯南正常控制器走、跑、转身、停步、顶墙与双脚 | 9/9；左右脚支撑漂移 .55–1.17 mm |
| 小五郎原场景 Idle、接近、E→Talk、位置保持 | 4/4 |
| Conan/Agasa/Kogoro 内嵌贴图、七动作及原 LeftShin 关键帧 | 7/7 |
| 非手臂动画与真实腿脚权重逐值保护 | Conan 294 条/3,184 点；Kogoro 231 条/19,525 点；未改变 |

修复事实：小五郎六个手臂关节使用原 Tripo 拟合位置，40 个误绑腿骨的手指顶点归回手部；肘部由向后反折改为向前弯曲。柯南走跑改为对侧摆臂、前向屈肘及轻微腕部姿态。两个角色的衣袖/躯干边界局部平滑，保留原几何、贴图、三角形以及所有非手臂动作。原模型备份及任务 ID 见 [来源记录](../../conan-character-source.json)。

- [范围保护数据](scope-audit.json) 验证真正腿脚的四个权重槽位、非手臂绑定、曲线及插值完全一致，且没有对侧手臂或腿部权重污染。
- [柯南实际控制器](conan-runtime-summary.json) 使用正常 `_physics_process`、实际位移速度和原输入，不手动 seek 动画或移动身体。最后障碍是明确的临时测试障碍。Walk .85 m/s、Run 1.85 m/s，基准速度/周期保持 .70/.8 s 与 1.50/.6 s。
- [小五郎原场景交谈](kogoro-runtime-check.json) 用现有 E 事件触发 Talk，NPC 原位置不变。Read 保留并检查了真实模型侧面；场景中没有书，默认改 Idle。不将保留的 Kogoro Walk/Run 声称为此次完整步态重建。
- [真实导入](import-check.json) 包括保留原 LeftShin .4 s 关键帧，关闭优化/压缩；Kogoro 4096²、Conan/Agasa 2048² 内嵌颜色贴图都可读取。

实际模型图：[柯南正面](conan-blender-run-front.png)、[柯南侧面](conan-blender-run-side.png)、[小五郎保留 Read 侧面](kogoro-blender-read-side.png)、[小五郎 Talk](kogoro-blender-talk-quarter.png)。实际引擎图：[柯南迈步](conan-engine-walk.png)、[柯南跑步](conan-engine-run.png)、[小五郎站姿](kogoro-engine-idle.png)、[小五郎交谈](kogoro-engine-talk.png)。这些都是模型/引擎渲染，未使用概念图代替验收。

连续录像保存在工作区 `outputs/角色手臂修复/柯南实机/` 与 `小五郎连续交付/`，由 `capture-conan-motion-v2.gd` 和 `capture-kogoro-arms.gd` 生成。1440×900、60 fps；MP4 从真实 AVI 逐帧编码，只去除最初 45 个准备帧，其余帧序与时间不变。首次小五郎相机位于窗外或墙内的片段不是交付证据，最终相机在室内且双手可见。

复现：按 [角色流程](../../conan-character-workflow.md) 恢复不可变原始 GLB，执行 `repair-conan-arms.py`、`test-conan-arm-scope.py`，真实 GLB 正侧面渲染通过后执行 `stage-conan-arm-repair.py`。它必须在旧 `stage-conan-characters.py` 之后，避免基础模型覆盖修复。Godot export 的共享导入配置包含可选 Kogoro，不能依赖当前电脑缓存。源与网页运行资产均同步，本步骤不直接发布。

后台原生窗口有时不再发出 frame_post_draw，但逻辑帧仍继续运行，等待截图会让 AVI 不断增长。小五郎最终捕捉使用 `--disable-render-loop`，在每个正常 process_frame 后显式 `RenderingServer.force_draw(false)` 一次；动作仍由原场景正常推进，不 seek、不手动设置骨骼。这种模式 MovieMaker 总结里的自动绘制帧数会显示 0，应校验实际 AVI 帧块数量、编码视频时长及连续画面，不能拿自动绘制计数判断录像为空。
