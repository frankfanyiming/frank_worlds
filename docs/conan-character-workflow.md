# 柯南与阿笠博士：形象、骨骼与步态

用户新给的最后两张柯南手办图、第五张博士动画形象为角色主参考。旧人物虽然有 17 根骨骼和动作名，外形仍偏离：柯南发型杂乱、脸偏旧式，步态压低髋部且高速快放；博士采用通用正弦摆腿，没有足底支撑约束。

本轮重新使用 imagegen 生成可建模的正面 A 姿态及同人物三视图，再以单人正面图驱动 Tripo v3.1。多视图用于核对身份和轮廓，不能把三个人物并列图直接作为单模型生成输入。真实任务 ID、输入 SHA、旧版备份和运行资产 SHA 见 [角色来源](conan-character-source.json)。参考图与原始 FBX 位于模型源包中的 `worlds/conan/blender/character-v2/`，公开证据图是重新导入最终 GLB 的 Blender 实际渲染。

## 复现步骤

1. 从模型源包恢复 `worlds/conan/blender/character-v2/tripo-conan`、`tripo-agasa` 的不可变 FBX 及 `reference`，旧 runtime GLB 保留在 `originals`。
2. 运行 `Blender --background --python tools/build-conan-character-motion.py`，或加 `-- --only conan` / `-- --only agasa`。脚本始终从原始 FBX 开始，不从已经绑骨的模型再次缩放。输出同目录角色 `.blend`、`.glb` 与足底采样报告。
3. 使用 `tools/inspect-conan-characters.py -- <final.glb> <evidence-dir> --contacts` 重新导入导出的 GLB，检查正面、侧面、四分之一步态、跑步、招手及交谈。这里检查的是实际网格，不是概念图。
4. 通过视觉检查后运行 `python3 tools/stage-conan-characters.py`，将两位角色及 `character-motion.json` 写入 Conan `source/assets` 和 `web-project/assets`。`python3 tools/export-native-web.py conan <output> --godot <Godot>` 会先 import，再调用共享 `configure_conan_import` 设置嵌入纹理 2、关闭 AnimationPlayer 的优化和压缩；只有参数改变时才再次 import。因此从没有 `.import` 的运行源包开始也可复现，不依赖当前电脑的缓存。独立源项目可在第一次 import 后运行 `python3 tools/configure_conan_import.py <project> --godot <Godot>`，若返回 `changed=true` 则再 import。
5. 引擎集成必须使用碰撞后的实际位移速度控制动画倍率，并单独验证院外、室内、顶墙和手机操作。源码、引擎实机与网页发布分别记录状态。

## 动作契约

| 角色 | 高度 | 朝向 | Walk 周期 / 速度 | Run 周期 / 速度 |
|---|---:|---|---|---|
| 柯南 | 1.05 m | Godot +Z | 0.8 s / 0.70 m/s | 0.6 s / 1.50 m/s |
| 阿笠博士 | 1.56 m | Godot +Z | 1.2 s / 0.58 m/s | 28/30 s / 1.05 m/s |

保留 `Idle / Walk / Run / Wave / Talk / Read / Sit`。博士当前主要使用 Idle/Talk，其慢步资产可用于后续漫步。每个角色 20 根骨骼，包括颈部、锁骨与双腿，真实最大权重数为 2。所有动作不包含水平根位移，Web 控制器读取 `assets/character-motion.json` 的速度基准。

## 本轮实际发现与修正

