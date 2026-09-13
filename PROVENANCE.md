# XLands 的署名与来源追溯

原创项目：**XLands小世界**。作者：**Frank（frankfanyiming / @FrankFYM001）**。

- 原始仓库：https://github.com/frankfanyiming/frank_worlds
- 作者：https://x.com/FrankFYM001
- 固定来源标识：`xlands-frankfym001`

## 使用与二次开发

本项目原创代码延续 [MIT 许可](LICENSE)，没有新增禁止修改或商业使用的代码许可条款。复制或分发相应代码时，应保留 MIT 要求的版权和许可声明。欢迎保留项目页面的作者署名、原始仓库链接和 [SOURCE.json](SOURCE.json)，在自己的作品中注明所作修改。

`SOURCE.json` 表示上游来源，fork 后不必把它改成自己的项目。构建时另行记录当前仓库与 Git 提交，以区分原项目和衍生版本。第三方依赖、模型、字体、贴图和既有作品 IP 的范围见 [CREDITS.md](CREDITS.md)；这些来源标识不把第三方作品标为 Frank 原创，也不授予额外 IP 权利。

## 已加入的来源标识

1. 本仓库的原创世界控制器、网页组件与相关脚本包含版权、SPDX 和原始仓库注释；生成库、第三方运行时不批量改署名。
2. Pages 构建的 JS 保留 `XLands build provenance` 注释，包含项目 ID、上游、当前构建提交。压缩之后仍可查找。
3. 发布目录中的 `provenance.json` 记录当前构建仓库、Git 提交、是否有相关未提交代码，以及此次前端产物的 SHA-256。网页壳包含相应提交，`SOURCE.json`、`NOTICE.txt` 和 `LICENSE.txt` 一同分发。
4. 首页页脚保留 `XLands小世界 · Frank / @FrankFYM001`。两种原生世界的壳也保留来源注释；无需重新导出大型游戏包。

## 如何核对

先查看目标站点的 `provenance.json`、页面源代码或下载后的 JS，查找 `xlands-frankfym001` 和 `frankfanyiming/frank_worlds`。在可信的原始仓库中核对该 Git 提交及发布记录。可以用 `tools/verify-build-provenance.mjs <发布目录>` 验证目录中各前端文件是否仍匹配构建清单。

散列匹配表示文件与清单一致，不等于清单本身具有可信签名；第三方可以一并修改代码和清单。保留的源码注释和 Git 历史有助于判断来源，但不能保证追踪被删除标识、重写或混淆过的代码，也不能自动知道谁使用了本项目。

本机制不请求回传接口，不收集访客身份、IP、设备信息或使用记录，不影响游戏循环。它是公开的署名与版本记录，不是防复制 DRM。
