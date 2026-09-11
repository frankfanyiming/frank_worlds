# Blender 5.2.1 生成贴图颜色校准

2026-09-12。只运行颜色实验，未改动青蛙家正式模型。

结论：**对于本项目实际使用的 8-bit generated Image、sRGB 色彩空间、Image.pixels 写入后 pack 再导出 GLB 的流程，如果输入色值表达的是线性 albedo，必须先编码成 sRGB 再写入 Image.pixels。** 此流程与 Principled BSDF 的常量线性 Base Color 一致。删除预编码虽然让画面变暗，但并不是修复双重编码，而是降低了真实反射率。

不要把这个结论泛化到 float_buffer=True、线性图片色彩空间、Non-Color 法线贴图或其他读写 API；本次没有测这些路径。

## 设计与实测

三块相同大小、相同法线的平面，均匀白色 World 光，Cycles 64 samples，Standard 色彩变换，无 Look、无曝光偏移。Principled roughness=1，specular=0。三个平面分别为：

| 从左到右 | 材质构造 | 原场景渲染 RGB 均值 | GLB 回导渲染均值 | GLB 内嵌 PNG 像素 |
|---|---|---:|---:|---:|
| A | 常量 Base Color 线性 0.25 | 136.966 | 136.966 | 无图片；baseColorFactor=0.25 |
| B | sRGB Image.pixels 直接写 0.25 | 64.007 | 64.007 | 64 / 255 |
| C | 0.25 线性先编码为 0.537099，再写 Image.pixels | 136.988 | 136.988 | 137 / 255 |

另外把三个材质接到 Emission，排除灯光与 BSDF 的影响，得到相同数值。每个色块取中央 48×48 像素均值。A 与 C 差异为 0.022 个 8-bit 灰度级（低于一个 8-bit 量化级），A 与 B 差异约 73 个灰度级。

写入 Image.pixels 后立即读取，B 为 0.2509804、C 为 0.5372549；pack 前后不变，显示这个 float_buffer=False 的图像缓冲已经按 8-bit 色样量化。导出的 PNG 也保留相同码值。B 的 64/255 经 sRGB 解码后约为线性 0.0513，远低于声明的 0.25。

![原场景：左常量，中直接写，右正确预编码](01-original-principled.png)

![GLB 导出回导：同样结果](03-glb-roundtrip-principled.png)

## 在项目中怎么用

- 如果材质参数定义为**线性 albedo**：常量节点直接用该线性数值；8-bit sRGB 颜色贴图对该数值做 linear_to_srgb 后写入。
- 如果调色时选择的是**显示用 sRGB 色值**：先定义它为 sRGB，再解码成线性用于常量节点；写到 8-bit sRGB 图片时使用原 sRGB 码值。不要让同一个 RGB 元组在常量和纹理里代表两个不同色域。
- 屋子太亮时，调整真实反射率、光照与曝光，不能通过破坏色彩空间让纹理“碰巧变暗”。裂隙和灰缝等常量材质也要保持相同线性标准。
- 法线纹理仍是 Non-Color 数据，本次颜色转换规则不适用于法线。

## 文件与复现

- `calibrate.py`：可复用实验脚本，生成三种材质、原场景渲染、Emission 渲染、GLB 和回导渲染。
- `calibration.blend` / `calibration.glb`：实际源文件和导出文件。
- `experiment.json`：版本、节点/像素设置与 pack 前后缓冲值。
- `sample.py`：用 Pillow 对三次渲染和 GLB 内嵌 PNG 采样。
- `results.json`：中央像素均值、材质 JSON 与内嵌 PNG 原始码值。
- `B_generated_direct_linear.png` / `C_generated_preconverted_sRGB.png`：从 GLB 内嵌缓冲提取的图片，未改色。

从项目根目录运行：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python docs/evidence/material-calibration/calibrate.py
python3 docs/evidence/material-calibration/sample.py
```

此前“生成 PNG 的线性色值需转换到 sRGB”的项目记录，在这条具体的 8-bit 生成图片流程里被实验证实；需要补充其适用边界，而不是反向改成一律删除转换。
