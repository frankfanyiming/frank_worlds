# 那个夏天 · frank 小世界

可自由探索的哆啦A梦同人 3D 小镇，由 Frank 发起，欢迎一起共建。

包括大雄家与静香家两层室内、庭院、学校周边、河流、桥与后山；角色互动、竹蜻蜓、任意门、抽屉时光机、棒球挑战、四季昼夜和环境音。胖虎家和小夫家开放外观与庭院，网页画面与 Godot 桌面版存在差异。

## 本地运行

需要 Node.js 22.13 或更新版本。

```sh
npm ci
npm run dev
```

浏览器打开终端显示的本地地址。项目无登录要求，无需 Tripo 密钥即可运行已有模型。首次下载模型较大，建议桌面浏览器和硬件加速。

## 操作

WASD / 方向键行走，Shift 跑步，鼠标拖动环视，V 切换视角，E 互动，R 剖面；口袋内的任意门可前往地点。竹蜻蜓：空格上升、Ctrl 下降、C 着陆。手机可用屏幕方向键。

## 2026-09-10 更新

加载进度保持在 0–100%，首次成功绘制后才完成。资源失败会提供重试入口；低性能设备可在网址末尾加 `?safe=1`。加载界面使用旋转的二维哆啦A梦头像，支持系统的减少动态效果设置。移除了页面品牌块、地点卡、小地图和招手操作。

野比家和静香家支持一、二楼和可连续行走的楼梯；房间门与哆啦A梦壁橱使用独立滑动面板、固定轨道与碰撞。胖虎家、小夫家外观、喷泉及庭院按参考重建。角色、草木、车辆与道路使用压缩贴图和减面版本。

使用 `npm test` 检查加载、通路与交通；`node tools/verify-adventure.cjs` 回归现有玩法与推拉门防夹；`npm run typecheck` 检查类型；`npm run build:pages` 生成 GitHub Pages 发布包。构建只保留运行时模型，房间精修贴图单独加载，音频按需加载。

大雄房间恢复到用户确认过的 Godot 精修资产：保留完整家具网格、4K 墙面/木材/榻榻米色彩贴图、2K 扫描法线与粗糙度，以及布料和盆栽贴图。`bedroom-materials/manifest.json` 保留来源、尺寸和 SHA-256；这些贴图没有降采样。网页移植了榻榻米织纹采样与木纹方向，并配置窗边阴影和室内暖色反射光。网页实时光照与原 Godot 烘焙光照仍可能有差别。

新楼梯从原房门接入。当前建筑源文件为 `tools/neighborhood-v12.blend`，脚本为 `restore_bedroom_neighborhood.py`；房间导入、原始贴图复制、重复贴图剔除脚本依次为 `restore_bedroom_details.py`、`copy_bedroom_materials.py`、`prune_bedroom_maps.py`。最终资产已包含在仓库，日常运行无需 Blender。旧版全局降采样脚本不适用于已恢复的精修房间。

## 验证与构建

```sh
node node_modules/typescript/bin/tsc --noEmit
node tools/verify-world.mjs
npm run build
```

`app/` 是界面，`lib/town/` 是玩法和渲染，`public/models/` 是已压缩、含内嵌贴图的游戏模型。Godot 与 Blender 工程见仓库 Releases。

源码、共建入口与资产下载：[frank_worlds](https://github.com/frankfanyiming/frank_worlds)。许可与原作来源见 [CREDITS.md](CREDITS.md)。


## GitHub Pages

线上地址：https://frankfanyiming.github.io/frank_worlds/

运行 `npm ci` 后执行 `npm run build:pages`。将 `dist-pages` 发布到 GitHub Pages。子目录资源路径自动使用 `/frank_worlds/`。
