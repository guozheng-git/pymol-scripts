# -*- coding: utf-8 -*-
"""
Mutation Compare Plugin for PyMOL
Enhanced Qt Version v3

核心逻辑：
- PDB sequence 默认作为 WT/reference
- 输入框可以输入 1 条或多条 sequence
- 单序列模式：
    PDB/WT vs input sequence
    直接在原始 object 上按突变类型染色
- 多序列模式：
    PDB/WT vs multiple input sequences
    1. 原始 object 只创建 hotspot selections，不自动染色/显示
    2. 每条输入 sequence 自动复制一个 object
    3. 每个复制 object 独立按突变类型染色，避免颜色互相覆盖

Selections:
- exact_shared_geN_<object>
    至少 N 条序列共享完全相同突变
- shared_position_geN_<object>
    至少 N 条序列在同一 WT/PDB 位点发生突变，但突变 AA 可以不同

颜色：
- conservative: gray
- charge_change: green
- hydro_polar: cyan
- other: red
"""

import re
from collections import Counter

# from numpy import rec

from pymol.plugins import addmenuitemqt
from pymol import cmd
from PyQt5 import QtWidgets, QtCore


dialog = None


# =========================================================
# amino acid definitions
# =========================================================

AA3_TO_1 = {
    "ALA": "A", "VAL": "V", "PHE": "F", "PRO": "P", "MET": "M",
    "ILE": "I", "LEU": "L", "ASP": "D", "GLU": "E", "LYS": "K",
    "ARG": "R", "SER": "S", "THR": "T", "TYR": "Y", "HIS": "H",
    "CYS": "C", "ASN": "N", "GLN": "Q", "TRP": "W", "GLY": "G",
}

POSITIVE = set("KRH")
NEGATIVE = set("DE")
CHARGED = POSITIVE | NEGATIVE

HYDROPHOBIC = set("AVLIMFWYP")
POLAR = set("STNQCG")

DEFAULT_COLORS = {
    "conservative": "gray",
    "charge_change": "green",
    "hydro_polar": "cyan",
    "other": "red",
}


# =========================================================
# sequence parsing
# =========================================================

def normalize_sequence(seq):
    """
    清理单条序列：
    - 允许 FASTA header
    - 去掉空格、tab、换行
    """

    seq = seq.strip()

    lines = []

    for line in seq.splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith(">"):
            continue

        lines.append(line)

    return "".join(lines).replace(" ", "").replace("\t", "").upper()


# def parse_sequences(text):
#     """
#     支持：
#     - 单条裸序列
#     - 单条 FASTA
#     - multi-FASTA

#     返回：
#     list[str]
#     """

#     text = text.strip()

#     if not text:
#         return []

#     # 普通单序列
#     if ">" not in text:
#         return [normalize_sequence(text)]

#     # FASTA / multi-FASTA
#     seqs = []
#     current = []

#     for line in text.splitlines():

#         line = line.strip()

#         if not line:
#             continue

#         if line.startswith(">"):

#             if current:
#                 seqs.append("".join(current).replace(" ", "").replace("\t", "").upper())
#                 current = []

#         else:
#             current.append(line)

#     if current:
#         seqs.append("".join(current).replace(" ", "").replace("\t", "").upper())

#     return seqs

def parse_sequences(text):
    """
    支持：
    - 单条裸序列
    - 单条 FASTA
    - multi-FASTA

    返回：
    list of dict:
    [
        {"name": "MT-28", "seq": "MKT..."},
        {"name": "MT-04", "seq": "MKT..."},
    ]
    """

    text = text.strip()

    if not text:
        return []

    # 普通单序列：没有 FASTA header
    if ">" not in text:
        return [
            {
                "name": "seq1",
                "seq": normalize_sequence(text),
            }
        ]

    records = []
    current_name = None
    current_seq = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith(">"):

            if current_name is not None and current_seq:
                records.append(
                    {
                        "name": sanitize_object_name(current_name, max_len=15),
                        "seq": "".join(current_seq).replace(" ", "").replace("\t", "").upper(),
                    }
                )

            current_name = line[1:].strip()
            current_seq = []

        else:
            current_seq.append(line)

    if current_name is not None and current_seq:
        records.append(
            {
                "name": sanitize_object_name(current_name, max_len=15),
                "seq": "".join(current_seq).replace(" ", "").replace("\t", "").upper(),
            }
        )

    # 防止空 header 或重复名
    fixed_records = []
    used = set()

    for i, rec in enumerate(records, start=1):
        name = rec["name"] or f"seq{i}"

        if name in used:
            name = f"{name}_{i}"

        used.add(name)

        fixed_records.append(
            {
                "name": name,
                "seq": rec["seq"],
            }
        )

    return fixed_records

