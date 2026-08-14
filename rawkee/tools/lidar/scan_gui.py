"""Desktop GUI for the rawkee scan pipelines (mesh + Gaussian splat).

Requires: PySide6  (pip install PySide6)
Run:      python scan_gui.py
"""
from __future__ import annotations
import logging
import sys
from pathlib import Path

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QTabWidget,
        QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QLineEdit, QPushButton, QComboBox,
        QCheckBox, QSpinBox, QGroupBox,
        QFileDialog, QTextEdit, QSizePolicy, QMessageBox, QMenu,
    )
    from PySide6.QtCore import QThread, Signal, Qt
    from PySide6.QtGui import QFont, QTextCursor
except ImportError:
    print('PySide6 is required: pip install PySide6')
    sys.exit(1)


# ---------------------------------------------------------------------------
# Logging → Qt text widget bridge
# ---------------------------------------------------------------------------

class _QtLogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self._signal = signal

    def emit(self, record):
        self._signal.emit(self.format(record))


# ---------------------------------------------------------------------------
# Background worker thread
# ---------------------------------------------------------------------------

class _PipelineWorker(QThread):
    log_line  = Signal(str)
    finished  = Signal(bool, str)   # success, message

    def __init__(self, mode: str, kwargs: dict):
        super().__init__()
        self._mode   = mode
        self._kwargs = kwargs

    def run(self):
        handler = _QtLogHandler(self.log_line)
        handler.setFormatter(logging.Formatter('%(levelname)s %(name)s %(message)s'))
        root_log = logging.getLogger()
        root_log.addHandler(handler)
        root_log.setLevel(logging.INFO)
        try:
            from rawkee.tools.lidar import ScanDataset, MeshPipeline, SplatPipeline
            kw = self._kwargs

            dataset = ScanDataset(kw['dataset'], platform=kw['platform'])

            # Georeferencing: apply before pipeline if CSV given and not suppressed
            effective_csv = _resolve_georef_csv(kw.get('trimble_csv'), kw.get('no_georef', False))

            if self._mode == 'mesh':
                out = MeshPipeline(
                    poisson_depth        = kw['poisson_depth'],
                    atlas_size           = kw['atlas_size'],
                    colorise_stride      = kw['colorise_stride'],
                ).run(
                    dataset,
                    output_dir    = kw['output'],
                    output_format = kw['fmt'],
                    hdri_frame    = kw.get('hdri_frame'),
                    envmap_width  = kw['envmap_width'],
                    envmap_height = kw['envmap_height'],
                    trimble_csv   = effective_csv,
                    georef_epsg   = kw['epsg'],
                )
            else:
                out = SplatPipeline(
                    image_size   = kw['image_size'],
                    sh_degree    = kw['sh_degree'],
                    iterations   = kw['iterations'],
                    frame_stride = kw['frame_stride'],
                    init_points  = kw['init_points'],
                ).run(
                    dataset,
                    output_dir    = kw['output'],
                    output_format = kw['fmt'],
                    trimble_csv   = effective_csv,
                    georef_epsg   = kw['epsg'],
                    decode_sh     = kw.get('decode_sh', False),
                )
            self.finished.emit(True, str(out))
        except Exception as exc:
            import traceback
            self.log_line.emit('ERROR: ' + traceback.format_exc())
            self.finished.emit(False, str(exc))
        finally:
            root_log.removeHandler(handler)


def _resolve_georef_csv(trimble_csv: str | None, no_georef: bool) -> Path | None:
    """Return Path to Trimble CSV, or None with a warning if unavailable."""
    if no_georef or not trimble_csv:
        return None
    p = Path(trimble_csv)
    if not p.exists():
        logging.getLogger(__name__).warning(
            'Trimble CSV not found: %s — proceeding without georeferencing', p
        )
        return None
    return p


# ---------------------------------------------------------------------------
# Reusable widgets
# ---------------------------------------------------------------------------

