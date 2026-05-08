# pymol-scripts
相比pymolwiki的color_h，color_h2b_E.py添加了显示表面和显示scale bar的功能。

autoplay3: use left (last object), right (next object), F5(pause & resume), F6 (print current object name) to check thousand-level scale of PDB files.

StyleToggleQtPlugin2: packaged “github.com/FridrichMethod/PyMOLScripts/blob/main/configs/.pymolrc” as a PyMOL plugin to facilitate switching between the default view and customized views. 

addFIXEDlabels_gz.py：An extended version of the dl_binder_design addFIXEDlabels script that does not require a trb file.

-------------------------
mutation_compare_qt_v3.py：
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
