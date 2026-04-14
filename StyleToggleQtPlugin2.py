from pymol import cmd
from pymol.Qt import QtWidgets
import os

try:
    from pymol.plugins import addmenuitemqt
except Exception:
    addmenuitemqt = None

_DIALOG = None


def apply_my_style():
    cmd.do("util.performance(0)")
    cmd.do("space cmyk")

    settings = [
        ("ambient", 0.25),
        ("ambient_occlusion_mode", 1),
        ("ambient_occlusion_scale", 1.0),
        ("ambient_occlusion_smooth", 100),
        ("antialias", 2),
        ("antialias_shader", 2),
        ("async_builds", 1),
        ("backface_cull", 1),
        ("bg_rgb", "white"),
        ("cartoon_ladder_mode", 1),
        ("cartoon_loop_radius", 0.2),
        ("cartoon_nucleic_acid_mode", 4),
        ("cartoon_oval_quality", 100),
        ("cartoon_oval_width", 0.2),
        ("cartoon_rect_width", 0.3),
        ("cartoon_ring_finder", 1),
        ("cartoon_ring_mode", 3),
        ("cartoon_ring_width", 0.15),
        ("cartoon_ring_transparency", 0.5),
        ("cartoon_sampling", 20),
        ("cartoon_side_chain_helper", 1),
        ("cartoon_smooth_loops", 0),
        ("cartoon_tube_quality", 100),
        ("cartoon_tube_radius", 0.5),
        ("dash_radius", 0.14),
        ("dash_width", 4),
        ("defer_builds_mode", 3),
        ("depth_cue", 1),
        ("direct", 0.5),
        ("draw_mode", 1),
        ("dynamic_width", 1),
        ("fog", 1),
        ("fog_start", 0.4),
        ("hash_max", 16000),
        ("light_count", 8),
        ("line_smooth", 1),
        ("nb_spheres_quality", 3),
        ("opaque_background", 0),
        ("orthoscopic", 1),
        ("power", 0),
        ("ray_opaque_background", 0),
        ("ray_orthoscopic", 1),
        ("ray_shadow", 0),
        ("ray_shadow_decay_factor", 0),
        ("ray_shadow_decay_range", 0),
        ("ray_trace_depth_factor", 1),
        ("ray_trace_disco_factor", 0.4),
        ("ray_trace_fog", 1),
        ("ray_trace_fog_start", 0.5),
        ("ray_trace_frames", 0),
        ("ray_trace_gain", 0.2),
        ("ray_trace_mode", 1),
        ("ray_trace_slope_factor", 50),
        ("reflect", 0.3),
        ("ribbon_sampling", 20),
        ("shininess", 50),
        ("spec_count", -1),
        ("spec_direct", 0),
        ("spec_direct_power", 0),
        ("spec_power", 0),
        ("spec_reflect", 0),
        ("specular", 0),
        ("specular_intensity", 1),
        ("sphere_quality", 2),
        ("stick_radius", 0.3),
        ("surface_mode", 0),
        ("surface_quality", 2),
        ("surface_ramp_above_mode", 1),
        ("surface_smooth_edges", 1),
        ("surface_solvent", 0),
        ("transparency", 0.5),
        ("transparency_mode", 2),
        ("two_sided_lighting", 1),
        ("valence", 1),
        ("valence_mode", 1),
        ("volume_layers", 1000),
    ]

    for key, value in settings:
        cmd.set(key, value)

    cmd.do("valence guess, all")

    downloads_dir = os.path.expanduser("~/Downloads")
    if os.path.isdir(downloads_dir):
        try:
            os.chdir(downloads_dir)
        except Exception:
            pass


def restore_defaults():
    cmd.reinitialize("settings")


def ray_and_export(output_path=None, width=2400, height=1800, dpi=300):
    if output_path is None or not str(output_path).strip():
        output_path = os.path.join(os.getcwd(), "pymol_render.png")

    output_path = os.path.expanduser(output_path)
    output_dir = os.path.dirname(output_path)

    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    if not output_path.lower().endswith(".png"):
        output_path += ".png"

    # 用一次性 png(ray=1) 代替先 ray 再 png，通常更稳
    cmd.png(output_path, width=width, height=height, dpi=dpi, ray=1)
    return output_path


class StyleToggleDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(StyleToggleDialog, self).__init__(parent)
        self.setWindowTitle("Style Toggle")
        self.setMinimumWidth(460)

        layout = QtWidgets.QVBoxLayout(self)

        info = QtWidgets.QLabel(
            "Apply your PyMOL preset, restore defaults, or ray trace and export a PNG."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_apply = QtWidgets.QPushButton("Apply Style")
        btn_apply.clicked.connect(self.on_apply_style)
        layout.addWidget(btn_apply)

        btn_restore = QtWidgets.QPushButton("Restore Defaults")
        btn_restore.clicked.connect(self.on_restore_defaults)
        layout.addWidget(btn_restore)

        layout.addSpacing(10)

        form = QtWidgets.QFormLayout()

        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setText(os.path.join(os.getcwd(), "pymol_render.png"))

        path_row_widget = QtWidgets.QWidget()
        path_row = QtWidgets.QHBoxLayout(path_row_widget)
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.addWidget(self.path_edit)

        btn_browse = QtWidgets.QPushButton("Browse")
        btn_browse.clicked.connect(self.on_browse)
        path_row.addWidget(btn_browse)

        form.addRow("Output image:", path_row_widget)

        self.width_spin = QtWidgets.QSpinBox()
        self.width_spin.setRange(100, 20000)
        self.width_spin.setValue(2400)
        form.addRow("Width:", self.width_spin)

        self.height_spin = QtWidgets.QSpinBox()
        self.height_spin.setRange(100, 20000)
        self.height_spin.setValue(1800)
        form.addRow("Height:", self.height_spin)

        self.dpi_spin = QtWidgets.QSpinBox()
        self.dpi_spin.setRange(30, 1200)
        self.dpi_spin.setValue(300)
        form.addRow("DPI:", self.dpi_spin)

        layout.addLayout(form)

        btn_ray_export = QtWidgets.QPushButton("Ray + Export PNG")
        btn_ray_export.clicked.connect(self.on_ray_export)
        layout.addWidget(btn_ray_export)

        btn_apply_and_export = QtWidgets.QPushButton("Apply Style + Ray + Export PNG")
        btn_apply_and_export.clicked.connect(self.on_apply_and_export)
        layout.addWidget(btn_apply_and_export)

        self.status_label = QtWidgets.QLabel("Ready.")
        self.status_label.setWordWrap(True)
        layout.addSpacing(8)
        layout.addWidget(self.status_label)

    def set_status(self, text):
        self.status_label.setText(text)
        print(text)

    def on_apply_style(self):
        try:
            apply_my_style()
            self.set_status("Style applied.")
        except Exception as e:
            self.set_status(f"Apply style failed: {e}")

    def on_restore_defaults(self):
        try:
            restore_defaults()
            self.set_status("PyMOL settings restored to defaults.")
        except Exception as e:
            self.set_status(f"Restore defaults failed: {e}")

    def on_browse(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Rendered Image",
            self.path_edit.text(),
            "PNG Image (*.png)"
        )
        if filename:
            if not filename.lower().endswith(".png"):
                filename += ".png"
            self.path_edit.setText(filename)

    def on_ray_export(self):
        try:
            self.set_status("Rendering and exporting...")
            path = ray_and_export(
                output_path=self.path_edit.text(),
                width=self.width_spin.value(),
                height=self.height_spin.value(),
                dpi=self.dpi_spin.value(),
            )
            self.set_status(f"Saved image to: {path}")
        except Exception as e:
            self.set_status(f"Export failed: {e}")

    def on_apply_and_export(self):
        try:
            self.set_status("Applying style...")
            apply_my_style()
            self.set_status("Rendering and exporting...")
            path = ray_and_export(
                output_path=self.path_edit.text(),
                width=self.width_spin.value(),
                height=self.height_spin.value(),
                dpi=self.dpi_spin.value(),
            )
            self.set_status(f"Style applied and image saved to: {path}")
        except Exception as e:
            self.set_status(f"Apply + export failed: {e}")


def show_dialog():
    global _DIALOG
    try:
        if _DIALOG is None:
            _DIALOG = StyleToggleDialog()
        _DIALOG.show()
        _DIALOG.raise_()
        _DIALOG.activateWindow()
    except Exception:
        _DIALOG = StyleToggleDialog()
        _DIALOG.show()


def __init_plugin__(app=None):
    if addmenuitemqt is not None:
        addmenuitemqt("Style Toggle", show_dialog)


cmd.extend("apply_my_style", apply_my_style)
cmd.extend("restore_pymol_defaults", restore_defaults)
cmd.extend("ray_and_export", ray_and_export)