# pymol-scripts

My pymol plugins and scripts. Hope make pymol more easy to use ~

<br/>

| Tool | Function | Status |
|---|---|---|
|PymolMPNN | MPNN style sequence design inside pymol| Active |
|Mutation_Compare | compare given sequence and map results into struture | Active |
|Object_Autoplay | Browse 10^2 ~ 10^3 scale PDB model in pymol | Active |
|Style_Toggle | Switch pymol visualization  between classic and popular style | Active |
|addFIXEDlabels | RFdiffusion helper scripts | Stable | 

<br/>
<br/>

## Object_Autoplay
结构批量浏览插件（我制作的第一个pymol插件）<br/>
当前版本：object_autoplay_qt8.py
使用说明：

- GUI 控制（上一帧 / 下一帧 / 播放 / 暂停 / 筛选 / 排序 / 只播放可见 / 截图）
- 快捷键：←、→、F5、F6

更新说明：
object_autoplay_qt7：相较qt6增加了对滚轮的支持
object_autoplay_qt8：优化弹框内pdb名字的显示顺序（从字符串排序到数值排序）

<br/>

## Style_Toggle
渲染风格切换插件
当前版本：StyleToggleQtPlugin2.py
使用说明：

- 点击Apply Style 将风格切换为主刊常见的类Chimera风格
- 点击Restore Defaults 切换回pymol经典风格
- 可直接在GUI设置：输出目录、宽、高、DPI，并渲染导出

<br/>

## Mutation_Compare
突变批量可视化插件
当前版本：mutation_compare_qt_v4_6.py
使用说明：
- 以fasta格式输入1至多条序列，选择cutoff，得到差异位点的展示。

更新说明：
mutation_compare_qt_v3.5：增加批量添加fasta形式序列名的按钮
mutation_compare_qt_v4：增加对DNA序列的支持
mutation_compare_qt_v4_1：在 v4 的 DNA 预处理层上加“坏序列跳过”机制
mutation_compare_qt_v4_2：增加序列比对cutoff（排除掺入的长度符合要求的杂序列）
mutation_compare_qt_v4_3：加入length mismatch 跳过
mutation_compare_qt_v4_4：修正 hotspot report 编号体系 + 加 contributors 
mutation_compare_qt_v4_5：加一个 Show large results 按钮
mutation_compare_qt_v4_5_new：large results 窗口调整为600*800，且自动换行
mutation_compare_qt_v4_6：加入右侧和底部滚动条，增加窗口缩放灵活性

后续计划：
序列有多个cutter时做提示。


开发的
相比pymolwiki的color_h，color_h2b_E.py添加了显示表面和显示scale bar的功能。

autoplay3: use left (last object), right (next object), F5(pause & resume), F6 (print current object name) to check thousand-level scale of PDB files.

StyleToggleQtPlugin2: packaged “github.com/FridrichMethod/PyMOLScripts/blob/main/configs/.pymolrc” as a PyMOL plugin to facilitate switching between the default view and customized views. 

addFIXEDlabels_gz.py：An extended version of the dl_binder_design addFIXEDlabels script that does not require a trb file.

Pymol
Mutation_compare:
当前版本：mutation_compare_qt_v3_5.py：
Mutation Compare Plugin for PyMOL

Core Logic:
PDB sequence is used as the default WT/reference.
The input box accepts one or multiple sequences.

Single-sequence mode:
  Compares PDB/WT vs. input sequence.
  Colors mutations directly on the original object according to mutation type.

Multi-sequence mode:
  Compares PDB/WT vs. multiple input sequences.
  The original object is used only to create hotspot selections; no automatic coloring or display is applied.
  Each input sequence is automatically duplicated into a separate object.
  Each duplicated object is independently colored by mutation type to avoid color overlap.

Selections:
  exact_shared_geN_<object>:  At least N sequences share the exact same mutation.
  shared_position_geN_<object>: At least N sequences have a mutation at the same WT/PDB residue position, but the mutated amino acid may differ.
