# 朋友日常实机证据

本轮新增熊猫串门、料理、送礼、同行野餐与共同照片。代码已接入本地源项目；上线状态以本轮发布记录为准。

- `state.json`：22/22 状态与 JSON 重载规范化检查通过。
- `runtime/runtime.json`：最终家具、静态烘焙接入后的 34/34 真引擎检查通过。包括在料理第2步销毁世界、重建世界后继续第3步，以及原57枚三叶草、旧照片、礼物和新相片恢复。
- `route/route.json`：住宅→营地→东桥头→过桥→蛙家四段同行全部通过；熊猫实际走67.29米，角色使用碰撞移动。
- `runtime/03-cooking-progress.png`：新家具前的实际三步料理画面。此图是桌面原生控件验证，网页采用统一 HTML UI，不将它当最终网页UI设计。
- `runtime/04-gift-displays.png`：礼物留在熊猫家的固定展示位置。
- `runtime/photos/friends-memory-6.png`：最后逐图复核的实际双人合影。薄布已贴合地面、修正朝上面和双面显示；没有添加角色贴图或背景图。
- `runtime/photos/friends-memory-4.png` 是34项功能验证中保存的照片；当前已用最终薄布和存档修复重跑。5为背面法线排查中间结果，6为独立视觉复核。

运行脚本：`tools/test-frog-friends-state.gd`、`test-frog-friends-runtime.gd`、`test-frog-friends-route.gd`。`capture-frog-friends-memory.gd` 仅用于在已完成的测试营地存档上重拍视觉比较图。测试存档中的额外相片来自此比较操作，不是又进行了一次消耗料理的正常野餐。

房间切换使用游戏正常门口转场；料理第二配方与营地照片测试有显式 fixture 坐标，仅用于单独验证交互，不声称这两段通过全地图步行。完整实际同行另由四段路线报告覆盖。图像不是AI生成图。基础配方和朋友逻辑不依赖服务器或API；跨设备同步尚未实现。
