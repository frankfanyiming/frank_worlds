# 熊猫邻居与竹木石屋：真实模型证据

2026-09-12。依据用户认可的第二轮概念实施；此目录图片均来自实际 Blender 模型渲染，非 imagegen 概念图。**本层图片与 manifest 为初版存档；最新房屋细节与运行文件清单见 [details-02](details-02/README.md)。**

- `panda-tripo-rig-blender.png`：真实 Tripo 熊猫，归一化身高 1.35，Blender 16 骨骼、Idle 与 Greet 动作。原始 PBR 贴图保留。
- `panda-room-main-blender.png`、`panda-room-side-blender.png`、`panda-room-loft-blender.png`：同一份密闭石屋几何的三个相机，真实 Tripo 熊猫导入同一场景。
- `panda-exterior-blender.png`：独立外壳、竹檐、圆窗、茶灯、竹叶路牌和石板小径。
- `panda-orientation-plusx.png`、`panda-orientation-minusy.png`：Tripo 原始方向核查。原始模型朝 +X，导出前旋转为 Godot +Z，避免用包围盒猜测方向。

原始来源与处理链见 [panda-asset-source.json](../../panda-asset-source.json)。可编辑源为 `worlds/frog/blender/panda-rig.blend`、`panda-home.blend`、`panda-home-with-tripo.blend` 和 `panda-exterior.blend`；构建入口是 `tools/prepare-panda.py` 与 `tools/build-panda-home.py`。

制作中修正：圆窗若用一个平面靠近弧形石壁，会被上部收拢的墙体吞掉。现在窗口、圆框和花格均沿当地石面径向布置；需在真实渲染中验证完整轮廓。运行副本按材料合并，源文件仍保留独立竹节、家具、器皿。

材质校准：一度把偏浅效果误判为预转 sRGB 导致重复提亮；三个独立色块及 GLB 往返实验否定了这个判断。8-bit generated image 的 .25 直接写入会得到过暗色块；.25 线性常量对应编码后的 .5371 才一致。最终保留正确编码，把期望的灰石、深竹木展示色先解码为较低线性反照率，再生成贴图；裂隙与灰缝常量使用同一线性域。实验原始结果见 `worlds/frog/blender/color-calibration/results.json`。

骨骼验证见 `panda-rig-check.json`：Idle 抽查 7 帧、Greet 抽查 5 帧，脚底最低点保持约 0，模型最高点 1.349–1.353；全部顶点最多 4 权重且归一化。

此处只证明模型与 Blender 视角，Godot 走动、互动及在线发布由项目主流程另行验收；不以源文件渲染代替实机结果。
