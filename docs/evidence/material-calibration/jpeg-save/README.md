# JPEG 保存颜色空间小检查

2026-09-12，Blender 5.2.1 LTS。为控制细化后网页体积，运行 GLB 的不透明 Base Color 改为 JPEG；原生模型保留 PNG，法线与粗糙度继续用无损 PNG。

同一个 16×16 灰块，8-bit sRGB 生成图片的 pixels 写入 0.5370987304831942（线性 0.25 的 sRGB 编码），用 Image.save 保存 JPEG。Pillow 读取中心 (8,8) 为 (137,137,137)。实际图片、结果与复现脚本位于本目录。

此结果说明该次 JPEG 保存没有再次改变颜色空间编码；不是所有图像像素完全不变的证明，也不是 Godot 渲染验证。JPEG 仍会产生局部压缩误差。

复现：`Blender --background --factory-startup --python reproduce.py`。读取结果：`PIL.Image.open('srgb-chip.jpg').getpixel((8,8))`。
