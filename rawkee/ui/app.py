"""Compact RawKee Scan Studio shell implementation.

This lighter implementation keeps the same public API required by the
story while avoiding excess code that previously caused accidental
duplication in the file during edits.
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
    QSizePolicy,
    QLineEdit,
    QFormLayout,
    QGridLayout,
    QSpinBox,
    QGroupBox,
    QCheckBox,
)

from .theme import apply_theme


class RawKeeMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RawKee Scan Studio")
        self.resize(1100, 750)

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
        for name, icon in [("Mesh","⛶"),("Gaussian Splat","⁕"),("Folder → Splat","📂"),("Convert Splat","⇄")]:
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
        dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        console = QTextEdit()
        console.setReadOnly(True)
        console.setLineWrapMode(QTextEdit.NoWrap)
        console.append("Ready to process scan data.")
        dock.setWidget(console)
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
        self._console.append(message)

    def update_status(self, status_text: str, activity_state: str = "Idle") -> None:
        self._status_label.setText(status_text)
        self._activity_label.setText(activity_state)


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
        io_box = QWidget()
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
        opts = QWidget()
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

        opts_box.setLayout(opts_grid)
        main.addWidget(opts_box)

        # Checkboxes row
        cb_row = QWidget()
        cb_layout = QHBoxLayout(cb_row)
        cb_layout.addWidget(QCheckBox("Pre-decode SH → RGB"))
        cb_layout.addStretch()
        cb_layout.addWidget(QCheckBox("Screen-space density gradients (2D)"))
        main.addWidget(cb_row)

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
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QWidget()
        header.setObjectName("headerContainer")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 10)

        icon = QLabel("📂")
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

        opts_grid.addWidget(QLabel("Output format"), 0, 0)
        opts_grid.addWidget(QLineEdit("x3d"), 0, 1)
        opts_grid.addWidget(QLabel("COLMAP matcher"), 0, 2)
        opts_grid.addWidget(QLineEdit("Exhaustive — hloc (SfM)"), 0, 3)

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

        # Advanced box placeholder
        adv = QGroupBox("Advanced Training Options")
        adv_layout = QVBoxLayout(adv)
        adv_layout.addWidget(QLabel("(advanced options placeholder)"))
        main.addWidget(adv)

        main.addStretch()

        footer = QWidget()
        f_layout = QHBoxLayout(footer)
        f_layout.addStretch()
        run_btn = QPushButton("▷ Run (COLMAP → 3DGS)")
        run_btn.setObjectName("rk_primary")
        f_layout.addWidget(run_btn)
        main.addWidget(footer)


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
