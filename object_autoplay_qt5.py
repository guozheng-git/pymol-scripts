# -*- coding: utf-8 -*-
"""
Object Autoplay (Advanced)
最终版：含自动播放、筛选、排序、自动旋转、截图、循环模式、快捷键
"""

from pymol.plugins import addmenuitemqt
from pymol import cmd
from PyQt5 import QtWidgets, QtCore

dialog = None


class ObjectAutoplayDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Object Autoplay (Advanced)")
        self.resize(420, 350)

        # 状态
        self.all_objs = []
        self.filtered_objs = []
        self.index = 0
        self.is_playing = False

        # 保存用户设置
        self.settings = QtCore.QSettings("PyMOL", "ObjectAutoplay")

        interval = self.settings.value("interval", 2.0, type=float)
        only_visible = self.settings.value("only_visible", False, type=bool)
        spin_on = self.settings.value("spin_on", False, type=bool)
        loop_mode = self.settings.value("loop_mode", 0, type=int)

        # ===================== 控件 =====================

        self.label_current = QtWidgets.QLabel("当前显示: (无对象)")
        self.label_current.setWordWrap(True)

        self.list_widget = QtWidgets.QListWidget()

        # 筛选输入
        self.edit_filter = QtWidgets.QLineEdit()
        self.edit_filter.setPlaceholderText("输入关键词筛选 object...")

        # 排序
        self.combo_sort = QtWidgets.QComboBox()
        self.combo_sort.addItems(["名称 A→Z", "名称 Z→A"])

        # 轮播间隔
        self.spin_interval = QtWidgets.QDoubleSpinBox()
        self.spin_interval.setRange(0.5, 60.0)
        self.spin_interval.setValue(interval)
        self.spin_interval.setSingleStep(0.5)

        # 只播放可见对象
        self.check_visible = QtWidgets.QCheckBox("只播放可见对象")
        self.check_visible.setChecked(only_visible)

        # 自动旋转
        self.check_spin = QtWidgets.QCheckBox("自动旋转 spin")
        self.check_spin.setChecked(spin_on)

        # 循环模式
        self.combo_loop = QtWidgets.QComboBox()
        self.combo_loop.addItems(["循环所有对象", "单项重复"])
        self.combo_loop.setCurrentIndex(loop_mode)

        # 按钮
        self.btn_refresh = QtWidgets.QPushButton("刷新对象列表")
        self.btn_prev = QtWidgets.QPushButton("⟵ 上一个")
        self.btn_play = QtWidgets.QPushButton("▶ 播放")
        self.btn_next = QtWidgets.QPushButton("下一个 ⟶")
        self.btn_snapshot = QtWidgets.QPushButton("📸 截图当前对象")

        # ===================== 布局 =====================

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label_current)
        layout.addWidget(self.list_widget)

        # 筛选 + 排序
        h_filter = QtWidgets.QHBoxLayout()
        h_filter.addWidget(self.edit_filter)
        h_filter.addWidget(self.combo_sort)
        layout.addLayout(h_filter)

        # 配置行 1
        h_cfg1 = QtWidgets.QHBoxLayout()
        h_cfg1.addWidget(QtWidgets.QLabel("间隔 秒:"))
        h_cfg1.addWidget(self.spin_interval)
        h_cfg1.addWidget(self.check_visible)
        layout.addLayout(h_cfg1)

        # 配置行 2
        h_cfg2 = QtWidgets.QHBoxLayout()
        h_cfg2.addWidget(self.check_spin)
        h_cfg2.addWidget(self.combo_loop)
        layout.addLayout(h_cfg2)

        # 控制按钮
        h_btns = QtWidgets.QHBoxLayout()
        h_btns.addWidget(self.btn_prev)
        h_btns.addWidget(self.btn_play)
        h_btns.addWidget(self.btn_next)
        layout.addLayout(h_btns)

        layout.addWidget(self.btn_snapshot)
        layout.addWidget(self.btn_refresh)

        # ===================== 计时器 =====================
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timeout)

        # ===================== 信号 =====================
        self.btn_refresh.clicked.connect(self.refresh_objects)
        self.btn_prev.clicked.connect(self.prev_object)
        self.btn_next.clicked.connect(self.next_object)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_snapshot.clicked.connect(self.take_snapshot)
        self.list_widget.currentRowChanged.connect(self.on_list_select)

        self.edit_filter.textChanged.connect(self.apply_filter)
        self.combo_sort.currentIndexChanged.connect(self.apply_filter)

        # 初始化
        self.refresh_objects()

    # =============================================================
    # 功能函数
    # =============================================================

    def refresh_objects(self):
        """刷新 object 列表"""
        all_items = cmd.get_object_list()

        if self.check_visible.isChecked():
            visible = []
            for o in all_items:
                try:
                    if cmd.get("enable", o) == "on":
                        visible.append(o)
                except:
                    visible.append(o)
            self.all_objs = visible
        else:
            self.all_objs = all_items

        self.apply_filter()

    def apply_filter(self):
        """筛选与排序"""
        keyword = self.edit_filter.text().lower()
        items = [o for o in self.all_objs if keyword in o.lower()]

        # 排序
        if self.combo_sort.currentIndex() == 0:
            items.sort()
        else:
            items.sort(reverse=True)

        self.filtered_objs = items
        self.list_widget.clear()

        if not items:
            self.label_current.setText("当前显示: (无对象)")
            return

        for o in items:
            self.list_widget.addItem(o)

        self.index = 0
        self.list_widget.setCurrentRow(0)
        self.show_object(0)

    def show_object(self, idx):
        """显示 object"""
        if not self.filtered_objs:
            return

        self.index = idx % len(self.filtered_objs)
        obj = self.filtered_objs[self.index]

        cmd.do("disable all")
        cmd.do(f"enable {obj}")

        if self.check_spin.isChecked():
            cmd.do("spin on")
        else:
            cmd.do("spin off")

        self.label_current.setText(f"当前显示: {obj}")

    def next_object(self):
        if not self.filtered_objs:
            return

        if self.combo_loop.currentIndex() == 1:
            # 单项重复
            self.show_object(self.index)
        else:
            self.show_object(self.index + 1)

    def prev_object(self):
        if not self.filtered_objs:
            return
        self.show_object(self.index - 1)

    def on_list_select(self, row):
        if 0 <= row < len(self.filtered_objs):
            self.show_object(row)

    # =============================================================
    # 播放控制
    # =============================================================

    def toggle_play(self):
        if self.is_playing:
            self.timer.stop()
            self.is_playing = False
            self.btn_play.setText("▶ 播放")
        else:
            interval_ms = int(self.spin_interval.value() * 1000)
            self.timer.start(interval_ms)
            self.is_playing = True
            self.btn_play.setText("⏸ 暂停")

    def on_timeout(self):
        self.next_object()

    # =============================================================
    # 截图
    # =============================================================

    def take_snapshot(self):
        if not self.filtered_objs:
            return
        obj = self.filtered_objs[self.index]
        filename = f"{obj}_{self.index}.png"
        cmd.png(filename, width=1600, height=1200, ray=1)
        print(f"[Snapshot] Saved → {filename}")

    # =============================================================
    # 保存用户设置
    # =============================================================

    def closeEvent(self, event):
        self.settings.setValue("interval", self.spin_interval.value())
        self.settings.setValue("only_visible", self.check_visible.isChecked())
        self.settings.setValue("spin_on", self.check_spin.isChecked())
        self.settings.setValue("loop_mode", self.combo_loop.currentIndex())

        self.timer.stop()
        super().closeEvent(event)


# =============================================================
# 快捷键绑定函数
# =============================================================

def key_next():
    if dialog is not None:
        dialog.next_object()


def key_prev():
    if dialog is not None:
        dialog.prev_object()


def key_toggle_play():
    if dialog is not None:
        dialog.toggle_play()


def key_print():
    if dialog is not None and dialog.filtered_objs:
        name = dialog.filtered_objs[dialog.index]
        print(f"[Object Autoplay] 当前对象: {name}")


# =============================================================
# 插件入口：菜单 + 快捷键
# =============================================================

def run_plugin_gui():
    global dialog
    try:
        dialog.close()
    except:
        pass
    dialog = ObjectAutoplayDialog()
    dialog.show()
    dialog.activateWindow()


def __init_plugin__(app=None):
    addmenuitemqt("Object Autoplay (Advanced)", run_plugin_gui)

    # 快捷键绑定
    cmd.set_key("right", key_next)
    cmd.set_key("left", key_prev)
    cmd.set_key("F5", key_toggle_play)
    cmd.set_key("F6", key_print)

    print("[Object Autoplay] Advanced version loaded with full shortcut keys!")
