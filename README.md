# frank 小世界

一起来创建可以走进去的小世界。由 [Frank](https://github.com/frankfanyiming) 发起，欢迎一起做场景、人物、玩法与优化。

## 已开放

**那个夏天 · 哆啦A梦小镇**：网页源码和游戏模型位于 [`worlds/doraemon/web`](worlds/doraemon/web)，可直接本地运行。**[点击直接游玩 →](https://frankfanyiming.github.io/frank_worlds/)** 无需安装或登录，首次会加载模型。

[下载 Godot 完整工程和 Blender 源资产](https://github.com/frankfanyiming/frank_worlds/releases/tag/doraemon-v1.0.0)。Godot 包已排除编辑器缓存，第一次打开需要导入资源。完整源工程使用 32 MiB 分卷，下载脚本会自动获取、拼接、校验并解包：

```sh
python3 tools/download-source-assets.py godot
python3 tools/download-source-assets.py blender
```

需要 Python 3.12 或更新版本。网页试玩无需下载这些源工程。

```sh
cd worlds/doraemon/web
npm ci
npm run dev
```

WASD 行走 · Shift 跑步 · V 切换视角 · E 互动 · H 招手 · R 剖面。可与伙伴交流，获得竹蜻蜓和任意门、从二楼抽屉进入时光机，也可玩棒球和调整季节时间。

## 世界进度

| 世界 | 当前状态 |
| --- | --- |
| 哆啦A梦 | 网页可玩，Godot 和 Blender 工程可下载 |
| 柯南 · 米花町 | 重建中，尚未公开成品 |
| 数码宝贝 | 计划中 |
| 七龙珠 | 计划中 |

不同世界放在 `worlds/<world>/`，各自保留运行说明和资产目录。欢迎先从一件家具、一条街道或一个动作开始贡献。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

代码 MIT；原创独立资产 CC BY 4.0，适用范围和原作署名见 [CREDITS.md](CREDITS.md)。这是非官方同人项目。