def sanitize_object_name(name, max_len=10):
    """
    把 FASTA header 转成 PyMOL object 友好的名字：
    - 只保留字母、数字、下划线、短横线
    - 其它字符替换成下划线
    - 限制长度
    """

    name = name.strip()

    if not name:
        name = "seq"

    safe = []

    for ch in name:
        if ch.isalnum() or ch in ["_", "-"]:
            safe.append(ch)
        else:
            safe.append("_")

    safe = "".join(safe).strip("_")

    if not safe:
        safe = "seq"

    return safe[:max_len]

# =========================================================
# mutation classification
# =========================================================

def classify_mutation(wt, mut):
    """
    输入方向：
    wt  = PDB/WT residue
    mut = input sequence residue
    """

    if wt == mut:
        return "WT"

    # charge change
    if wt in POSITIVE and mut in NEGATIVE:
        return "charge_change"

    if wt in NEGATIVE and mut in POSITIVE:
        return "charge_change"

    if (wt in CHARGED and mut not in CHARGED) or (wt not in CHARGED and mut in CHARGED):
        return "charge_change"

    # hydrophobic <-> polar
    if wt in HYDROPHOBIC and mut in POLAR:
        return "hydro_polar"

    if wt in POLAR and mut in HYDROPHOBIC:
        return "hydro_polar"

    # conservative
    if wt in POSITIVE and mut in POSITIVE:
        return "conservative"

    if wt in NEGATIVE and mut in NEGATIVE:
        return "conservative"

    if wt in HYDROPHOBIC and mut in HYDROPHOBIC:
        return "conservative"

    if wt in POLAR and mut in POLAR:
        return "conservative"

    return "other"


# =========================================================
# pdb sequence extraction
# =========================================================

def get_object_sequence(obj, chain=""):
    """
    从 PyMOL object 中提取 CA 序列。

    返回：
    pdb_seq, resi_list, chain_list

    注意：
    pdb_seq 的第 i 位对应：
        resi_list[i]
        chain_list[i]
    """

    if chain.strip():
        selection = f'"{obj}" and chain {chain.strip()} and name CA'
    else:
        selection = f'"{obj}" and name CA'

    model = cmd.get_model(selection)

    seq = []
    resi_list = []
    chain_list = []

    for atom in model.atom:

        aa = AA3_TO_1.get(atom.resn.upper(), "X")

        seq.append(aa)
        resi_list.append(atom.resi)
        chain_list.append(atom.chain)

    return "".join(seq), resi_list, chain_list


# =========================================================
# color parsing
# =========================================================

def parse_color(color_text, tag):
    """
    支持：
    - PyMOL 内置颜色名，例如 green, cyan, red
    - 十六进制颜色，例如 #ff0000
    """

    color_text = color_text.strip()

    if color_text.startswith("#") and len(color_text) == 7:

        try:
            r = int(color_text[1:3], 16) / 255.0
            g = int(color_text[3:5], 16) / 255.0
            b = int(color_text[5:7], 16) / 255.0

            color_name = f"user_mutcmp_{tag}"

            cmd.set_color(color_name, [r, g, b])

            return color_name

        except Exception:
            return DEFAULT_COLORS.get(tag, "red")

    return color_text


# =========================================================
# single-sequence / copied-object compare
# =========================================================

