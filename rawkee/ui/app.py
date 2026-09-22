"""
File Author: Thomaz Diaz, UND Dream Lab;
Description: "Rawkee Scan Studio Main Aplication"  [DL-4]:

Librays Used: 
-Pyside6 on Python 3.14 Interpreter
-
"""

import sys
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QButtonGroup,
    QStackedWidget,
    QDockWidget,
    QTextEdit,
    QStatusBar,
    QLabel,
    QLineEdit,
    QFormLayout,
    QGridLayout,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QGroupBox,
    QCheckBox,
    QScrollArea,
    QToolButton,
)

from .theme import apply_theme


class RawKeeMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RawKee Scan Studio")
        self.resize(1200, 700)
        self.setMinimumSize(900, 500)

        self._page_index: Dict[str, int] = {}

        # layout
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # sidebar
        self.sidebar = QWidget()
        self.sidebar.setObjectName("rk_sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(6, 6, 6, 6)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: Dict[str, QPushButton] = {}
        for name, icon in [("Mesh","⛶"),("Gaussian Splat","⁕"),("Folder → Splat","🖿"),("Convert Splat","⇄")]:
            b = QPushButton(f"  {icon}  {name}")
            b.setCheckable(True)
            b.setProperty("class", "rk_navButton")
            # store the logical page name for this button so toggles map correctly
            b.setProperty("rk_name", name)
            self.nav_group.addButton(b)
            sidebar_layout.addWidget(b)
            self.nav_buttons[name] = b

        sidebar_layout.addStretch()

        # central stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("rk_stack")

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(container)
        self._last_console_message = ""

        # register pages for each sidebar item (Mesh + real pages)
        for pname in list(self.nav_buttons.keys()):
            if pname == "Mesh":
                page = MeshPage()
            elif pname == "Gaussian Splat":
                page = GaussianSplatPage()
            elif pname == "Folder → Splat":
                page = FolderSplatPage()
            elif pname == "Convert Splat":
                page = ConvertSplatPage()
            else:
                page = PlaceholderPage(pname)
            self.register_tool_page(pname, page)

        # select default
        self.select_tool_page("Mesh")

        # console dock
        dock = QDockWidget("Console")
        dock.setObjectName("rk_console_dock")
        dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetClosable)
        dock.setMinimumHeight(70)
        dock.setMaximumHeight(220)
        

        console = QTextEdit()
        console.setObjectName("rk_console")
        console.setReadOnly(True)
        console.setLineWrapMode(QTextEdit.NoWrap)
        console.append("Ready to process scan data.")
        dock.setWidget(console)

        title_bar = QWidget()
        title_bar.setObjectName("rk_console_titlebar")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 0, 0, 0)
        title_layout.setSpacing(6)

        toggle_btn = QToolButton()
        toggle_btn.setToolTip("Collapse / expand console")
        toggle_btn.setArrowType(Qt.DownArrow)
        toggle_btn.setFixedSize(18, 30)
        toggle_btn.clicked.connect(lambda: self._toggle_console_dock(dock, console, toggle_btn))

        title_label = QLabel("Console")
        title_label.setObjectName("rk_console_title")
        title_layout.addWidget(toggle_btn)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        dock.setTitleBarWidget(title_bar)

        self.addDockWidget(Qt.BottomDockWidgetArea, dock)
        self._console = console

        # status bar
        sb = QStatusBar()
        self._status_label = QLabel("Ready")
        # give the left status label a stable objectName for styling
        self._status_label.setObjectName("rk_status_left")
        self._activity_label = QLabel("Idle")
        # right-side activity badge (matches accent)
        self._activity_label.setObjectName("rk_status_right")
        sb.addWidget(self._status_label)
        sb.addPermanentWidget(self._activity_label)
        self.setStatusBar(sb)

        # connect
        self.nav_group.buttonToggled.connect(self._on_nav_toggled)
        # default visual selection
        first = list(self.nav_buttons.values())[0]
        first.setChecked(True)

    def _on_nav_toggled(self, button: QPushButton, checked: bool) -> None:
        if not checked:
            return
        # prefer the stored logical name property so icons/spacing don't break matching
        name = button.property("rk_name") or button.text().strip()
        if name in self._page_index:
            self.stack.setCurrentIndex(self._page_index[name])
            # announce selection
            try:
                self.update_status("Ready")
                self.append_console_output("Ready")
            except Exception:
                pass

    def register_tool_page(self, name: str, widget: QWidget) -> int:
        idx = self.stack.addWidget(widget)
        self._page_index[name] = idx
        return idx

    def select_tool_page(self, name: str) -> None:
        if name in self._page_index:
            self.stack.setCurrentIndex(self._page_index[name])
            btn = self.nav_buttons.get(name)
            if btn:
                btn.setChecked(True)

    def append_console_output(self, message: str) -> None:
        if message == self._last_console_message:
            return
        self._console.append(message)
        self._last_console_message = message

    def update_status(self, status_text: str, activity_state: str = "Idle") -> None:
        self._status_label.setText(status_text)
        self._activity_label.setText(activity_state)

    def _toggle_console_dock(self, dock: QDockWidget, console: QTextEdit, toggle_btn: QToolButton) -> None:
        is_expanded = console.isVisible()

        if is_expanded:
            console.hide()
            dock.setMinimumHeight(30)
            dock.setMaximumHeight(30)
            toggle_btn.setArrowType(Qt.RightArrow)
            dock.resize(dock.width(), 28)
        else:
            console.show()
            dock.setMinimumHeight(70)
            dock.setMaximumHeight(220)
            toggle_btn.setArrowType(Qt.DownArrow)
            dock.resize(dock.width(), 120)