def _folder_row(label: str, placeholder: str) -> tuple[QLabel, QLineEdit, QPushButton]:
    lbl  = QLabel(label)
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    btn  = QPushButton('Browse…')
    return lbl, edit, btn


# _file_row is an alias; both open a file dialog depending on caller context
_file_row = _folder_row


# ---------------------------------------------------------------------------
# Shared options group (georef + format + platform)
# ---------------------------------------------------------------------------

class _SharedOptions(QGroupBox):
    def __init__(self):
        super().__init__('Common Options')
        g = QGridLayout(self)
        row = 0

        # Platform
        g.addWidget(QLabel('Platform'), row, 0)
        self.platform = QComboBox()
        self.platform.addItems(['auto', 'navvis', 'metashape', 'meshroom', 'pix4d', 'colmap', 'e57'])
        self.platform.setEditable(True)
        self.platform.setToolTip('auto = detected from the dataset path')
        g.addWidget(self.platform, row, 1)
        row += 1

        # Format
        g.addWidget(QLabel('Output format'), row, 0)
        self.fmt = QComboBox()
        g.addWidget(self.fmt, row, 1)
        row += 1

        # Trimble CSV
        g.addWidget(QLabel('Trimble CSV'), row, 0)
        self.trimble_edit = QLineEdit()
        self.trimble_edit.setPlaceholderText('Optional — for georeferencing')
        g.addWidget(self.trimble_edit, row, 1)
        self.trimble_btn = QPushButton('Browse CSV…')
        g.addWidget(self.trimble_btn, row, 2)
        row += 1

        # No-georef override
        self.no_georef = QCheckBox('Skip georeferencing (even if CSV is set)')
        g.addWidget(self.no_georef, row, 0, 1, 3)
        row += 1

        # EPSG
        g.addWidget(QLabel('EPSG code'), row, 0)
        self.epsg = QSpinBox()
        self.epsg.setRange(1024, 99999)
        self.epsg.setValue(32605)
        self.epsg.setToolTip('Projected CRS for georeferencing (32605 = UTM Zone 5N)')
        g.addWidget(self.epsg, row, 1)
        row += 1

        self.trimble_btn.clicked.connect(self._browse_csv)

    def _browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select Trimble CSV', '', 'CSV files (*.csv);;All files (*)')
        if path:
            self.trimble_edit.setText(path)

    def set_formats(self, formats: list[str]):
        self.fmt.clear()
        self.fmt.addItems(formats)


# ---------------------------------------------------------------------------
# Mesh tab
# ---------------------------------------------------------------------------

