# 那个夏天 · frank 小世界

可自由探索的哆啦A梦同人 3D 小镇，由 Frank 发起，欢迎一起共建。

包括大雄家两层室内、庭院、学校周边、河流、桥与后山；角色互动、竹蜻蜓、任意门、抽屉时光机、棒球挑战、四季昼夜和环境音。其他住宅主要开放外观与庭院，网页画面与 Godot 桌面版存在差异。

## 本地运行

需要 Node.js 22.13 或更新版本。

```sh
npm ci
npm run dev
```

浏览器打开终端显示的本地地址。项目无登录要求，无需 Tripo 密钥即可运行已有模型。首次下载模型较大，建议桌面浏览器和硬件加速。

## 操作

WASD / 方向键行走，Shift 跑步，鼠标拖动环视，V 切换视角，E 互动，H 招手，R 剖面；地图可直接前往地点。竹蜻蜓：空格上升、Ctrl 下降、C 着陆。手机可用屏幕方向键。

## 验证与构建

```sh
node node_modules/typescript/bin/tsc --noEmit
node tools/verify-world.mjs
npm run build
```

`app/` 是界面，`lib/town/` 是玩法和渲染，`public/models/` 是已压缩、含内嵌贴图的游戏模型。Godot 与 Blender 工程见仓库 Releases。

源码、共建入口与资产下载：[frank_worlds](https://github.com/frankfanyiming/frank_worlds)。许可与原作来源见 [CREDITS.md](CREDITS.md)。
