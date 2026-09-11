# 旅行蛙

2026-09-12 当前实现说明：两户模型与动作已进入 Godot 调试，本轮细化的最终实机视觉验收、网页发布尚需对应证据确认；下面描述本地功能与资产，不作为线上版本承诺。

日版自然旅行世界。青蛙、熊猫由 Tripo 生成，庭院、石屋、森林与道具由 Blender 制作。两位角色分别使用 16 根骨骼；左右大腿、小腿、脚掌单独绑定。蛙包含 Idle、Walk、Run、Sit、JumpStart、JumpAir、Land，熊猫包含站立、迈步、转向、坐下与招呼动作。具体周期与基准速度见 `source/assets/locomotion.json`。

`source` 是 Godot 4.7.2 项目。Space 跳跃，WASD 行走，Shift 奔跑，E 互动，P 拍照。原创新作森林背景音随声音开关播放。

走过门槛进入青蛙家：左侧树干与蘑菇梯、后侧蓝色睡铺、小圆桌、叶毯、陶罐架与双灶延续原作装修。灰米色天然岩壁围合室内，地面是碎边石板。地板、树皮、年轮、织物和陶釉分别制作实际几何与可导出的表面贴图。室外地形与树木在屋内停止显示，出门恢复庭院。

沿营地旁的新小径向南，按 E 拜访熊猫的竹木茶室。这里有独立的石屋、右侧楼梯、竹床、茶具、编织坐垫和花格圆窗；可喝茶、上楼，熊猫会在桌旁走动。两个住宅使用独立室内碰撞，不与室外山坡重叠。

进门默认较低的近距离跟随视角，右键环视、滚轮调节距离，C 切换蛙眼和全景；相机检测墙体与家具遮挡。移动速度与步幅匹配，播放速度跟随实际移动，起跳保留蓄力与蹬地阶段。

根目录的 `tools/build-frog-home.py`、`tools/build-frog-furnishings.py` 和 `tools/build-panda-home.py` 保留可编辑 Blender 场景并导出运行 GLB。源文件位于本目录 `blender/`：`frog-home-enclosure.blend`、`frog-home-furnishings.blend`、`frog-home-review.blend` 与 `panda-home.blend`。蛙家细化包含浅浮雕岩面、碎边倒角石板、细树皮与年轮、叶毯缝线、不同轮廓陶罐、编篮和厚圆窗；[Blender 四视角](../../docs/evidence/frog-home/detail-pass/README.md) 与 [熊猫茶屋细节](../../docs/evidence/panda-home/details-02/README.md) 保留模型证据。`tools/build-panda-trail.py` 将庭院小径贴合原地形，`tools/build-character-motion.py` 在真实 Tripo 网格上修整轮廓、权重与动作。

当前两户路线验收用 `tools/test-frog-households.gd`：从出生点真实走到门口，检查上下楼、跳跃、墙体、相机、熊猫碰撞/步行、翻译和两次出门。用 Godot 的 `--script` 参数传入脚本绝对路径，`--` 后指定独立报告目录。`tools/capture-household-motion.gd` 另用于近景实机录像；它会安排初始镜头与站位，不冒充完整步行路线验证。

完整源资产的下载入口为根目录 `tools/fetch-native-assets.py`，公开后按清单核验 SHA-256 再解压。当前 `asset-manifest.json` 仍是 2026-09-11 归档条目，标记 `pending-publication`；下载脚本会提示尚未公开，不能据此取得本轮完整可编辑资产。大型源资产与网页运行包是不同发布对象。

浏览器入口：[小世界](https://frankfanyiming.github.io/frank_worlds/)

网页运行包、可读源码与完整源资产分别记录发布状态。公开清单及版本摘要更新完成前，不将本地模型完成视为本轮线上更新完成。
