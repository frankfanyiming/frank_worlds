# Tripo 角色动作的复现与验收

当前角色仍是原始 Tripo 网格；Blender 调整比例、材质、权重和骨骼动作。蛙保持 1.08 高，熊猫保持 1.35 高。真实人物外形、原 UV、颜色纹理均保留，没有用球体或程序几何替换角色。

## 复现

1. 从模型源文件包恢复 `worlds/frog/blender/character-motion-originals/frog-rig-jump.blend` 与 `panda-rig.blend`。它们是本次处理前的不可变输入，不能用处理后的输出覆盖。各自 SHA 记录在 `docs/frog-asset-source.json` 和 `docs/panda-asset-source.json`。
2. 运行 `Blender --background --python tools/build-character-motion.py`。可以追加 `-- --only frog` 或 `-- --only panda`。脚本从不可变输入开始，因此重复执行不会叠加缩放、造型或权重修改。
3. 输出为 `worlds/frog/blender/frog-rig-jump.blend`、`panda-rig.blend`、`worlds/frog/source/assets/frog.glb`、`panda.glb`、`locomotion.json`。来源记录自动由 `tools/update-character-provenance.py` 刷新。
4. `Blender --background --python tools/render-character-motion.py` 输出真实蒙皮模型的近景动作图。引擎内的实际碰撞、速度、相机与动作混合，另外用 `tools/capture-household-motion.gd` 验证；Blender 图不能替代引擎视频。

`prepare-panda.py` 的普通调用已转到上述新处理链，防止旧的 Idle/Greet 覆盖新版。只有恢复最初输入时使用 `--baseline-only`：它从真实 `panda-tripo/panda-20k-source.glb` 重建最初的规范化模型；核对来源和旧版形态后，另存为输入基线，再运行新处理链。不要将旧一次性 `work/prepare_models.py` 当作新版角色发布入口。

## 引擎契约

| 角色动作 | 周期 | 对应前进速度 | 正面方向 |
|---|---:|---:|---|
| 蛙 Walk | 20/30 秒 | 1.18 单位/秒 | Godot -Z |
| 蛙 Run | 14/30 秒 | 2.45 单位/秒 | Godot -Z |
| 熊猫 Walk | 24/30 秒 | 0.68 单位/秒 | Godot +Z |

动作不包含水平根位移。控制器按照 **实际位移速度 ÷ 基准速度** 调整播放速度；顶墙时应进入 Idle。蛙 JumpStart 包含 0.12 秒压低蓄力和随后 0.13 秒蹬地，不能刚播放就被空中状态覆盖；JumpAir 收腿，Land 双脚着地后屈膝恢复。熊猫保留 Idle/Greet，新增 Walk/Turn/Sit/Stand；Stand 是从坐姿站起的非循环动作。

## 实际踩坑

- 旧蛙动作一个周期 0.933 秒，支撑期脚后移仅 0.146 单位，对应约 0.313 单位/秒；引擎却以 2.9 单位/秒前进。仅加大抬脚无法解决滑步，必须同时匹配移动距离与动作周期。
- 不能按一个全局高度把胖大腿中间切成小腿。蛙膝盖应沿原蹲姿弯曲方向解算，完整的大腿体积由大腿骨主导，细脚踝和脚掌才交给小腿/脚骨；奶白腹部留在躯干。
- 熊猫挎包位于手臂和大腿附近。必须从肢体影响范围排除；但不能把贴图的细碎明暗直接当成手部权重，否则会出现小三角拉扯。手臂使用连续空间权重，包按空间位置排除，外侧低垂的手掌也必须排除出大腿区域。UV 接缝处重合顶点要获得相同权重；不能直接按未焊接的各自邻接面做平滑，否则会把闭合表面拉成裂缝。逐帧检查重合顶点间距可以抓住这种问题。
- 地面锁脚测量需要采样真正蒙皮后的脚底顶点，而非仅检查骨骼或 IK 目标。JSON 中逐帧记录左右脚底、前后行程与支撑期世界滑移，同时保留近景接触图检查轮廓；数字通过不意味着外形自然。
- 新输入与输出必须分开保存。直接再次处理已缩放的 rig 会让比例越改越偏；来源文档、动作列表和构建入口要一并更新，避免日后复现时回退成旧角色。

模型、Blender 动作检查、引擎实机检查与线上版本是四个状态。来源文件中的引擎验收字段由实际集成验收填写。

Blender 与引擎外观有明显差异时，先按[角色灯光隔离检查](evidence/character-motion/lighting-audit/README.md)验证资源、法线、LOD、阴影与单盏中性主光，再决定是否改模型。

JumpAir 不能靠把脚目标抬进身体来表示离地。首次收腿 .16、后续降到 .09，虽然 UV 接缝检查均为 0，侧面仍出现脚趾穿出大腿表面；这说明接缝检查只检测蒙皮裂缝，不能判断肢体自相交。最终改为脚掌前伸 .015、抬起 .003（变化 ±.002）、脚踝下倾 .035 弧度，根骨上移 .012，让脚掌保持在大腿下方；整体离地由世界物理轨迹承担。0/.2/.4 秒正面及侧面六张真实渲染已人工检查，记录在 `jumpair-visual-check.json`。`jumpair-only-change.json` 的二进制访问器对比确认本轮只改变 JumpAir，模型、权重与其他动作不变。

LightmapGI 接入后的环状自阴影要单独排查：关闭 GI/normal map 无效，而窗 Spot 的 `shadow_reverse_cull_face=true` 在本次 GL Compatibility 实机中解决，静态房间像素不变。详见[窗灯自阴影诊断](evidence/character-motion/spot-shadow-audit/README.md)；不要把新出现的渲染问题再次归咎于已验证的角色网格。
