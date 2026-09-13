# 柯南世界开放家具素材记录 · 2026-09-13

这轮先替换博士家的工作桌与靠窗矮柜，再补事务所和工藤宅的书籍。建筑外观、门窗、楼梯和房间动线继续使用项目的参考图建模，家具库只承担适合其尺寸和用途的物件。

## 已下载并接入

以下五组是 Poly Haven 的 CC0 模型，来源与作者由官方 API 的模型记录核对。其[官方许可页](https://polyhaven.com/license)允许修改和随项目分发。31 个源文件已逐个核对大小和 MD5；机器可读记录见 [下载清单](../tools/conan/open-assets-manifest.json)。

| 模型与原作者 | 实际使用位置 | 调整 |
| --- | --- | --- |
| [Metal Office Desk](https://polyhaven.com/a/metal_office_desk) · Ulan Cabanilla | 博士家地下工作区、车库工作台 | 按工作台标高重设尺度，柜门朝向操作通道 |
| [Desk Lamp Arm 01](https://polyhaven.com/a/desk_lamp_arm_01) · Kuutti Siitonen / Yann Kervran | 地下工作桌、车库工作台 | 冻结家具自带姿态，保留关节和夹具；不处理角色骨骼 |
| [Vintage Radio Transceiver](https://polyhaven.com/a/vintage_radio_transceiver) · Mateusz Sadek | 博士实验桌、车库台面 | 缩放整套设备，保留旋钮、面板和附件 |
| [Modern Wooden Cabinet](https://polyhaven.com/a/modern_wooden_cabinet) · Patrik Pangerl | 博士家客厅弧窗旁 | 替换原有两段书柜，不与旧柜叠放；柜体和碰撞一同旋转 |
| [Book Encyclopedia Set 01](https://polyhaven.com/a/book_encyclopedia_set_01) · John Malcolm | 博士家矮柜、毛利办公桌、工藤宅边柜 | 整套书籍按真实尺寸摆放，避开原有花瓶、台灯和文具 |

源模型保留在本地 `work/open-assets-r22`；改造后的可编辑 Blender 场景在各世界 `blender` 目录。网页使用导出的运行模型。完整原始模型归档仍沿用仓库 README 的发布状态，不把网页运行包等同于全部编辑源文件。

## 已核对、尚未接入的参考候选

- [Anime Classroom — argonius / BlendSwap](https://blendswap.com/blend/19436)：页面标注 CC0，作者说明模型及照片贴图由自己制作，场景包含教室和走廊。适合后续学校场景；不是本轮住宅家具的替代品。
- [Japanese Vending Machine — argonius / BlendSwap](https://blendswap.com/blend/19306)：页面标注 CC0，适合住宅街转角或咖啡店附近。

本次访问这两项下载入口时需要登录，因此没有下载或宣称已装入。页面展示效果也不作为 Godot 实机效果证据。

## 重建

1. `python3 tools/conan/download-open-furniture.py`：从清单获取精确版本，验证已有文件；不在游戏运行时调用素材服务。
2. 用 Blender 执行 `tools/conan/build-agasa-reference.py`：创建带开放家具的博士住宅。
3. 用 Blender 执行 `tools/conan/prepare-reference-runtime.py`：导出桌面与网页副本，网页贴图最长边 768；颜色及打包材质图用 JPEG，法线图保留无损。
4. 用 Blender 执行 `tools/conan/build-site-access.py`：加入完整车库地基、排水沟与连续车道，并补齐场地路线。
5. 用 Blender 执行 `tools/conan/open_furniture.py`：导出事务所和工藤宅的独立家具部件。
6. Godot 导入后执行 `tools/test-conan-reference-routes.gd`，用 `tools/conan/capture-access22.gd` 检查落地、朝向、与旧家具的重叠和通行空间。

完整工程基础资产需已安装。本轮增量下载脚本不声称能替代仍未发布的完整原始模型归档。
