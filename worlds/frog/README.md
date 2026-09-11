# 旅行蛙

日版自然旅行世界。角色由 Tripo 生成，庭院、树屋、森林与道具由 Blender 制作。角色有 16 根骨骼；左右大腿、小腿、脚掌分别绑定，包含 Idle、Walk、Sit、JumpStart、JumpAir、Land 动作。

`source` 是 Godot 4.7.2 项目。Space 跳跃，WASD 行走，Shift 奔跑，E 互动，P 拍照。原创新作森林背景音随声音开关播放。

走过门槛后进入封闭的石屋室内：Blender 灰色石墙、窗框与石拱顶围合两层空间，室外地形与树木停止显示；出门恢复庭院。室内全景和跟随视角限制在屋内，上夹层时调整镜头避开树干，C 仍可切换蛙眼视角。滚轮不会把室内镜头拉到屋外。屋内采用中性日光，木材用于楼板、楼梯与家具，石材保留灰色。

`tools/build-frog-home.py` 用 Blender 重建室内围合模型，保留可编辑 `.blend` 并将网页 GLB 合为 11 个网格。`tools/build-frog-stone-shell.py` 保留原有岩屋造型、门窗开口，生成灰色石材外壳。`tools/test-frog-home.gd` 通过真实角色控制器检查门口切换、楼梯、跳跃、墙面碰撞与出门恢复，并保存实机画面。用 Godot 的 `--script` 参数传入此脚本的绝对路径，`--` 后可指定报告输出目录。

完整资产通过根目录 `tools/fetch-native-assets.py` 下载，并核验 SHA-256 后解压。资产包链接见 `asset-manifest.json`。大型资产按仓库约定放在 GitHub Releases；源代码与版本清单保存在 Git。

浏览器入口：[小世界](https://frankfanyiming.github.io/frank_worlds/)

完整源资产包已整理，但公开上传仍等待仓库所有者单独确认。网页运行包与可读源码独立发布；资产下载脚本会明确提示当前状态。
