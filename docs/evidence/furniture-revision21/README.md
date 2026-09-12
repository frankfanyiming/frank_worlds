# 家具精细化实机证据 · revision 21

本目录为真实 Godot 场景截图，不是效果提案。蛙家闭合蘑菇踏板、圆润树桩桌、杯碗及苔藓边缘已更新；熊猫家补了木作接头、茶盘、柜门与布料。两户日/暮照明在更新几何后重新烘焙。

- `final-bake-report.json`：四套 LightmapGI 结果。
- `final-uv2-report.json`：更新场景的 UV2。
- `dependency-closure.json`、`copied-resource-hashes.json`：74项烘焙依赖及复制校验。
- `runtime-proof.json`：Compatibility 实际镜头、动态角色和场景。
- `final-frog-day-close.png`、`final-panda-day-tea.png`：代表近景；其余昼夜/阁楼图保留在本地目录。

未更改房间楼梯尺寸和碰撞路线。大雄世界邻居及楼下家具补了椅子栏杆、桌榫、沙发分块坐垫与包边，新模型为 `neighborhood-v21.glb`；97项碰撞与18个分组保持原数据，原卧室资产继续使用已验收的 v12。

可编辑模型在本地 Blender 源文件与工作区“outputs/世界改版21”中保留；网页以 GLB / Godot 运行包交付。
