from pymol import cmd

# Eisenberg 共识疏水性标度（参考 Eisenberg et al. 1984）
# web.expasy.org/protscale/pscale/Hphob.Eisenberg.html
eisenberg_scale = {
    'ALA': 0.620,  'ARG': -2.530, 'ASN': -0.780, 'ASP': -0.900,
    'CYS': 0.290,  'GLN': -0.850, 'GLU': -0.740, 'GLY': 0.480,
    'HIS': -0.400, 'ILE': 1.380,  'LEU': 1.060,  'LYS': -1.500,
    'MET': 0.640,  'PHE': 1.190,  'PRO': 0.120,  'SER': -0.180,
    'THR': -0.050, 'TRP': 0.810,  'TYR': 0.260,  'VAL': 1.080
}

def color_h(selection='all',
            ramp_name='hydro_ramp',
            cartoon_transparency=0.3,
            surface_transparency=0.5):
    """
    使用自定义疏水性标度上色，并添加 scale bar。
    """
    # 写入 b-factor
    for resn, value in eisenberg_scale.items():
        cmd.alter(f"{selection} and resn {resn}", f"b = {value}")
    cmd.rebuild()

    # 显示 cartoon + surface
    cmd.hide("everything", selection)
    cmd.show("cartoon", selection)
    cmd.show("surface", selection)
    cmd.set("cartoon_transparency", cartoon_transparency, selection)
    cmd.set("transparency", surface_transparency, selection)

    # 颜色映射（根据疏水性范围自动调整）
    # min_val = min(eisenberg_scale.values())
    min_val = -2.530
    # max_val = max(eisenberg_scale.values())
    max_val = 1.380
    cmd.spectrum("b", "blue_white_red", selection, minimum=min_val, maximum=max_val)
    cmd.ramp_new(ramp_name, selection, [min_val, 0.0, max_val], ["blue", "white", "red"])

cmd.extend("color_h", color_h)

#使用格式：color_h 1ubq, cartoon_transparency=0, surface_transparency=0.5