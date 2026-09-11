# 窗灯自阴影圆环诊断

隔离项目 `outputs/panda-lighting-proof`，Godot 4.7.2 GL Compatibility / Apple M5 Pro，沿用交付的 LightmapGI 场景。只修改独立实例的属性，不保存 `.scn`、`.glb` 或生产 `world.gd`。

确认圆环来自窗灯实时自阴影：关闭角色 GI 仍有圆环，关闭 normal map 也仍有；仅关闭窗 Spot 的实时 shadow，或仅关闭蛙的投影，圆环消失。触发截图中主要是 `Window_FrogWindow1`。加大 normal bias 到 4 仍有残留；shadow bias 到 .25 可以清除这个机位，但不作为最终建议。

最小修正是在实例化两房 `BakedLights` 后，对 `SpotLight3D` 设置 `shadow_reverse_cull_face = true`。保留 `shadow_enabled = true`、`shadow_bias = .025`、`shadow_normal_bias = .45`，角色保持 `GI_MODE_DYNAMIC`；无需改角色资源或重新烘焙。

`15-spot-reverse-cull.png` 恢复平滑轮廓，静态房间区域（x=280…1200，全高）对比原图像素差为 0。另检查蛙站立、转向走步、背向空中以及熊猫走姿，没有原先等高线状圆环。只关 GI 会改变角色亮度，所以“不是 GI 根因”不表示 GI 完全没有作用。`pixel-comparison.json` 和 `properties.json` 留存具体属性和差异。

尝试单独加入 .23 能量的 Directional 实时影子会叠加房间直射和新条纹，因此本轮不采用。保留原窗灯与真实阴影的反向剔除修正影响更小。

本诊断证明的是本机引擎中这些姿态和位置的渲染；网页 Compatibility 导出仍应由集成录像确认。隔离项目青蛙 SHA `8b791b23bcf51c7d8800523c0b03c9cc35814e15a664691ab1ee4e8a9d8d2886` 是上一版 JumpAir，最新生产模型 SHA `d02f3bedea63cfd65f3406660b2f950377439fa58c60ce9937ebb649e6564f68` 只修改 JumpAir 动作，材质、网格和权重相同。此处动作截图用于阴影 A/B，不代表最终 JumpAir 验收。

复现：用 Godot `--path outputs/panda-lighting-proof --rendering-method gl_compatibility --script audit_frog_dynamic.gd` 与 `audit_actor_shadow_cull.gd`；脚本副本保存在本目录。所有变更均为进程内测试，无资源保存。