class MeshPage(QWidget):
    """Visual mock of the Mesh page matching the wireframe (no processing)."""

    def __init__(self):
        super().__init__()
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QWidget()
        header.setObjectName("headerContainer")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 10)

        icon = QLabel("⛶")
        icon.setObjectName("headerIcon")
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignCenter)

        title_block = QWidget()
        t_layout = QVBoxLayout(title_block)
        t_layout.setContentsMargins(8, 0, 0, 0)
        t_layout.setSpacing(2)

        title = QLabel("Mesh")
        title.setObjectName("pageTitle")
        desc = QLabel("Create a textured polygon mesh from LiDAR or photogrammetry scan data.")
        desc.setObjectName("pageDescription")

        t_layout.addWidget(title)
        t_layout.addWidget(desc)

        h_layout.addWidget(icon)
        h_layout.addWidget(title_block, 1)
        main.addWidget(header)

        # Input / Output group
        io_box = QGroupBox("Input / Output")
        io_box_layout = QFormLayout(io_box)

        ds_row = QWidget()
        ds_layout = QHBoxLayout(ds_row)
        ds_layout.setContentsMargins(0, 0, 0, 0)
        ds_input = QLineEdit("/path/to/navvis-folder or project.psx")
        ds_browse = QPushButton("Browse ▾")
        ds_browse.setProperty("class", "rk_browse")
        ds_layout.addWidget(ds_input)
        ds_layout.addWidget(ds_browse)
        io_box_layout.addRow("Dataset", ds_row)

        out_row = QWidget()
        out_layout = QHBoxLayout(out_row)
        out_layout.setContentsMargins(0, 0, 0, 0)
        out_input = QLineEdit("/path/to/output")
        out_browse = QPushButton("Browse...")
        out_browse.setProperty("class", "rk_browse")
        out_layout.addWidget(out_input)
        out_layout.addWidget(out_browse)
        io_box_layout.addRow("Output", out_row)

        main.addWidget(io_box)

        # Mesh Options
        opts = QGroupBox("Mesh Options")
        opts_grid = QGridLayout(opts)
        opts_grid.setSpacing(12)

        opts_grid.addWidget(QLabel("Poisson depth"), 0, 0)
        opts_grid.addWidget(QSpinBox(), 0, 1)
        opts_grid.addWidget(QLabel("Max LiDAR pkts"), 0, 2)
        opts_grid.addWidget(QSpinBox(), 0, 3)

        opts_grid.addWidget(QLabel("Atlas size (px)"), 1, 0)
        opts_grid.addWidget(QSpinBox(), 1, 1)
        opts_grid.addWidget(QLabel("Envmap width"), 1, 2)
        opts_grid.addWidget(QSpinBox(), 1, 3)

        opts_grid.addWidget(QLabel("Colorize stride"), 2, 0)
        opts_grid.addWidget(QSpinBox(), 2, 1)
        opts_grid.addWidget(QLabel("Envmap height"), 2, 2)
        opts_grid.addWidget(QSpinBox(), 2, 3)

        main.addWidget(opts)

        main.addStretch()

        # Primary action aligned right
        footer = QWidget()
        f_layout = QHBoxLayout(footer)
        f_layout.addStretch()
        run_btn = QPushButton("▷ Run Mesh Pipeline")
        run_btn.setObjectName("rk_primary")
        f_layout.addWidget(run_btn)
        main.addWidget(footer)