def compare_and_color(
    obj,
    ref_seq,
    chain="",
    color_map=None,
    show_labels=True,
    show_sticks=True,
):
    """
    对一个 object 进行 PDB/WT vs input sequence 比对并染色。

    重要：
    - PDB sequence = WT/reference
    - ref_seq/input sequence = mutant/design sequence

    所以突变方向是：
        PDB/WT residue -> input sequence residue
    """

    if color_map is None:
        color_map = DEFAULT_COLORS.copy()

    input_seq = normalize_sequence(ref_seq)

    pdb_seq, resi_list, chain_list = get_object_sequence(obj, chain)

    if not pdb_seq:
        raise ValueError(f"No CA atoms found in object: {obj}")

    if len(input_seq) != len(pdb_seq):

        raise ValueError(
            f"Length mismatch:\n"
            f"Input sequence length = {len(input_seq)}\n"
            f"PDB sequence length = {len(pdb_seq)}\n\n"
            f"This plugin currently assumes equal-length sequences."
        )

    groups = {
        "conservative": [],
        "charge_change": [],
        "hydro_polar": [],
        "other": [],
    }

    mutations = []

    for i, (mut_aa, wt_aa) in enumerate(zip(input_seq, pdb_seq)):

        if wt_aa == mut_aa:
            continue

        resi = resi_list[i]
        chain_id = chain_list[i]

        mtype = classify_mutation(wt_aa, mut_aa)

        groups[mtype].append(resi)

        mutations.append({
            "index": i + 1,
            "resi": resi,
            "chain": chain_id,
            "wt": wt_aa,
            "mut": mut_aa,
            "type": mtype,
            "label": f"{wt_aa}{resi}{mut_aa}",
        })

    # -----------------------------------------------------
    # reset object appearance
    # -----------------------------------------------------

    cmd.show("cartoon", f'"{obj}"')
    cmd.color("gray80", f'"{obj}"')

    cmd.hide("labels", f'"{obj}"')

    # 保守一点：隐藏 sticks，但不乱动其它显示
    cmd.hide("sticks", f'"{obj}"')

    # -----------------------------------------------------
    # color mutation groups
    # -----------------------------------------------------

    for mtype, resis in groups.items():

        if not resis:
            continue

        color = parse_color(
            color_map.get(mtype, DEFAULT_COLORS[mtype]),
            mtype,
        )

        resi_str = "+".join(
            str(x)
            for x in sorted(set(resis))
        )

        if chain.strip():

            sel = (
                f'"{obj}" and '
                f'chain {chain.strip()} and '
                f'resi {resi_str}'
            )

        else:

            sel = f'"{obj}" and resi {resi_str}'

        cmd.color(color, sel)

        if show_sticks:
            cmd.show("sticks", sel)

    # -----------------------------------------------------
    # labels
    # -----------------------------------------------------

    if show_labels:

        for m in mutations:

            if chain.strip():

                sel = (
                    f'"{obj}" and '
                    f'chain {chain.strip()} and '
                    f'resi {m["resi"]} and name CA'
                )

            else:

                sel = (
                    f'"{obj}" and '
                    f'resi {m["resi"]} and name CA'
                )

            cmd.label(
                sel,
                f'"{m["label"]}"'
            )

            cmd.show("labels", sel)

    return mutations, pdb_seq


# =========================================================
# hotspot analysis
# =========================================================

def analyze_hotspots(pdb_seq, sequences):
    """
    多序列 hotspot 统计。

    PDB sequence = WT/reference
    sequences    = variants

    exact_counter:
        具体突变计数，例如 D103E 出现了几次

    position_counter:
        位点突变计数，例如 position 103 有几条序列发生了突变
    """

    exact_counter = Counter()
    position_counter = Counter()

    mutation_records = []

    min_len = min(
        [len(pdb_seq)] + [len(s) for s in sequences]
    )

    for seq_idx, seq in enumerate(sequences):

        seq = normalize_sequence(seq)

        for i in range(min_len):

            wt = pdb_seq[i]
            aa = seq[i]

            if aa == wt:
                continue

            mutation = f"{wt}{i+1}{aa}"

            exact_counter[mutation] += 1
            position_counter[i+1] += 1

            mutation_records.append({
                "seq_index": seq_idx + 1,
                "position": i + 1,
                "wt": wt,
                "mut": aa,
                "mutation": mutation,
            })

    return {
        "exact_counter": exact_counter,
        "position_counter": position_counter,
        "mutation_records": mutation_records,
    }