- 旧柯南 Walk 1 秒周期只对应 0.3667 m/s，运行以 0.85 m/s 移动时需要约 2.32 倍快放，且整个周期持续压低髋部 0.046 m，容易呈现屈膝碎步。新周期与速度接近实际儿童步频，髋部在中支撑恢复高度，仅在跨步需要时适当下降。
- 逐帧骨骼目标正确仍不等于足底轨迹正确。首次 Bezier 插值在支撑边缘产生约 16 mm 滑移；改成逐帧 LINEAR 后，97 个含子帧采样中，柯南步行最大支撑漂移约 1.20 mm，跑步约 1.40 mm。博士步行约 0.72 mm。测量对象是蒙皮后的鞋底顶点，并叠加角色前进位移，不能只测骨骼位置。
- 鞋体保持一个脚骨的刚性权重，袜子向小腿连续过渡；手指由手骨控制，衣袖在腕肘处连续过渡。博士白大褂与裤子在同一高度，不能按一个全局高度截断，否则大褂会被拉进腿里。根据原纹理与空间分区识别外套，再统一重合 UV 接缝的权重。
- 柯南黑发与蓝衣使用局部材质因子校准，保留原生成 UV 与纹理。Blender 5.2 的 glTF 导出在共享纹理上忽略了 MixRGB 乘法，导致 Blender 看起来正确而引擎回退灰发。构建脚本导出后将相同系数写入标准 `baseColorFactor`，并重新导入最终 GLB 检查，避免仅凭 `.blend` 截图宣布通过。
- 本轮造型重建来自新的 Tripo 网格，不是对旧角色仅调灯光，也没有使用几何小人替代 Tripo。用户参考、生成提案、真实模型和上线状态必须清楚区分。

## 引擎导入后的关键帧回归

第一次正常控制器实机里，停步、转向与撞墙五项通过，但真实鞋底采样暴露出每个 Walk 周期左脚在约 .4 秒下陷 23 mm、支撑滑移 38.7 mm，右脚与 Run 没有同样问题。原始 GLB 中 LeftShin 在 .400 秒的四元数 x 为 .271376；导入后被优化为 .172217，必要关键帧被删，而相关脚骨补偿仍保留。关闭该角色 AnimationPlayer 的 `optimizer/enabled` 后，同一时间恢复 .271376，足底和脚轴同步恢复。这个设置属于节点高级导入选项，并非单个动画选项；官方实现位置见 [Godot 场景导入器](https://github.com/godotengine/godot/blob/master/editor/import/3d/resource_importer_scene.cpp)。

修正后的正常物理控制器验收中，Walk 左右脚支撑漂移约 1.07 / 1.17 mm，Run 约 .55 / .83 mm；实际步速 .85 / 1.85 m/s，所有移动采样着地率 100%，顶住临时可见测试障碍后实际速度为 0 并播放 Idle。原始角色 GLB 字节未变。证据在 [导入前后对照](evidence/conan-character/optimizer-regression.json)。

`tools/capture-conan-motion-v2.gd` 使用实际 world.gd、CharacterBody3D 和原控制器，`testing=false`；通过 audit_input 和正常 Run 输入驱动，不调用动画 seek、advance，也不手动移动身体。最后的障碍为脚本临时创建并明确标注的回归测试用障碍，不冒充生产街区建筑。`tools/analyze-conan-motion-v2.py` 对足底、支撑滑移、停步和碰撞给出九项结果。引擎逐帧证据不能只拿先前 Blender 采样替代。

纯净项目回归只复制两位角色的原始 GLB，从不存在 `.godot` 和 `.import` 开始。首次配置返回 `changed=true`，重新导入后再执行返回 `false`；两角色都保留 2048² 嵌入贴图和七个动作，LeftShin 在 .4 秒的四元数 x 为 .27137643。见 [新项目导入验收](evidence/conan-character/fresh-import-check.json)。

录像命令必须先创建输出目录，并保持项目的视口尺寸。Godot MovieMaker 在脚本 `_initialize` 之前固定 AVI 尺寸；脚本中途改变 `root.size` 会产生尺寸不同的 JPEG 帧。最终捕捉脚本不再更改视口，使用项目的 1440×900。当前 macOS 的 avconvert 仍无法读取这份正确尺寸的 Godot MJPEG AVI，因此使用 `tools/encode-godot-avi.swift` 逐帧解码原 JPEG、交给系统 AVAssetWriter 编成 H.264。保留原始 AVI，展示 MP4 仅去掉最初 45 个摄像机准备帧（.75 秒），后续帧序和 60 fps 时间不变，不能把转换问题误判为角色动画错误。

Blender 逐帧数据见 `docs/evidence/conan-character/conan/motion-check.json` 与 `agasa/motion-check.json`，最终模型图见 `conan-final/` 与 `agasa-final/`。实际引擎证据单独归档在 `runtime/`，来源文件分别记录已验收范围与网页状态，博士的资产 Walk 检查不冒充生产 NPC 走动。