class PlaceholderPage(QWidget):
    def __init__(self, title: str):
        super().__init__()
        l = QVBoxLayout(self)
        l.setContentsMargins(20, 20, 20, 20)
        lbl = QLabel(title)
        lbl.setObjectName("pageTitle")
        desc = QLabel(f"Placeholder page for {title}.")
        desc.setObjectName("pageDescription")
        l.addWidget(lbl)
        l.addWidget(desc)
        l.addStretch()


class GaussianSplatPage(QWidget):
    def __init__(self):
        super().__init__()
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QWidget()
        header.setObjectName("headerContainer")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 10)

        icon = QLabel("⁕")
        icon.setObjectName("headerIcon")
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignCenter)

        title_block = QWidget()
        t_layout = QVBoxLayout(title_block)
        t_layout.setContentsMargins(8, 0, 0, 0)
        t_layout.setSpacing(2)

        title = QLabel("Gaussian Splat")
        title.setObjectName("pageTitle")
        desc = QLabel("Train and export a Gaussian splat from a supported scan dataset.")
        desc.setObjectName("pageDescription")

        t_layout.addWidget(title)
        t_layout.addWidget(desc)

        h_layout.addWidget(icon)
        h_layout.addWidget(title_block, 1)
        main.addWidget(header)

        # Input / Output group
        io_box = QGroupBox("Input / Output")
        io_layout = QFormLayout(io_box)

        ds_row = QWidget()
        ds_layout = QHBoxLayout(ds_row)
        ds_layout.setContentsMargins(0, 0, 0, 0)
        ds_input = QLineEdit("/path/to/navvis-folder or project.psx")
        ds_browse = QPushButton("Browse ▾")
        ds_browse.setProperty("class", "rk_browse")
        ds_layout.addWidget(ds_input)
        ds_layout.addWidget(ds_browse)
        io_layout.addRow("Dataset", ds_row)

        out_row = QWidget()
        out_layout = QHBoxLayout(out_row)
        out_layout.setContentsMargins(0, 0, 0, 0)
        out_input = QLineEdit("/path/to/output")
        out_browse = QPushButton("Browse...")
        out_browse.setProperty("class", "rk_browse")
        out_layout.addWidget(out_input)
        out_layout.addWidget(out_browse)
        io_layout.addRow("Output", out_row)

        main.addWidget(io_box)

        # Splat Options
        opts_box = QGroupBox("Splat Options")
        opts_grid = QGridLayout()
        opts_grid.setSpacing(12)

        opts_grid.addWidget(QLabel("Image size (px)"), 0, 0)
        opts_grid.addWidget(QSpinBox(), 0, 1)
        opts_grid.addWidget(QLabel("SH degree"), 0, 2)
        opts_grid.addWidget(QSpinBox(), 0, 3)

        opts_grid.addWidget(QLabel("Iterations"), 1, 0)
        opts_grid.addWidget(QSpinBox(), 1, 1)
        opts_grid.addWidget(QLabel("Densify until"), 1, 2)
        opts_grid.addWidget(QSpinBox(), 1, 3)

        opts_grid.addWidget(QLabel("Frame stride"), 2, 0)
        opts_grid.addWidget(QSpinBox(), 2, 1)
        opts_grid.addWidget(QLabel("Init points"), 2, 2)
        opts_grid.addWidget(QSpinBox(), 2, 3)

        opts_grid.addWidget(QCheckBox("Pre-decode SH → RGB"), 3, 0)
        opts_grid.addWidget(QCheckBox("Screen-space density gradients (2D)"), 3, 1, 1, 3)

        opts_box.setLayout(opts_grid)
        main.addWidget(opts_box)

        main.addStretch()

        # Primary action aligned right
        footer = QWidget()
        f_layout = QHBoxLayout(footer)
        f_layout.addStretch()
        run_btn = QPushButton("▷ Run Splat Pipeline")
        run_btn.setObjectName("rk_primary")
        f_layout.addWidget(run_btn)
        main.addWidget(footer)