class _MeshTab(QWidget):
    def __init__(self, shared: _SharedOptions, log_widget: QTextEdit):
        super().__init__()
        self._shared = shared
        self._log    = log_widget
        self._worker = None
        layout = QVBoxLayout(self)

        # Dataset + output
        io_box = QGroupBox('Input / Output')
        g = QGridLayout(io_box)
        _, self.ds_edit, ds_btn = _folder_row('Dataset', '/path/to/navvis-folder  or  project.psx')
        _, self.out_edit, out_btn = _folder_row('Output folder', '/path/to/output')
        ds_menu = QMenu(ds_btn)
        ds_menu.addAction('Browse Folder…',        lambda: self._browse_dataset_folder())
        ds_menu.addAction('Browse .psx File…',     lambda: self._browse_dataset_psx())
        ds_menu.addAction('Browse .mg File…',      lambda: self._browse_dataset_mg())
        ds_menu.addAction('Browse .p4d File…',     lambda: self._browse_dataset_p4d())
        ds_menu.addAction('Browse .e57 File…',     lambda: self._browse_dataset_e57())
        ds_menu.addAction('Browse COLMAP Folder…', lambda: self._browse_dataset_colmap())
        ds_btn.setMenu(ds_menu)
        ds_btn.setText('Browse ▾')
        g.addWidget(QLabel('Dataset'), 0, 0); g.addWidget(self.ds_edit, 0, 1); g.addWidget(ds_btn, 0, 2)
        g.addWidget(QLabel('Output'),  1, 0); g.addWidget(self.out_edit, 1, 1); g.addWidget(out_btn, 1, 2)
        out_btn.clicked.connect(lambda: self._browse_output_folder())
        layout.addWidget(io_box)
        opt_box = QGroupBox('Mesh Options')
        g2 = QGridLayout(opt_box)
        self.poisson_depth   = self._spin(g2, 0, 'Poisson depth',    9,  4, 13)
        self.atlas_size      = self._spin(g2, 1, 'Atlas size (px)',   4096, 512, 16384, step=512)
        self.colorise_stride = self._spin(g2, 2, 'Colorise stride',   10, 1, 50)
        self.envmap_w        = self._spin(g2, 3, 'Envmap width',      4096, 512, 8192, step=512)
        self.envmap_h        = self._spin(g2, 4, 'Envmap height',     2048, 256, 4096, step=256)
        layout.addWidget(opt_box)

        self.run_btn = QPushButton('Run Mesh Pipeline')
        self.run_btn.setFixedHeight(36)
        self.run_btn.clicked.connect(self._run)
        layout.addWidget(self.run_btn)
        layout.addStretch()

        shared.set_formats(['x3d', 'x3dv', 'x3dj', 'obj', 'glb'])

    def _spin(self, grid, row, label, default, lo, hi, step=1):
        grid.addWidget(QLabel(label), row, 0)
        w = QSpinBox()
        w.setRange(lo, hi)
        w.setValue(default)
        w.setSingleStep(step)
        grid.addWidget(w, row, 1)
        return w

    def _browse_dataset_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Select NavVis dataset folder')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText(self._auto_detect(path))

    def _browse_dataset_psx(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select Metashape project', '', 'Metashape Projects (*.psx);;All files (*)')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText('metashape')

    def _browse_dataset_mg(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select Meshroom project', '', 'Meshroom Projects (*.mg);;All files (*)')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText('meshroom')

    def _browse_dataset_p4d(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select Pix4D project', '', 'Pix4D Projects (*.p4d);;All files (*)')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText('pix4d')

    def _browse_dataset_e57(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select E57 point cloud', '', 'E57 Files (*.e57);;All files (*)')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText('e57')

    def _browse_dataset_colmap(self):
        path = QFileDialog.getExistingDirectory(self, 'Select COLMAP sparse reconstruction folder')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText('colmap')

    def _browse_output_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Select output folder')
        if path:
            self.out_edit.setText(path)

    @staticmethod
    def _auto_detect(path: str) -> str:
        try:
            from rawkee.tools.lidar.dataset import _detect_platform
            return _detect_platform(path)
        except Exception:
            return 'auto'

    def _browse_folder(self, edit):
        path = QFileDialog.getExistingDirectory(self, 'Select folder')
        if path:
            edit.setText(path)

    def _run(self):
        if not self.ds_edit.text() or not self.out_edit.text():
            QMessageBox.warning(self, 'Missing paths', 'Dataset and output folders are required.')
            return
        s = self._shared
        kw = dict(
            dataset        = self.ds_edit.text(),
            output         = self.out_edit.text(),
            platform       = s.platform.currentText(),
            fmt            = s.fmt.currentText(),
            trimble_csv    = s.trimble_edit.text() or None,
            no_georef      = s.no_georef.isChecked(),
            epsg           = s.epsg.value(),
            poisson_depth  = self.poisson_depth.value(),
            atlas_size     = self.atlas_size.value(),
            colorise_stride= self.colorise_stride.value(),
            envmap_width   = self.envmap_w.value(),
            envmap_height  = self.envmap_h.value(),
        )
        self._start_worker('mesh', kw)

    def _start_worker(self, mode, kw):
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(2000)
        self.run_btn.setEnabled(False)
        self._log.clear()
        self._worker = _PipelineWorker(mode, kw)
        self._worker.log_line.connect(self._append_log)
        self._worker.finished.connect(self._done)
        self._worker.start()

    def _append_log(self, text):
        self._log.append(text)
        self._log.moveCursor(QTextCursor.End)

    def _done(self, ok, msg):
        self.run_btn.setEnabled(True)
        if ok:
            QMessageBox.information(self, 'Done', f'Output written to:\n{msg}')
        else:
            QMessageBox.critical(self, 'Pipeline error', msg)


# ---------------------------------------------------------------------------
# Splat tab
# ---------------------------------------------------------------------------

class _SplatTab(QWidget):
    def __init__(self, shared: _SharedOptions, log_widget: QTextEdit):
        super().__init__()
        self._shared = shared
        self._log    = log_widget
        self._worker = None
        layout = QVBoxLayout(self)

        io_box = QGroupBox('Input / Output')
        g = QGridLayout(io_box)
        _, self.ds_edit, ds_btn = _folder_row('Dataset', '/path/to/navvis-folder  or  project.psx')
        _, self.out_edit, out_btn = _folder_row('Output folder', '/path/to/output')
        ds_menu = QMenu(ds_btn)
        ds_menu.addAction('Browse Folder…',        lambda: self._browse_dataset_folder())
        ds_menu.addAction('Browse .psx File…',     lambda: self._browse_dataset_psx())
        ds_menu.addAction('Browse .mg File…',      lambda: self._browse_dataset_mg())
        ds_menu.addAction('Browse .p4d File…',     lambda: self._browse_dataset_p4d())
        ds_menu.addAction('Browse .e57 File…',     lambda: self._browse_dataset_e57())
        ds_menu.addAction('Browse COLMAP Folder…', lambda: self._browse_dataset_colmap())
        ds_btn.setMenu(ds_menu)
        ds_btn.setText('Browse ▾')
        g.addWidget(QLabel('Dataset'), 0, 0); g.addWidget(self.ds_edit, 0, 1); g.addWidget(ds_btn, 0, 2)
        g.addWidget(QLabel('Output'),  1, 0); g.addWidget(self.out_edit, 1, 1); g.addWidget(out_btn, 1, 2)
        out_btn.clicked.connect(lambda: self._browse_output_folder())
        layout.addWidget(io_box)

        opt_box = QGroupBox('Splat Options')
        g2 = QGridLayout(opt_box)
        self.image_size   = self._spin(g2, 0, 'Image size (px)',   512,  64,  2048, step=64)
        self.sh_degree    = self._spin(g2, 1, 'SH degree',         3,    0,   3)
        self.iterations   = self._spin(g2, 2, 'Iterations',        10000, 100, 100000, step=1000)
        self.frame_stride = self._spin(g2, 3, 'Frame stride',      5,    1,   20)
        self.init_points  = self._spin(g2, 4, 'Init points',       100000, 1000, 1000000, step=10000)
        self.decode_sh    = QCheckBox('Pre-decode SH → RGB in PLY output')
        self.decode_sh.setToolTip(
            'Enable for PLY consumers that do not implement SH decoding.\n'
            'Has no effect for non-PLY formats.'
        )
        g2.addWidget(self.decode_sh, 5, 0, 1, 2)
        layout.addWidget(opt_box)

        self.run_btn = QPushButton('Run Splat Pipeline')
        self.run_btn.setFixedHeight(36)
        self.run_btn.clicked.connect(self._run)
        layout.addWidget(self.run_btn)
        layout.addStretch()

        shared.set_formats(['x3d', 'x3dv', 'x3dj', 'ply', 'splat', 'glb'])

    def _spin(self, grid, row, label, default, lo, hi, step=1):
        grid.addWidget(QLabel(label), row, 0)
        w = QSpinBox()
        w.setRange(lo, hi)
        w.setValue(default)
        w.setSingleStep(step)
        grid.addWidget(w, row, 1)
        return w

    def _browse_dataset_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Select NavVis dataset folder')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText(self._auto_detect(path))

    def _browse_dataset_psx(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select Metashape project', '', 'Metashape Projects (*.psx);;All files (*)')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText('metashape')

    def _browse_dataset_mg(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select Meshroom project', '', 'Meshroom Projects (*.mg);;All files (*)')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText('meshroom')

    def _browse_dataset_p4d(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select Pix4D project', '', 'Pix4D Projects (*.p4d);;All files (*)')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText('pix4d')

    def _browse_dataset_e57(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select E57 point cloud', '', 'E57 Files (*.e57);;All files (*)')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText('e57')

    def _browse_dataset_colmap(self):
        path = QFileDialog.getExistingDirectory(self, 'Select COLMAP sparse reconstruction folder')
        if path:
            self.ds_edit.setText(path)
            self._shared.platform.setCurrentText('colmap')

    def _browse_output_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Select output folder')
        if path:
            self.out_edit.setText(path)

    @staticmethod
    def _auto_detect(path: str) -> str:
        try:
            from rawkee.tools.lidar.dataset import _detect_platform
            return _detect_platform(path)
        except Exception:
            return 'auto'

    def _browse_folder(self, edit):
        path = QFileDialog.getExistingDirectory(self, 'Select folder')
        if path:
            edit.setText(path)

    def _run(self):
        if not self.ds_edit.text() or not self.out_edit.text():
            QMessageBox.warning(self, 'Missing paths', 'Dataset and output folders are required.')
            return
        s = self._shared
        kw = dict(
            dataset       = self.ds_edit.text(),
            output        = self.out_edit.text(),
            platform      = s.platform.currentText(),
            fmt           = s.fmt.currentText(),
            trimble_csv   = s.trimble_edit.text() or None,
            no_georef     = s.no_georef.isChecked(),
            epsg          = s.epsg.value(),
            image_size    = self.image_size.value(),
            sh_degree     = self.sh_degree.value(),
            iterations    = self.iterations.value(),
            frame_stride  = self.frame_stride.value(),
            init_points   = self.init_points.value(),
            decode_sh     = self.decode_sh.isChecked(),
        )
        self._start_worker('splat', kw)

    def _start_worker(self, mode, kw):
        self.run_btn.setEnabled(False)
        self._log.clear()
        self._worker = _PipelineWorker(mode, kw)
        self._worker.log_line.connect(self._append_log)
        self._worker.finished.connect(self._done)
        self._worker.start()

    def _append_log(self, text):
        self._log.append(text)
        self._log.moveCursor(QTextCursor.End)

    def _done(self, ok, msg):
        self.run_btn.setEnabled(True)
        if ok:
            QMessageBox.information(self, 'Done', f'Output written to:\n{msg}')
        else:
            QMessageBox.critical(self, 'Pipeline error', msg)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class ScanPipelineApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('rawkee — Scan Pipeline')
        self.resize(680, 720)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(8)

        # Shared options (georef, format, platform) — lives above the tabs
        self._shared = _SharedOptions()
        root.addWidget(self._shared)

        # Log output — shared between both tabs
        log_box = QGroupBox('Log')
        log_layout = QVBoxLayout(log_box)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont('Courier New', 9))
        self._log.setMinimumHeight(160)
        log_layout.addWidget(self._log)
        root.addWidget(log_box)

        # Pipeline tabs
        tabs = QTabWidget()
        tabs.addTab(_MeshTab(self._shared, self._log),  'Mesh')
        tabs.addTab(_SplatTab(self._shared, self._log), 'Gaussian Splat')
        root.insertWidget(1, tabs)   # insert between shared options and log


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = ScanPipelineApp()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
