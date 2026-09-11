# 两户住宅的真实柔光烘焙

状态：2026-09-12，真实 Godot Compatibility 渲染验证通过；网页发布状态由主任务另行记录。模型、材质、相机和角色都是真实 3D。烘焙没有包含角色。

## 交付与接入

- `res://assets/house-lighting/frog-room.scn`：根 `FrogRoom`，其下保留 `home-enclosure`、`home-furnishings`，与原 GLB 相同的模型节点名称和全局变换。
- `res://assets/house-lighting/panda-room.scn`：根 `PandaRoom`，其下 `panda-home`；原点不变，可放在现有 `PandaHome` 的 `(100,0,0)` 父变换下。
- 每屋根下另有 `BakedLights`、`LightmapGI`，没有相机、环境、碰撞包装或动态角色。
- `LightmapGI` 的 `day_data` / `dusk_data` metadata 是完整资源路径；切换 `light_data` 即可改变时段。LightmapGI 没有可调的整体 energy 属性，所以没有伪造此属性。
- 每盏灯带 `day_energy` / `dusk_energy` 与 `day_color` / `dusk_color`。静态窗光日间 `fff6e7`、黄昏 `bfd0e2`；反弹柔光 `edf2ef`；灯笼 `ffd49a`。
- 旧室内实时灯应在使用烘焙房间时关闭，避免重复照明。BakedLights 的静态灯保留正常运行能量，用于动态角色。环境 ambient 建议日间 0.10、黄昏 0.07，保持中性。
- `UnderLoftBounce` 是额外烘焙反弹填光，运行 energy 为 0；其 `bake_day_energy` / `bake_dusk_energy` 只供重新烘焙时使用。
- 每屋 SCN 已将 UV2 mesh / material 保存为内部资源，纹理复用原 assets 路径；无旧 GLB 依赖。旧 GLB 可从 Web 包排除，原文件保留供编辑和回退。

## 证据

[证据目录](evidence/house-lighting/) 中 `runtime-proof.json` 记录日间/黄昏各一遍真实 Compatibility 渲染；角色为动态实例，baked users 只包括 27 个熊猫屋静态 mesh、33 个蛙屋静态 mesh。`dependency-closure.json` 覆盖两个 SCN 及四个 lmbake 的资源闭包，64 张纹理逐文件 SHA256 与原 source assets 一致，见 `texture-parity.json`。

`geometry-closure-proof.json` 保留严格三角哈希比较的失败结果，不能称为完全几何相同。UV2 导入会拆顶点并清理零面积/极细三角；`geometry-surface-proof.json` 进一步逐三角比较坐标，墙和地板在 1 mm 范围等价，节点变换不变。极细面差异集中编织、罐口及少数天花面，未移动家具、通道或围墙。不能用 vertex 数量变化推断房间尺寸变了。

## 实际踩坑与有效修正

