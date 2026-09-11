# 两户室内柔光实机证据

2026-09-12 最终资源已冻结。前后图均为真实 Godot 4.7.2 Compatibility 帧，未用图片替代房间模型。角色在烘焙完成后才动态加入验证，未留下静态角色影子。

- `before-close.png`：原实时照明，硬阴影与接触层次不足。
- `after-close.png`：首次真实 GI proof，层次已改善但偏棕且架子过暗，保留为中间状态。
- `final-panda-*`：最终中性日光与黄昏，夹层下额外反弹填光。
- `final-frog-*`：最终日光与黄昏；木框、石窗楣反向法线已修，日间桌面蜡烛高亮减弱。
- `dependency-closure.json`：74 项资源依赖，无 GLB 依赖且无缺失。
- `texture-parity.json`：64 张复用贴图在隔离验证项目与原项目逐文件 SHA256 一致。
- `geometry-closure-proof.json`：原始严格哈希比较，部分失败如实保留。
- `geometry-surface-proof.json`：非零面积三角进一步比对，墙、地板保持 1 mm 范围等价。主要差异是 UV2 导入清理零面积及極细小面。
- `window-normal-fix.json`：窗木环 3 × 1,280 面、石揭口 768 面定点翻转，位置、UV、UV2 没有改变。
- `asset-manifest.json`：最终 10 个运行源资源的大小与 SHA256；EXR 源大小不等于最终网页包大小。

编辑器烘焙会在保存后出现内部 list erase /退出路径警告，但四套数据实际有 27 / 33 个静态用户，Compatibility 能显示，截图与运行检查已完成。GUI proof 运行本身没有报错。静态 GI 不能取代动态角色的全部实时接触阴影。

复现及限制见 [柔光烘焙方法](../../house-lighting-method.md)。网页发布与最终游戏路线验收由主任务单独记录。