# =========================================================
# hotspot selections
# =========================================================

def create_hotspot_selections(
    obj,
    hotspot_result,
    cutoff,
    resi_list,
    chain_list,
    make_exact=True,
    make_position=True,
):
    """
    只在原始 object 上创建 selections。
    不自动 show，不自动 color。

    命名：
    - exact_shared_geN_<obj>
    - shared_position_geN_<obj>
    """

    exact_counter = hotspot_result["exact_counter"]
    position_counter = hotspot_result["position_counter"]

    created = []

    # -----------------------------------------------------
    # exact mutation selection
    # -----------------------------------------------------

    if make_exact:

        exact_positions = []

        for mut, count in exact_counter.items():

            if count < cutoff:
                continue

            # safer parsing: A123V
            m = re.match(r"^[A-Z](\d+)[A-Z]$", mut)

            if not m:
                continue

            pos = int(m.group(1))

            exact_positions.append(pos)

        if exact_positions:

            resi_expr = []

            for pos in sorted(set(exact_positions)):

                idx = pos - 1

                if idx >= len(resi_list):
                    continue

                resi = resi_list[idx]
                chain = chain_list[idx]

                if chain:
                    resi_expr.append(f"(chain {chain} and resi {resi})")
                else:
                    resi_expr.append(f"(resi {resi})")

            if resi_expr:

                sel_expr = (
                    f'"{obj}" and ('
                    + " or ".join(resi_expr)
                    + ")"
                )

                sel_name = f"exact_shared_ge{cutoff}_{obj}"

                cmd.select(sel_name, sel_expr)

                created.append(sel_name)

    # -----------------------------------------------------
    # shared position selection
    # -----------------------------------------------------

    if make_position:

        shared_positions = []

        for pos, count in position_counter.items():

            if count >= cutoff:
                shared_positions.append(pos)

        if shared_positions:

            resi_expr = []

            for pos in sorted(set(shared_positions)):

                idx = pos - 1

                if idx >= len(resi_list):
                    continue

                resi = resi_list[idx]
                chain = chain_list[idx]

                if chain:
                    resi_expr.append(f"(chain {chain} and resi {resi})")
                else:
                    resi_expr.append(f"(resi {resi})")

            if resi_expr:

                sel_expr = (
                    f'"{obj}" and ('
                    + " or ".join(resi_expr)
                    + ")"
                )

                sel_name = f"shared_position_ge{cutoff}_{obj}"

                cmd.select(sel_name, sel_expr)

                created.append(sel_name)

    return created


# =========================================================
# per-sequence mutation selections
# =========================================================

def create_sequence_mutation_selection(
    selection_name,
    obj,
    mutations,
):
    """
    给每个 sequence-specific copied object 创建一个 selection，
    包含该 object 上所有发生突变、被染色的位点。

    selection_name:
        例如 MT-28_mutated_sites_fold2772

    obj:
        例如 MT-28_fold2772

    mutations:
        compare_and_color() 返回的 mutations list
    """

    if not mutations:
        return None

    resi_expr = []

    seen = set()

    for m in mutations:

        chain = m.get("chain", "")
        resi = m["resi"]

        key = (chain, resi)

        if key in seen:
            continue

        seen.add(key)

        if chain:
            resi_expr.append(
                f"(chain {chain} and resi {resi})"
            )
        else:
            resi_expr.append(
                f"(resi {resi})"
            )

    if not resi_expr:
        return None

    sel_expr = (
        f'"{obj}" and ('
        + " or ".join(resi_expr)
        + ")"
    )

    cmd.select(
        selection_name,
        sel_expr
    )

    return selection_name


# =========================================================
# GUI
# =========================================================

class MutationCompareDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("Mutation Compare")
        self.resize(850, 800)

        self.settings = QtCore.QSettings(
            "PyMOL",
            "MutationCompare"
        )

        # -------------------------------------------------
        # widgets
        # -------------------------------------------------

        self.obj_var = QtWidgets.QComboBox()
        self.obj_var.setEditable(True)

        self.chain_edit = QtWidgets.QLineEdit()
        self.chain_edit.setPlaceholderText(
            "optional, e.g. A"
        )

        self.seq_text = QtWidgets.QPlainTextEdit()

        self.seq_text.setPlaceholderText(
            "Single sequence OR multi-FASTA.\n"
            "PDB sequence is treated as WT/reference.\n\n"
            ">seq1\n"
            "SEQUENCE...\n"
            ">seq2\n"
            "SEQUENCE..."
        )

        self.result_text = QtWidgets.QPlainTextEdit()
        self.result_text.setReadOnly(True)

        # -------------------------------------------------
        # colors
        # -------------------------------------------------

        self.color_edits = {}

        for key in [
            "conservative",
            "charge_change",
            "hydro_polar",
            "other",
        ]:

            edit = QtWidgets.QLineEdit()

            edit.setText(
                self.settings.value(
                    f"color_{key}",
                    DEFAULT_COLORS[key]
                )
            )

            self.color_edits[key] = edit

        # -------------------------------------------------
        # options
        # -------------------------------------------------

        self.check_labels = QtWidgets.QCheckBox(
            "Show labels"
        )

        self.check_labels.setChecked(
            self.settings.value(
                "show_labels",
                True,
                type=bool,
            )
        )

        self.check_sticks = QtWidgets.QCheckBox(
            "Show sticks"
        )

        self.check_sticks.setChecked(
            self.settings.value(
                "show_sticks",
                True,
                type=bool,
            )
        )

        self.check_shared_exact = QtWidgets.QCheckBox(
            "Create exact shared hotspot selection"
        )

        self.check_shared_exact.setChecked(True)

        self.check_shared_position = QtWidgets.QCheckBox(
            "Create shared position hotspot selection"
        )

        self.check_shared_position.setChecked(True)

        self.cutoff_spin = QtWidgets.QSpinBox()

        self.cutoff_spin.setMinimum(2)
        self.cutoff_spin.setMaximum(999)
        self.cutoff_spin.setValue(2)

        # -------------------------------------------------
        # buttons
        # -------------------------------------------------

        self.btn_refresh = QtWidgets.QPushButton(
            "Refresh objects"
        )

        self.btn_compare = QtWidgets.QPushButton(
            "Analyze"
        )

        self.btn_reset_colors = QtWidgets.QPushButton(
            "Reset default colors"
        )

        # -------------------------------------------------
        # build ui
        # -------------------------------------------------

        self.build_ui()
        self.bind_signals()
        self.refresh_objects()

    # =====================================================
    # ui
    # =====================================================

    def build_ui(self):

        layout = QtWidgets.QVBoxLayout(self)

        # object

        row1 = QtWidgets.QHBoxLayout()

        row1.addWidget(QtWidgets.QLabel("PyMOL object:"))
        row1.addWidget(self.obj_var, stretch=1)
        row1.addWidget(self.btn_refresh)

        layout.addLayout(row1)

        # chain

        row2 = QtWidgets.QHBoxLayout()

        row2.addWidget(QtWidgets.QLabel("Chain ID:"))
        row2.addWidget(self.chain_edit)
        row2.addStretch()

        layout.addLayout(row2)

        # sequences

        layout.addWidget(
            QtWidgets.QLabel(
                "Input sequence(s):"
            )
        )

        layout.addWidget(
            self.seq_text,
            stretch=2
        )

        # colors

        color_box = QtWidgets.QGroupBox(
            "Mutation type colors"
        )

        color_layout = QtWidgets.QGridLayout(color_box)

        items = [
            ("Conservative", "conservative"),
            ("Charge change", "charge_change"),
            ("Hydrophobic ↔ Polar", "hydro_polar"),
            ("Other", "other"),
        ]

        for i, (label, key) in enumerate(items):

            color_layout.addWidget(
                QtWidgets.QLabel(label),
                i,
                0,
            )

            color_layout.addWidget(
                self.color_edits[key],
                i,
                1,
            )

        layout.addWidget(color_box)

        # hotspot box

        hotspot_box = QtWidgets.QGroupBox(
            "Hotspot analysis, multi-sequence mode only"
        )

        hotspot_layout = QtWidgets.QVBoxLayout(hotspot_box)

        cutoff_row = QtWidgets.QHBoxLayout()

        cutoff_row.addWidget(
            QtWidgets.QLabel(
                "Selection cutoff (>= N sequences)"
            )
        )

        cutoff_row.addWidget(self.cutoff_spin)
        cutoff_row.addStretch()

        hotspot_layout.addLayout(cutoff_row)

        hotspot_layout.addWidget(
            self.check_shared_exact
        )

        hotspot_layout.addWidget(
            self.check_shared_position
        )

        layout.addWidget(hotspot_box)

        # options

        option_row = QtWidgets.QHBoxLayout()

        option_row.addWidget(self.check_sticks)
        option_row.addWidget(self.check_labels)

        option_row.addStretch()

        option_row.addWidget(self.btn_reset_colors)
        option_row.addWidget(self.btn_compare)

        layout.addLayout(option_row)

        # result

        layout.addWidget(
            QtWidgets.QLabel("Results:")
        )

        layout.addWidget(
            self.result_text,
            stretch=3
        )

    # =====================================================
    # signals
    # =====================================================

    def bind_signals(self):

        self.btn_refresh.clicked.connect(
            self.refresh_objects
        )

        self.btn_compare.clicked.connect(
            self.run_compare
        )

        self.btn_reset_colors.clicked.connect(
            self.reset_colors
        )

    # =====================================================
    # refresh
    # =====================================================

    def refresh_objects(self):

        current = self.obj_var.currentText()

        objs = cmd.get_object_list("all")

        self.obj_var.clear()
        self.obj_var.addItems(objs)

        if current:
            self.obj_var.setCurrentText(current)

        elif objs:
            self.obj_var.setCurrentText(objs[0])

    # =====================================================
    # reset
    # =====================================================

    def reset_colors(self):

        for key, value in DEFAULT_COLORS.items():
            self.color_edits[key].setText(value)

    # =====================================================
    # run
    # =====================================================

    def run_compare(self):

        obj = self.obj_var.currentText().strip()

        chain = self.chain_edit.text().strip()

        seq_text = self.seq_text.toPlainText().strip()

        if not obj:

            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "Please select object"
            )

            return

        sequences = parse_sequences(seq_text)
        seq_strings = [x["seq"] for x in sequences]

        if len(sequences) == 0:

            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "No sequences found"
            )

            return

        color_map = {
            k: e.text().strip()
            for k, e in self.color_edits.items()
        }

        try:

            pdb_seq, resi_list, chain_list = get_object_sequence(
                obj,
                chain,
            )

            if not pdb_seq:
                raise ValueError(f"No CA atoms found in object: {obj}")

            # =================================================
            # single sequence mode
            # =================================================

            if len(sequences) == 1:

                mutations, pdb_seq = compare_and_color(
                    obj=obj,
                    ref_seq=seq_strings[0],
                    chain=chain,
                    color_map=color_map,
                    show_labels=self.check_labels.isChecked(),
                    show_sticks=self.check_sticks.isChecked(),
                )

                counts = {
                    "conservative": 0,
                    "charge_change": 0,
                    "hydro_polar": 0,
                    "other": 0,
                }

                for m in mutations:
                    counts[m["type"]] += 1

                lines = []

                lines.append(
                    "Single-sequence mode"
                )

                lines.append(
                    "PDB sequence is treated as WT/reference."
                )

                lines.append(
                    f"PDB length = {len(pdb_seq)}"
                )

                lines.append(
                    f"Total mutations = {len(mutations)}"
                )

                lines.append("")

                for k in [
                    "conservative",
                    "charge_change",
                    "hydro_polar",
                    "other",
                ]:
                    lines.append(
                        f"{k}: {counts[k]}"
                    )

                lines.append("")

                lines.append(
                    "index\tchain\tresi\tmutation\ttype"
                )

                for m in mutations:

                    lines.append(
                        f"{m['index']}\t"
                        f"{m['chain']}\t"
                        f"{m['resi']}\t"
                        f"{m['label']}\t"
                        f"{m['type']}"
                    )

                self.result_text.setPlainText(
                    "\n".join(lines)
                )

            # =================================================
            # multi-sequence hotspot mode
            # =================================================

            else:

                # ---------------------------------------------
                # reset original object appearance
                # ---------------------------------------------

                cmd.show("cartoon", f'"{obj}"')
                cmd.color("gray80", f'"{obj}"')

                cmd.hide("sticks", f'"{obj}"')
                cmd.hide("labels", f'"{obj}"')

                # ---------------------------------------------
                # hotspot analysis
                # ---------------------------------------------

                hotspot_result = analyze_hotspots(
                    pdb_seq,
                    seq_strings,
                )

                cutoff = self.cutoff_spin.value()

                # ---------------------------------------------
                # create selections on ORIGINAL object only
                # ---------------------------------------------

                created_selections = create_hotspot_selections(
                    obj=obj,
                    hotspot_result=hotspot_result,
                    cutoff=cutoff,
                    resi_list=resi_list,
                    chain_list=chain_list,
                    make_exact=self.check_shared_exact.isChecked(),
                    make_position=self.check_shared_position.isChecked(),
                )

                # ---------------------------------------------
                # create sequence-specific objects
                # ---------------------------------------------

                created_objects = []
                per_sequence_summaries = []

                # 多序列模式默认关闭 label，避免画面混乱
                # multi_show_labels = False
                # 多序列模式是否显示 label，由用户界面的 Show labels 决定
                multi_show_labels = self.check_labels.isChecked()

                #for i, seq in enumerate(sequences):
                for i, rec in enumerate(sequences):

                    seq_name = rec["name"]
                    seq = rec["seq"]

                    new_obj = f"{seq_name}_{obj}"

                    # 已存在就删除，避免旧颜色残留
                    if new_obj in cmd.get_object_list("all"):
                        cmd.delete(new_obj)

                    cmd.create(new_obj, obj)

                    created_objects.append(new_obj)

                    # compare_and_color(
                    #     obj=new_obj,
                    #     ref_seq=seq,
                    #     chain=chain,
                    #     color_map=color_map,
                    #     show_labels=multi_show_labels,
                    #     show_sticks=self.check_sticks.isChecked(),
                    # )
                    mutations, _ = compare_and_color(
                        obj=new_obj,
                        ref_seq=seq,
                        chain=chain,
                        color_map=color_map,
                        show_labels=multi_show_labels,
                        show_sticks=self.check_sticks.isChecked(),
                    )

                    mutation_selection_name = f"{seq_name}_mutated_sites_{obj}"

                    created_mutation_selection = create_sequence_mutation_selection(
                        selection_name=mutation_selection_name,
                        obj=new_obj,
                        mutations=mutations,
                    )

                    type_counts = {
                        "conservative": 0,
                        "charge_change": 0,
                        "hydro_polar": 0,
                        "other": 0,
                    }

                    for m in mutations:
                        type_counts[m["type"]] += 1

                    per_sequence_summaries.append({
                        "name": seq_name,
                        "object": new_obj,
                        "mutation_selection": created_mutation_selection,
                        "mutation_count": len(mutations),
                        "type_counts": type_counts,
                        "mutations": mutations,
                    })

                # ---------------------------------------------
                # result text
                # ---------------------------------------------

                lines = []

                lines.append(
                    "Multi-sequence hotspot mode"
                )

                lines.append(
                    "PDB sequence is treated as WT/reference."
                )

                lines.append(
                    f"Number of input sequences = {len(sequences)}"
                )

                lines.append(
                    f"PDB length = {len(pdb_seq)}"
                )

                lines.append(
                    f"Cutoff = {cutoff}"
                )

                lines.append("")

                lines.append(
                    "=== Created sequence objects ==="
                )

                for obj_name in created_objects:
                    lines.append(obj_name)

                lines.append("")

                lines.append("")


                for obj_name in created_objects:

                    lines.append(obj_name)

                lines.append("")

                lines.append(
                    "=== Created selections on ORIGINAL object only ==="
                )

                if created_selections:

                    for sel in created_selections:
                        lines.append(sel)

                else:
                    lines.append("None")

                lines.append("")

                # ---------------------------------------------
                # exact shared mutations
                # ---------------------------------------------

                lines.append(
                    "=== Exact shared mutations ==="
                )

                exact_found = False

                for mut, count in sorted(
                    hotspot_result["exact_counter"].items(),
                    key=lambda x: (-x[1], x[0])
                ):

                    if count >= cutoff:

                        exact_found = True

                        lines.append(
                            f"{mut}\tcount={count}"
                        )

                if not exact_found:
                    lines.append("None")

                lines.append("")

                # ---------------------------------------------
                # shared positions
                # ---------------------------------------------

                lines.append(
                    "=== Shared mutated positions ==="
                )

                shared_found = False

                for pos, count in sorted(
                    hotspot_result["position_counter"].items()
                ):

                    if count >= cutoff:

                        shared_found = True

                        lines.append(
                            f"position {pos}\tcount={count}"
                        )

                if not shared_found:
                    lines.append("None")

                lines.append("")

                # ---------------------------------------------
                # Per-sequence positions
                # ---------------------------------------------

                lines.append(
                    "=== Per-sequence mutation summary ==="
                )

                for summary in per_sequence_summaries:

                    lines.append("")
                    lines.append(
                        f"[{summary['name']}] object={summary['object']}"
                    )

                    if summary["mutation_selection"]:
                        lines.append(
                            f"Mutation selection = {summary['mutation_selection']}"
                        )
                    else:
                        lines.append(
                            "Mutation selection = None"
                        )

                    lines.append(
                        f"Total mutations = {summary['mutation_count']}"
                    )

                    for k in [
                        "conservative",
                        "charge_change",
                        "hydro_polar",
                        "other",
                    ]:
                        lines.append(
                            f"{k}: {summary['type_counts'][k]}"
                        )

                    mut_labels = [m["label"] for m in summary["mutations"]]

                    if mut_labels:
                        lines.append(
                            "Mutations: " + ", ".join(mut_labels)
                        )
                    else:
                        lines.append("Mutations: None")

                lines.append("")



                lines.append(
                    "Selections are NOT automatically colored or shown."
                )

                lines.append(
                    "Use PyMOL commands manually, e.g.:"
                )

                lines.append(
                    f"show sticks, shared_position_ge{cutoff}_{obj}"
                )

                lines.append(
                    f"color yellow, shared_position_ge{cutoff}_{obj}"
                )

                lines.append("")

                lines.append(
                    "Sequence-specific mutation chemistry coloring is applied to copied objects."
                )

                lines.append(
                    f"Labels in multi-sequence mode: {'ON' if multi_show_labels else 'OFF'}"
                )

                self.result_text.setPlainText(
                    "\n".join(lines)
                )

        except Exception as e:

            QtWidgets.QMessageBox.critical(
                self,
                "Mutation Compare Error",
                str(e)
            )

    # =====================================================
    # close
    # =====================================================

    def closeEvent(self, event):

        for key, edit in self.color_edits.items():

            self.settings.setValue(
                f"color_{key}",
                edit.text().strip()
            )

        self.settings.setValue(
            "show_labels",
            self.check_labels.isChecked()
        )

        self.settings.setValue(
            "show_sticks",
            self.check_sticks.isChecked()
        )

        super().closeEvent(event)


# =========================================================
# launcher
# =========================================================

def run_plugin_gui():

    global dialog

    try:
        dialog.close()
    except Exception:
        pass

    dialog = MutationCompareDialog()

    dialog.show()
    dialog.activateWindow()


def mutation_compare_panel():
    run_plugin_gui()


cmd.extend(
    "mutation_compare_panel",
    mutation_compare_panel
)


def __init_plugin__(app=None):

    addmenuitemqt(
        "Mutation Compare3",
        run_plugin_gui
    )

    print("[Mutation Compare] plugin loaded.")