1. **网页能显示 LightmapGI，但不能烘焙。** 本次在 Godot 4.7.2 / Apple M5 Pro / Metal Mobile 编辑器烘焙，Compatibility 实际显示验证。不要在浏览器内调用烘焙。官方说明：[Using LightmapGI](https://docs.godotengine.org/en/stable/tutorials/3d/global_illumination/using_lightmap_gi.html)。
2. **Godot 的 bake 方法没有绑定到 GDScript。** `has_method("bake")` 为 false；原生编辑器 LightmapGI 工具条按钮能够执行。隔离项目 EditorPlugin 自动选中 LightmapGI 并触发真实 Bake Lightmaps 按钮，四次烘焙分别约 5–7 秒。不是伪造结果文件。[原生编辑器实现](https://raw.githubusercontent.com/godotengine/godot/4.7-stable/editor/scene/3d/lightmap_gi_editor_plugin.cpp)。
3. **Compatibility 不支持本机生成的 BPTC HDR 数组贴图。** 初次出现黑图/texture null 警告。将 EXR 导入 `compress/mode=0`、`compress/hdr_compression=0`，并删除隔离项目对应旧导入缓存、重新 import 后正确显示。仅改 `.import` 配置却继续用旧缓存不够。
4. **烘焙与运行能量不能混用。** 本机非物理单位设置下，原运行能量烘焙过暗，实际对照校准使用 12 倍静态 bake energy，烘焙完立即恢复原运行值。这个系数是本次 Godot 配置的实测校准，不是所有项目通用常量；不能拿 12 倍灯光照动态角色。
5. **保留 imported scene 路径又重设子节点 owner 会复制几何。** 最初 PackedScene 同时保存了原 GLB 实例和显式子 mesh，导致重影。正确做法清空导入根 `scene_file_path`，统一保存一次子节点，内部 mesh/material 清空 GLB 子资源路径。
6. **跨项目 UID 不能仅复制。** scratch 保存的外部纹理 UID 不属于 source 项目，虽可 fallback 路径，但会产生大量警告。复制后在 source 项目重新保存两个 SCN，再次加载无 invalid UID。纹理内容另做 SHA256，比“文件存在”更可靠。
7. **全静态烘焙有动态阴影限制。** 角色没有参与 bake，走开不留固定人影；静态 baked 接收面不会自动得到所有动态角色实时投影。运行角色表面可接收静态灯和 GI probe，必要的接触影由游戏层独立处理。不能宣称烘焙后等同完整实时 GI。
8. **应保存失败证据。** 暗图、重复几何、HDR 兼容和三角哈希不等价都保留了原因；后续应对照实机截图，而非只看 baker 返回 users 数量。

重建脚本在 `tools/house-lighting/`；需要使用隔离项目复制原 GLB、将导入模式设为 Static Lightmaps / texel size 0.1，并保留原模型源文件。不要把验证场景的环境、相机或角色装进最终静态 SCN。

## 复现顺序

1. 用 `tools/house-lighting/prepare_project.py --source worlds/frog/source --output <新的隔离目录>` 创建副本。必须是新目录，避免旧缓存与资源重复。
2. 用 Godot `--headless --editor --path <隔离目录> --import` 导入 UV2，再 `--headless --path <隔离目录> --script build_houses.gd` 生成两屋场景。
3. 对本轮保留的旧 frog GLB，运行 `fix_frog_window_normals.gd`。该修正仅改变三只木窗环及石窗楣的绕序、NORMAL 和 tangent.w，位置/UV/UV2 不变，每木环必须恰好选中 1,280 面才保存；石窗楣独立节点须恰好 768 面；有 metadata 防止重复翻转，同时以本次旧 `home-enclosure.glb` SHA256 `9bce017c78a3ce5b72b2a88b83c2e8cfc831d25ace50f1fc9a4ad823b34fdc3b` 做门禁：源文件哈希不同则明确跳过，绝不按三角数量盲翻。源建模脚本已同步正确绕序，未来从修正后源脚本重新导出的 GLB **不要再运行此旧资产补丁**。
4. 启用隔离项目 `addons/bake_probe/plugin.cfg`，以 Metal Mobile 编辑器打开，插件顺序执行两屋 day/dusk 原生烘焙。自动恢复正常实时灯能量，保存压缩 `.scn`。插件只对选中的静态房屋工作，不加载任何角色。
5. 运行 `prepare_compatibility.py <隔离目录>`，随后再次 `--headless --editor --import`，确认四张 EXR 已重新导入为无 HDR 压缩。
6. 用真实 Compatibility 窗口运行 `snapshot_houses.gd`，生成日间/黄昏含动态角色的截图。运行 `dependencies.gd` 输出资源闭包。
7. 仅复制 `assets/house-lighting` 下 SCN、EXR、EXR.import、LMBake 到 source；不要复制 `.godot` 或整个隔离 assets。在 source 执行 `resave_source.gd`，把纹理外部 UID 重存为真实项目 UID；再加载一次确认无 UID warning。
8. 源 GLB、纹理哈希、静态模型节点/变换、围护几何与运行光照分别核对，再交游戏层验收发布。

最终蛙屋额外修正：源圆窗木环原始法线向管内，真实 GI 暴露为黑圈；仅运行版修正木环 3,840 个三角、石窗楣 768 个三角及对应法线，源 GLB/.blend 保留。日间桌面蜡烛的 bake energy 降为 0.09，黄昏仍为 0.34；运行能量不乘烘焙系数。

## 最后网页发布：不能用模型来源词做排除通配

实际网页报 `panda.glb` 两个外部贴图 `invalid UID` / `No loader found`。角色 GLB 与 `.import` 本身正确，`_subresources={}` 无旧映射；原因是 Web `exclude_filter` 的 `assets/*_tripo*` 把当前模型引用的 BaseColor 和 Metallic/Roughness 提取图一起排除了。Native 能读取 assets，所以 Native 验收不能覆盖此类打包缺失。

修正只删除这一条过宽排除；角色 GLB、导入方式和房间 bake 不变。蛙 GLB 当前为内嵌 PortableCompressedTexture2D，没有外部图依赖；熊猫当前恰有两张外部图。`character-export-dependencies.json` 记录递归依赖与排除匹配，均不再被过滤。进一步用真实 Web 导出的隔离 PCK 加载两角色，读到蛙 4096² 内嵌图、熊猫 2048² BaseColor 与 1024² Metallic/Roughness，记录在 `packed-character-textures.json`。模型 SHA256 保持 `b7ee5da7c6010cc45a5e02736bedac637b06def09cc4d31f4e01d3a63cf05c20`（panda.glb）。

可用 `tools/test-packed-character-textures.gd` 配合 Godot `--headless --main-pack <导出的PCK> --script <检查脚本绝对路径> -- <结果JSON绝对路径>` 复验。必须同时断言场景加载、必需贴图槽存在与贴图尺寸大于零；仅“没有 missing 文件”或“原项目能打开”都不够。原模型带 Tripo 名称不是多余贴图的证据，今后仅在依赖闭包证明无引用后按具体资源路径排除。
