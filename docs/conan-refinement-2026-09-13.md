# 柯南建筑与家具深化 · 2026-09-13

本轮状态：Blender 源模型、原生/网页 GLB 和 Godot Compatibility 实机验收。网页导出与发布由主任务单独完成，本记录不把本地截图当成线上发布证据。

## 变更与依据

用户给的毛利夜景截图要求浅冷蓝墙面、亮底深字事务所窗牌、暖色咖啡店。阿笠家家具与空间分区参考用户给出的双床、圆形厨房、环廊、地下实验室图纸，来源为[用户指定的建筑资料页](https://felicia1012.pixnet.net/blog/posts/14219272223)。图纸是相对布局参考，不是可靠的尺寸测绘图。

- 毛利楼深橙褐烘焙底色改为浅蓝灰，保留原法线与粗糙度。七扇窗采用独立浅色灯箱片和 W7 黑字，侧牌采用 W8 黑字；咖啡店旧细字完整移除，改为粗体窗标和杯形图标。
- 新招牌、吊灯和家具构件通过 `mouri-details.glb` / `kudo-details.glb` 加载，不重做已验收的建筑碰撞、角色或街区。
- 阿笠厨房改成有前开口的环形柜台：柜门、拉手、踢脚、洗槽、龙头、灶圈、抽油烟罩、器具和吧凳。62° 开口约 1.30 米，环台内缘半径 1.27 米、中央设备半径 0.48 米。角色可从客厅经开口进工作区。
- 两张床改为平行共用床头书柜方向；增加独立床架、嵌板、床垫、枕头、被面缝边、CRT、音箱、电脑车。床尾净空 1.30 米；床间缝约 0.23 米仅作家具间隔，不当通道。
- 客厅沙发增加分块坐垫、靠背、缝边、扶手和脚；茶桌增加层板和茶具。周边低书柜改为开架两层书格，保持窗带和环形室内视线。
- 毛利桌柜增加桌沿、抽屉、档案标签、文具托盘、布巾及餐具。工藤已有边柜和厨房柜增补框架门板、抽屉、拉手、桌布缝边和早餐器具。
- 地下实验室、车库、塔楼旋梯、上下层洞口保持已验收的结构与通路。不是把所有楼梯重建一遍。

## 可复现来源

- `tools/conan/patch-mouri-reference.py`：从保存的 release20 原件精确剔除旧字索引和修改墙面材质，逐项断言所有碰撞 buffer 与 25 张内嵌图片不变。
- `tools/conan/build-house-detail.py`：测量原家具坐标后生成独立门板、桌沿、标牌和灯具，写入 `detail_assets` / `accent_lights` / `emissive_materials` 元数据。
- `tools/conan/agasa_furniture.py`：可复用的圆台、双床、成套客厅、书柜构件。
- `tools/conan/build-agasa-reference.py`：组装阿笠外壳与新家具，输出路线、入口、房间和视图坐标。
- `tools/conan/capture-reference-refinement.gd`：实际 `world.tscn` 和生产昼夜设置截图；只隐藏 UI 和玩家避免遮挡，不藏墙、不加摄影灯。

源文件位于 `worlds/conan/blender/reference-2026-09/`；正式消费的 GLB 与 JSON 位于 `worlds/conan/{source,web-project}/assets/buildings/`。不要发布 `originals/`、完整 `.blend` 或原始导入归档。

## 引擎证据与适用范围

[实机视角清单](evidence/conan-refinement-2026-09-13/pass04/capture-report.json) 包含 Godot 4.7.2 Compatibility 的 22 个昼夜视角。生产材质、环境光和建筑可见性均保留。重点：

- [浅墙与窗字](evidence/conan-refinement-2026-09-13/pass04/day-mouri-sign-close.png)
- [夜间毛利楼](evidence/conan-refinement-2026-09-13/pass04/night-mouri-night-reference.png)
- [咖啡店近景](evidence/conan-refinement-2026-09-13/pass04/night-mouri-poirot-close.png)
- [阿笠厨房与整体分区](evidence/conan-refinement-2026-09-13/pass04/day-agasa-whole-plan.png)
- [双床、床头书柜与显示器](evidence/conan-refinement-2026-09-13/pass04/day-agasa-beds.png)
- [厨房实际料理开口](evidence/conan-refinement-2026-09-13/pass04/day-agasa-kitchen.png)
- [成套客厅](evidence/conan-refinement-2026-09-13/pass04/day-agasa-living.png)
- [地下研究区](evidence/conan-refinement-2026-09-13/pass04/day-agasa-research.png)
- [工藤边柜](evidence/conan-refinement-2026-09-13/pass04/day-kudo-joinery.png)

[真实角色碰撞结果](evidence/conan-refinement-2026-09-13/routes03/physical-routes.json)：41 项检查、295 个实际行走分段、0 失败；包含门外连街、厨房开口双向、主厅到塔楼、地下一层往返、二楼环廊往返、车库往返。测试运行正常 CharacterBody3D 物理，`testing=false`，没有用瞬移或射线替代步行。该检查证明通路，不证明移动浏览器帧率。

所有资产校验见 [asset-manifest.json](evidence/conan-refinement-2026-09-13/asset-manifest.json)。Conan / Kogoro / Agasa 人物 SHA 与本轮输入一致，修复后的姿态与动作未被建筑导出覆盖。路线结果包含最终厨房互动点 metadata；路线后仅调整三盏咖啡灯的夜间强度，碰撞和控制器未变。最终夜景 pass04 已用生产灯复验。

网页阿笠建筑为 31.97 MB，原为约 21.28 MB；网格由约 31.7 万三角面增到 46.2 万，增加的是家具构件。毛利独立细节 2.10 MB，工藤 0.53 MB。需要在最终 Web 包中验证实际加载与触屏性能，不能从桌面原生截图推断手机流畅度。

## 经验沉淀

1. 字体名存在不代表字体真的被加载。macOS 日文字体文件名使用分解 Unicode，直接写 NFC 路径会找不到；扫描后统一 NFC 比较并在失败时显式报错，避免静默回退细字。窗上文字需要用实际步行距离而非建模窗口放大检查。
2. 旧字不一定叫 Text 或 Ink。原咖啡字使用雨篷红和黄铜材质。删除要联合 mesh、材质与局部几何范围，不能整材质删除，否则雨篷和五金也会消失。
3. 补几何比重复烘焙全楼更可控。独立 detail GLB 保留旧家具纹理与既有物理，新增框架门板和五金需先测量原物体表面位置。
4. 缝边需要实际几何间距。最初被面细线与床被顶部交叉，吧凳缝边与坐垫同面；抬高 0.01 米并缩小线径后，实机闪面消失。不要只靠 Blender 材质视图验收。
5. 厨房需要先留可走的开口，再布柜门和凳子。凳面有实体碰撞、柜台碰撞与可见弧形一致，工作路线绕桌腿而非穿家具。
6. Compatibility 模式中整楼合并 mesh 加上大量 Omni 时，单独增加更强彩灯未必产生预期的局部暖色。要复用房间已有主灯并按时间设置颜色，实际渲染检查，而不是只读 JSON 中的暖色值。pass02 暴露了咖啡店暖度不足；复用原有三盏咖啡灯，夜間设为杏色并将原能量乘 3.2，白天保持原能量。pass04 确认暖色墙、桌和灯具可见，同时外墙冷蓝和事务所白底黑字保留。
7. 街区全景的汽车可能挡住窗牌。增加实际人行道近景相机来核查文字，不临时隐藏车、墙或换摄影照明。