class FolderSplatPage(QWidget):
    def __init__(self):
        super().__init__()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        main = QVBoxLayout(content)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(12)

        # Header
        header = QWidget()
        header.setObjectName("headerContainer")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 10)

        icon = QLabel("🖿")
        icon.setObjectName("headerIcon")
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignCenter)

        title_block = QWidget()
        t_layout = QVBoxLayout(title_block)
        t_layout.setContentsMargins(8, 0, 0, 0)
        t_layout.setSpacing(2)

        title = QLabel("Folder → Splat")
        title.setObjectName("pageTitle")
        desc = QLabel("Build a COLMAP reconstruction and Gaussian splat from a folder of photographs.")
        desc.setObjectName("pageDescription")

        t_layout.addWidget(title)
        t_layout.addWidget(desc)

        h_layout.addWidget(icon)
        h_layout.addWidget(title_block, 1)
        main.addWidget(header)

        # Input / Output group
        io_box = QGroupBox("Input / Output")
        io_layout = QFormLayout(io_box)

        ds_row = QWidget()
        ds_layout = QHBoxLayout(ds_row)
        ds_layout.setContentsMargins(0, 0, 0, 0)
        ds_input = QLineEdit("/path/to/folder/of/images")
        ds_browse = QPushButton("Browse ▾")
        ds_browse.setProperty("class", "rk_browse")
        ds_layout.addWidget(ds_input)
        ds_layout.addWidget(ds_browse)
        io_layout.addRow("Images folder", ds_row)

        out_row = QWidget()
        out_layout = QHBoxLayout(out_row)
        out_layout.setContentsMargins(0, 0, 0, 0)
        out_input = QLineEdit("/path/to/output")
        out_browse = QPushButton("Browse...")
        out_browse.setProperty("class", "rk_browse")
        out_layout.addWidget(out_input)
        out_layout.addWidget(out_browse)
        io_layout.addRow("Output folder", out_row)

        main.addWidget(io_box)

        # Pipeline Options box
        opts_box = QGroupBox("Pipeline Options")
        opts_grid = QGridLayout()
        opts_grid.setSpacing(12)

        output_format = QComboBox()
        output_format.addItems(["x3d", "ply", "splat", "glb"])
        output_format.setCurrentText("x3d")

        matcher = QComboBox()
        matcher.addItems(["Exhaustive — hloc (SfM)", "Sequential — hloc (SfM)", "Vocabulary tree"])
        matcher.setCurrentText("Exhaustive — hloc (SfM)")

        opts_grid.addWidget(QLabel("Output format"), 0, 0)
        opts_grid.addWidget(output_format, 0, 1)
        opts_grid.addWidget(QLabel("COLMAP matcher"), 0, 2)
        opts_grid.addWidget(matcher, 0, 3)

        opts_grid.addWidget(QLabel("Focal length (px)"), 1, 0)
        opts_grid.addWidget(QSpinBox(), 1, 1)
        opts_grid.addWidget(QLabel("Image size (px)"), 1, 2)
        opts_grid.addWidget(QSpinBox(), 1, 3)

        opts_grid.addWidget(QLabel("SH degree"), 2, 0)
        opts_grid.addWidget(QSpinBox(), 2, 1)
        opts_grid.addWidget(QLabel("Iterations"), 2, 2)
        opts_grid.addWidget(QSpinBox(), 2, 3)

        opts_box.setLayout(opts_grid)
        main.addWidget(opts_box)

        # Advanced Training Options
        adv = QGroupBox("Advanced Training Options")
        adv_layout = QGridLayout(adv)
        adv_layout.setSpacing(12)

        densify_until = QSpinBox()
        opacity_reset = QSpinBox()
        densify_every = QSpinBox()
        grad_threshold = QDoubleSpinBox()
        frame_stride = QSpinBox()

        adv_layout.addWidget(QLabel("Densify until"), 0, 0)
        adv_layout.addWidget(densify_until, 0, 1)
        adv_layout.addWidget(QLabel("Opacity reset (steps)"), 0, 2)
        adv_layout.addWidget(opacity_reset, 0, 3)

        adv_layout.addWidget(QLabel("Densify every (steps)"), 1, 0)
        adv_layout.addWidget(densify_every, 1, 1)
        adv_layout.addWidget(QLabel("Grad threshold"), 1, 2)
        adv_layout.addWidget(grad_threshold, 1, 3)

        adv_layout.addWidget(QLabel("Frame stride"), 2, 0)
        adv_layout.addWidget(frame_stride, 2, 1)

        adv_row = QWidget()
        adv_row_layout = QHBoxLayout(adv_row)
        adv_row_layout.setContentsMargins(0, 0, 0, 0)
        adv_row_layout.addWidget(QCheckBox("Pre-decode SH → RGB"))
        adv_row_layout.addStretch()
        adv_row_layout.addWidget(QCheckBox("Screen-space density gradients (2D)"))
        adv_layout.addWidget(adv_row, 3, 0, 1, 4)

        main.addWidget(adv)

        # Turntable capture
        turntable = QGroupBox("Turntable Capture")
        turn_layout = QVBoxLayout(turntable)
        turn_layout.setContentsMargins(10, 10, 10, 10)

        turn_mode = QCheckBox("Turntable mode")
        turn_mode.setChecked(False)
        turn_layout.addWidget(turn_mode)
        turn_layout.addWidget(QLabel("Use synthetic circular poses for object-on-turntable captures."))

        turn_params = QWidget()
        turn_params_layout = QGridLayout(turn_params)
        turn_params_layout.setContentsMargins(0, 0, 0, 0)
        turn_params_layout.setSpacing(12)

        turntable_sets = QSpinBox()
        elevation = QDoubleSpinBox()
        radius = QDoubleSpinBox()

        turn_params_layout.addWidget(QLabel("Turntable sets"), 0, 0)
        turn_params_layout.addWidget(turntable_sets, 0, 1)
        turn_params_layout.addWidget(QLabel("Elevation override (°)"), 0, 2)
        turn_params_layout.addWidget(elevation, 0, 3)

        turn_params_layout.addWidget(QLabel("Radius override (m)"), 1, 0)
        turn_params_layout.addWidget(radius, 1, 1)

        turn_layout.addWidget(turn_params)
        main.addWidget(turntable)

        # Background masking
        masking = QGroupBox("Background Masking")
        mask_layout = QVBoxLayout(masking)
        mask_layout.setContentsMargins(10, 10, 10, 10)

        mask_folder_row = QWidget()
        mask_folder_layout = QHBoxLayout(mask_folder_row)
        mask_folder_layout.setContentsMargins(0, 0, 0, 0)
        mask_folder_layout.addWidget(QLabel("Mask folder"))
        mask_folder_layout.addStretch()
        mask_input = QLineEdit("Auto-detect masks/ subfolder, or browse...")
        mask_folder_layout.addWidget(mask_input)
        mask_browse = QPushButton("Browse...")
        mask_browse.setProperty("class", "rk_browse")
        mask_folder_layout.addWidget(mask_browse)
        mask_layout.addWidget(mask_folder_row)

        mask_flags = QWidget()
        mask_flags_layout = QGridLayout(mask_flags)
        mask_flags_layout.setContentsMargins(0, 0, 0, 0)
        mask_flags_layout.setSpacing(12)

        auto_mask = QCheckBox("Auto-mask with rembg")
        edge_erosion = QSpinBox()
        chroma_key = QCheckBox("Chroma-key color")
        chroma_tolerance = QSpinBox()

        mask_flags_layout.addWidget(auto_mask, 0, 0)
        mask_flags_layout.addWidget(QLabel("Edge erosion (px)"), 0, 2)
        mask_flags_layout.addWidget(edge_erosion, 0, 3)

        mask_flags_layout.addWidget(chroma_key, 1, 0)
        mask_flags_layout.addWidget(QLabel("Tolerance"), 1, 2)
        mask_flags_layout.addWidget(chroma_tolerance, 1, 3)

        mask_layout.addWidget(mask_flags)

        colmap_only = QCheckBox("COLMAP + masks only")
        colmap_only.setChecked(False)
        mask_layout.addWidget(colmap_only)

        main.addWidget(masking)
        main.addStretch()

        footer = QWidget()
        f_layout = QHBoxLayout(footer)
        f_layout.addStretch()
        run_btn = QPushButton("▷ Run (COLMAP → 3DGS)")
        run_btn.setObjectName("rk_primary")
        f_layout.addWidget(run_btn)
        main.addWidget(footer)

        scroll.setWidget(content)
        outer.addWidget(scroll)


