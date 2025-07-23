import re
from collections import defaultdict

def list_patch_residues_with_area_and_atom_counts(pat_file, top_n=None):
    """
    读取 .pat 文件，输出每个 patch 的面积、残基列表及每个残基包含的原子数。
    """
    with open(pat_file, 'r') as f:
        lines = f.readlines()

    in_patch_section = False
    patch_index = -1
    patch_info = {}  # {patch_index: {'area': float, 'residue_counts': dict}}
    collecting_residue_lines = False
    residue_lines = []
    patch_count = 0
    current_area = 0.0

    for line in lines:
        line = line.strip()

        if not in_patch_section:
            if line.startswith("surface 'after recover'"):
                in_patch_section = True
            continue

        # 遇到 patch 开头，处理上一个 patch
        if line.startswith("#"):
            if collecting_residue_lines and patch_index >= 0:
                residue_counts = count_residues_from_lines(residue_lines)
                patch_info[patch_index]['residue_counts'] = residue_counts
                residue_lines = []
                collecting_residue_lines = False

            if top_n is not None and patch_count >= top_n:
                break

            parts = line.split()
            try:
                patch_index = int(parts[1])
                if "area" in parts:
                    area_index = parts.index("area")
                    current_area = float(parts[area_index + 1])
                else:
                    current_area = 0.0  # fallback
                patch_info[patch_index] = {'area': current_area, 'residue_counts': {}}
                patch_count += 1
            except:
                patch_index = -1
            continue

        if line.startswith("%"):
            continue

        if ";" in line:
            residue_lines.append(line)
            collecting_residue_lines = True

    # 补上最后一个 patch
    if collecting_residue_lines and patch_index >= 0:
        residue_counts = count_residues_from_lines(residue_lines)
        patch_info[patch_index]['residue_counts'] = residue_counts

    # 输出所有 patch 信息
    for idx in sorted(patch_info):
        area = patch_info[idx]['area']
        residue_counts = patch_info[idx]['residue_counts']
        print(f"Patch #{idx} | Area: {area:.3f} Å² | {len(residue_counts)} residues:")
        for res in sorted(residue_counts, key=lambda x: (x[0], int(x[1:]))):
            count = residue_counts[res]
            print(f"  - {res}: {count} atom{'s' if count > 1 else ''}")
        print()

def count_residues_from_lines(lines):
    """
    统计每个残基对应的原子数量。
    返回格式: { 'B33': 2, 'C87': 7, ... }
    """
    residue_counts = defaultdict(int)
    pattern = re.compile(r'([A-Z]) ([A-Z])(\d+) @')  # e.g., A B33 @ CB
    for line in lines:
        matches = re.findall(pattern, line)
        for _, chain, resi in matches:
            residue = f"{chain}{resi}"
            residue_counts[residue] += 1
    return residue_counts

# 示例调用
# list_patch_residues_with_area_and_atom_counts("TNF-3mer.pat", top_n=5)
