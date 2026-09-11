# 引擎角色硬边与偏黄：隔离检查

本次只修改独立验收进程中的对象，未修改 `world.gd`、GLB、导入配置或生产材质。检查使用 Godot 4.7.2、GL Compatibility、Apple M5 Pro，与当前实机一致。

结论：不需要为了这块硬边重做 Tripo 网格。贴图、平滑法线、骨骼和新版材质已正确导入；主要差异来自房间多盏窗光的衰减和整体光色。动态角色应与正在制作的静态烘焙光照一起校准。

## 有用的 A/B

固定相机、角色位置和动作时间后，只改检查项：

| 图 | 改动 | 观察 |
|---|---|---|
| [01 当前](01-current.png) | 当前运行设置 | 蛙背有强烈明暗分界，黄绿偏亮。 |
| [02 不接收阴影](02-no-receive-shadows.png) | 只禁用角色接收阴影 | 角色更亮，硬光分界仍在；不能用关阴影代替修光。 |
| [03 关闭法线贴图](03-no-normal-map.png) | 只关闭 normal map | 大块分界几乎不变，法线贴图不是主因。 |
| [05 无光照基础色](05-unlit-albedo.png) | 角色 unshaded | 基础色本身是较饱和的黄绿色；当前色调输出也不同于 Blender 的 AgX 灯光环境。 |
| [06 降低阴影法线偏移](06-smaller-normal-shadow-bias.png) | normal bias .45→.1、bias .025→.02 | 反而产生条纹 acne，不建议照此调整。 |
| [08 禁用 LOD](08-lod-disabled.png) | viewport mesh LOD threshold=0 | 大块分界不变；不是网格被减成少量大三角。 |
| [09 几何法线](09-geometric-normal-debug.png) | 直接显示几何 NORMAL | 头、背、大腿法线连续平滑。 |
| [10 单盏白色主光](10-one-white-light.png) | 关室内附加灯，白 Directional .65 +白 ambient .35，无阴影 | 圆润过渡恢复，可作为动态角色柔光校准目标。此图是诊断基准，不是全屋上线照明方案。 |
| [16 只扩大光锥](16-only-wider-cone-original-energy.png) | 42°→68°，仍 .35 attenuation/.65 energy | 硬块仍在，条纹更明显；扩大角度不是必要修复。 |
| [17 只柔化衰减](17-only-softer-attenuation-original-energy.png) | attenuation .35→1.3，仍42°/.65 energy | 硬光分界明显减弱，是本轮更小、更有依据的参数调整。 |

建议先保留42°，把窗光 attenuation 调到1.3，再结合烘焙结果单独平衡动态角色亮度和中性填光。不要一次同时大幅改变光锥、灯强、色调和材质，否则无法判断哪一步改善了效果。单纯将色调切到 Linear 或 AgX，在本场景里首先带来变暗，并没有复现 Blender 观感，因此不作为独立修复建议。

## 导入证据

- [Godot 实际材质记录](../godot-materials.json)：蛙当前使用 GLB 内嵌 `PortableCompressedTexture2D`；法线强度为新版 .35，albedo tint 为白色，逐像素着色，49,148个导入顶点、43,932个不同平滑法线、16骨绑定，未生成 shadow mesh。
- 熊猫实际 normal 已关闭，roughness=.86、16骨均为新版；原生GLB三角面22,777，未被旧渲染模型替换。
- [逐像素来源哈希](texture-hash-comparison.json)：蛙三张、熊猫两张 GLB 内嵌图片与 assets 下已提取图片的解码像素 SHA256 全部一致。不存在旧提取贴图覆盖新纹理。
- 原 Tripo metallic/roughness 打包图仍保留：蛙蓝色金属通道平均约10.38/255、熊猫约40.37/255；Godot 的 metallic=1 是乘图系数，不代表全身纯金属。本次不改此素材因素，先校准灯光。

## 复现与边界

`tools/audit-character-materials.gd` 读取引擎实际加载的材质、法线与骨骼信息。

`tools/audit-character-lighting.gd` 创建带独立保存路径的验收场景，在内存中做 A/B，输出到命令行传入的目录；运行结束即丢弃修改。固定近景用来定位差异，不能替代正常探索过程中相机、移动与跨房间的验收。

经验：Blender 平滑而引擎出现大块硬边时，先验证真实加载资源和中性单光结果。仅凭截图反复减面、加细分、重做角色或增大阴影偏移，会把渲染问题误判成模型问题。