class ConvertSplatPage(QWidget):
    def __init__(self):
        super().__init__()
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QWidget()
        header.setObjectName("headerContainer")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 10)

        icon = QLabel("⇄")
        icon.setObjectName("headerIcon")
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignCenter)

        title_block = QWidget()
        t_layout = QVBoxLayout(title_block)
        t_layout.setContentsMargins(8, 0, 0, 0)
        t_layout.setSpacing(2)

        title = QLabel("Convert Splat")
        title.setObjectName("pageTitle")
        desc = QLabel("Convert an existing Gaussian splat between supported interchange formats.")
        desc.setObjectName("pageDescription")

        t_layout.addWidget(title)
        t_layout.addWidget(desc)

        h_layout.addWidget(icon)
        h_layout.addWidget(title_block, 1)
        main.addWidget(header)

        # Input / Output group
        io_box = QGroupBox("Input / Output")
        io_layout = QFormLayout(io_box)

        in_row = QWidget()
        in_layout = QHBoxLayout(in_row)
        in_layout.setContentsMargins(0, 0, 0, 0)
        in_input = QLineEdit("source.ply / source.splat / source.glb / source.x3d ...")
        in_browse = QPushButton("Browse...")
        in_browse.setProperty("class", "rk_browse")
        in_layout.addWidget(in_input)
        in_layout.addWidget(in_browse)
        io_layout.addRow("Input file", in_row)

        out_row = QWidget()
        out_layout = QHBoxLayout(out_row)
        out_layout.setContentsMargins(0, 0, 0, 0)
        out_input = QLineEdit("/path/to/output")
        out_browse = QPushButton("Browse...")
        out_browse.setProperty("class", "rk_browse")
        out_layout.addWidget(out_input)
        out_layout.addWidget(out_browse)
        io_layout.addRow("Output folder", out_row)

        out_stem = QLineEdit("filename without extension (auto-filled from input)")
        io_layout.addRow("Output stem", out_stem)

        main.addWidget(io_box)

        # Convert Options
        opts_box = QGroupBox("Convert Options")
        opts_grid = QGridLayout()
        opts_grid.setSpacing(12)

        opts_grid.addWidget(QLabel("Target format"), 0, 0)
        opts_grid.addWidget(QLineEdit("x3d"), 0, 1)
        opts_grid.addWidget(QLabel("SH degree"), 0, 2)
        opts_grid.addWidget(QSpinBox(), 0, 3)

        opts_grid.addWidget(QLabel("Pre-decode SH → RGB"), 1, 0)
        opts_grid.addWidget(QCheckBox(), 1, 1)
        opts_grid.addWidget(QLabel("Maximum splats"), 1, 2)
        opts_grid.addWidget(QSpinBox(), 1, 3)

        opts_box.setLayout(opts_grid)
        main.addWidget(opts_box)

        main.addStretch()

        footer = QWidget()
        f_layout = QHBoxLayout(footer)
        f_layout.addStretch()
        run_btn = QPushButton("Convert")
        run_btn.setObjectName("rk_primary")
        f_layout.addWidget(run_btn)
        main.addWidget(footer)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    apply_theme(app)
    w = RawKeeMainWindow()
    w.show()
    sys.exit(app.exec())
