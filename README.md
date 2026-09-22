# pymol-scripts

My pymol plugins and scripts. Hope make pymol more easy to use ~

<br/>

| Tool | Function | Status |
|---|---|---|
|PymolMPNN | MPNN style sequence design inside pymol| Active |
|Mutation_Compare | compare given sequence and map results into struture | Active |
|Object_Autoplay | Browse 10^2 ~ 10^3 scale PDB model in pymol | Stable |
|Style_Toggle | Switch pymol visualization  between classic and popular style | Stable |
|addFIXEDlabels | RFdiffusion helper scripts | Stable | 

<br/>
<br/>

## Object_Autoplay
结构批量浏览插件（我制作的第一个pymol插件）<br/>
当前版本：object_autoplay_qt8.py <br/>
使用说明：

- GUI 控制（上一帧 / 下一帧 / 播放 / 暂停 / 筛选 / 排序 / 只播放可见 / 截图）
- 快捷键：←、→、F5、F6

更新说明：
object_autoplay_qt7：相较qt6增加了对滚轮的支持 <br/>
object_autoplay_qt8：优化弹框内pdb名字的显示顺序（从字符串排序到数值排序） <br/>

后续计划：
优化对滚轮的支持


## Style_Toggle
渲染风格切换插件 <br/>
（风格来源：github.com/FridrichMethod/PyMOLScripts/blob/main/configs/.pymolrc）<br/>
当前版本：StyleToggleQtPlugin2.py <br/>
使用说明：

- 点击Apply Style 将风格切换为主刊常见的类Chimera风格
- 点击Restore Defaults 切换回pymol经典风格
- 可直接在GUI设置：输出目录、宽、高、DPI，并渲染导出


## Mutation_Compare
突变批量可视化插件 <br/>
当前版本：mutation_compare_qt_v4_6.py <br/>
使用说明：
- 以fasta格式输入1至多条序列，选择cutoff，得到差异位点的展示。

实现逻辑：
PDB sequence is used as the default WT/reference. <br/>
The input box accepts one or multiple sequences. <br/>

Single-sequence mode:<br/>
  Compares PDB/WT vs. input sequence.<br/>
  Colors mutations directly on the original object according to mutation type.<br/>

Multi-sequence mode:<br/>
  Compares PDB/WT vs. multiple input sequences.<br/>
  The original object is used only to create hotspot selections; no automatic coloring or display is applied.<br/>
  Each input sequence is automatically duplicated into a separate object.<br/>
  Each duplicated object is independently colored by mutation type to avoid color overlap.<br/>

Selections:<br/>
  exact_shared_geN_<object>:  At least N sequences share the exact same mutation.<br/>
  shared_position_geN_<object>: At least N sequences have a mutation at the same WT/PDB residue position, but the mutated amino acid may differ.<br/>

更新说明：
mutation_compare_qt_v3.5：增加批量添加fasta形式序列名的按钮 <br/>
mutation_compare_qt_v4：增加对DNA序列的支持 <br/>
mutation_compare_qt_v4_1：在 v4 的 DNA 预处理层上加“坏序列跳过”机制 <br/>
mutation_compare_qt_v4_2：增加序列比对cutoff（排除掺入的长度符合要求的杂序列） <br/>
mutation_compare_qt_v4_3：加入length mismatch 跳过 <br/>
mutation_compare_qt_v4_4：修正 hotspot report 编号体系 + 加 contributors  <br/>
mutation_compare_qt_v4_5：加一个 Show large results 按钮 <br/>
mutation_compare_qt_v4_5_new：large results 窗口调整为600*800，且自动换行 <br/>
mutation_compare_qt_v4_6：加入右侧和底部滚动条，增加窗口缩放灵活性 <br/>

后续计划：
序列有多个cutter时做提示。


## hydrophobic_analysis
疏水分析插件 <br/>
coming soon

旧版：color_h2b_E.py
使用说明：相比pymolwiki的color_h，color_h2b_E.py添加了显示表面和显示scale bar的功能。


## 其他

addFIXEDlabels_gz.py：An extended version of the dl_binder_design addFIXEDlabels script that does not require a trb file.

<br/>
