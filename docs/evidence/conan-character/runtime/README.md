# 柯南与博士：实际引擎验证

Godot 4.7.2 Compatibility，最终白天光照：太阳 .42、环境 .40、窗光倍率 .65（博士家 .5525）。本目录图片均为生产场景的实际引擎截图；模型来源和 SHA 见 `../../../conan-character-source.json`。

- `conan-motion-v2-summary.json`：正常 CharacterBody3D 控制器走、跑、转身、停步、碰撞，以及蒙皮鞋底的九项验证。Walk 实速 .85 m/s、Run 1.85 m/s；左右支撑漂移分别约 1.07/1.17 mm、.55/.83 mm。撞上可见的临时测试障碍后，实际速度归零且切回 Idle。
- `agasa-runtime-check.json`：生产博士 NPC 原位 Idle、接近后 E 交谈、实际播放 Talk、位置保持四项验证。博士的 Walk/Run 目前属于 Blender 资产验证，本轮没有把它当作生产 NPC 行走验收。
- `capture-metadata.json`：实际场景源码与原始录像 SHA、尺寸、时间、展示视频编码范围和局限。

`conan-motion-v2.json.gz` 保存可复算的原始逐帧蒙皮采样（解压后交给分析脚本）。完整原始 JSON、649 帧 AVI 和可播放 MP4 位于工作区 `outputs/柯南与移动端升级/角色正常物理验收/最终/`。大文件未放入 Git；本目录保留精简报告和五张无遮挡实机图。这里记录原生引擎结果，公开网页的加载验收由发布环节单独记录。
