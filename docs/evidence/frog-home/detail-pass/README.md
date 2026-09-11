# 蛙家细化：同一真实模型的四视角

2026-09-12。下列图片是 Blender 5.2.1 LTS 对同一闭合房间模型的实际渲染，使用现有 Tripo 蛙模型作比例参照。**不是生成概念图，不是 Godot 截图，也不说明网页已发布。**

| 图片 | 用途 |
|---|---|
| [01-main.png](01-main.png) | 复核树干蘑菇梯、蓝睡阁、桌毯、厨房与储物的整屋关系 |
| [02-loft.png](02-loft.png) | 夹层、蓝被、木构与厚圆窗近看 |
| [03-entry.png](03-entry.png) | 入口方向检查同一模型的遮挡与通道 |
| [04-details.png](04-details.png) | 颗粒石壁、碎边石板、年轮、叶脉、陶罐、编篮与竹梯细节 |

原生场景为 `worlds/frog/blender/frog-home-review.blend`；分户源文件是同目录的 `frog-home-enclosure.blend` 和 `frog-home-furnishings.blend`。可用仓库脚本先运行 `tools/build-frog-home.py`，再运行 `tools/build-frog-furnishings.py` 复现。源模型保留各物体，运行资产按材料合并。法线、颗粒、粗糙度和颜色实际嵌入 GLB，不依赖无法导出的 Blender 程序节点。

冻结导出时围护 6,682,540 字节、11 网格、37,894 三角；家具 17,610,180 字节、23 网格、281,190 三角。合计约 24.29 MB，比细化前增加约 8.45 MB。不含未改动的蛙角色和其他世界。为控制体积，原生 PNG 色贴图在运行 GLB 中改为 JPEG；法线、粗糙度保持 PNG，因此本组 Blender PNG 与运行贴图存在正常有损压缩差异。

房间、蛙和主要家具比例没有放大；入口、出口、地板、夹层、楼梯路线与宽度、原 QA 路线、原家具碰撞记录逐项对比未变。岩面浅起伏并入真实墙碰撞；新增一处背后竹梯薄碰撞盒。真实控制器路线与引擎照明由主任务另行验收，本目录不代替它们。

图片、脚本、模型、布局和角色 SHA-256 见 [manifest.json](manifest.json)。方法与本次出现的周期纹理、年轮浮线、叶毯厚度问题见 [住宅制作方法](../../../household-production-method.md)。
