"""Desktop GUI for the RawKee Lidar and Scan Pipelines (mesh + Gaussian splat).

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
        QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox,
        QFileDialog, QTextEdit, QSizePolicy, QMessageBox, QMenu,
        QProgressBar,
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
                    max_packets          = kw['max_packets'],
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
            elif self._mode == 'splat':
                out = SplatPipeline(
                    image_size   = kw['image_size'],
                    sh_degree    = kw['sh_degree'],
                    iterations   = kw['iterations'],
                    frame_stride = kw['frame_stride'],
                    init_points  = kw['init_points'],
                ).run(
                    dataset,
                    output_dir       = kw['output'],
                    output_format    = kw['fmt'],
                    trimble_csv      = effective_csv,
                    georef_epsg      = kw['epsg'],
                    decode_sh        = kw.get('decode_sh', False),
                    densify_grad_mode = kw.get('grad_mode', '2d'),
                    densify_until    = kw.get('densify_until') or -1,
                )
            self.finished.emit(True, str(out))
        except Exception as exc:
            import traceback
            self.log_line.emit('ERROR: ' + traceback.format_exc())
            self.finished.emit(False, str(exc))
        finally:
            root_log.removeHandler(handler)


class _ConvertWorker(QThread):
    log_line = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, kwargs: dict):
        super().__init__()
        self._kw = kwargs

    def run(self):
        handler = _QtLogHandler(self.log_line)
        handler.setFormatter(logging.Formatter('%(levelname)s %(name)s %(message)s'))
        root_log = logging.getLogger()
        root_log.addHandler(handler)
        root_log.setLevel(logging.INFO)
        try:
            from rawkee.tools.lidar import convert_splat
            kw  = self._kw
            out = convert_splat(
                input_path = kw['input'],
                output_dir = kw['output'],
                stem       = kw['stem'],
                fmt        = kw['fmt'],
                sh_degree  = kw.get('sh_degree'),
                decode_sh  = kw.get('decode_sh', False),
                max_splats = kw.get('max_splats'),
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
        self.max_packets     = self._spin(g2, 3, 'Max LiDAR pkts',  6000, 100, 500000, step=1000)
        self.envmap_w        = self._spin(g2, 4, 'Envmap width',    4096, 512, 8192,  step=512)
        self.envmap_h        = self._spin(g2, 5, 'Envmap height',   2048, 256, 4096,  step=256)
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
            max_packets    = self.max_packets.value(),
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
            QMessageBox.critical(self, 'Pipeline error', msg[:400])


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
        self.image_size    = self._spin(g2, 0, 'Image size (px)',   1024,  64,  4096, step=64)
        self.sh_degree     = self._spin(g2, 1, 'SH degree',         3,    0,   3)
        self.iterations    = self._spin(g2, 2, 'Iterations',        30000, 100, 200000, step=1000)
        self.densify_until = self._spin(g2, 3, 'Densify until',     0,    0,   200000, step=1000)
        self.densify_until.setToolTip(
            '0 = auto (half of Iterations).\n'
            'Set explicitly for long outdoor runs:\n'
            '  Room/indoor:   20 000–30 000\n'
            '  Building:      30 000–50 000\n'
            '  Large outdoor: 50 000+'
        )
        self.frame_stride  = self._spin(g2, 4, 'Frame stride',      5,    1,   20)
        self.init_points   = self._spin(g2, 5, 'Init points',       100000, 1000, 1000000, step=10000)
        self.decode_sh    = QCheckBox('Pre-decode SH → RGB in PLY output')
        self.decode_sh.setToolTip(
            'Enable for PLY consumers that do not implement SH decoding.\n'
            'Has no effect for non-PLY formats.'
        )
        g2.addWidget(self.decode_sh, 6, 0, 1, 2)

        self.grad_mode_2d = QCheckBox('Screen-space density gradients (2D) — recommended')
        self.grad_mode_2d.setChecked(True)
        self.grad_mode_2d.setToolTip(
            'Use 2D screen-space gradients for density control (Kerbl et al. 2023).\n'
            'More robust than 3D world-space gradients, especially for masked training.\n'
            'Uncheck to fall back to 3D gradients (useful for debugging).'
        )
        g2.addWidget(self.grad_mode_2d, 7, 0, 1, 2)
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
            densify_until = self.densify_until.value() or None,
            frame_stride  = self.frame_stride.value(),
            init_points   = self.init_points.value(),
            decode_sh     = self.decode_sh.isChecked(),
            grad_mode     = '2d' if self.grad_mode_2d.isChecked() else '3d',
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
            QMessageBox.critical(self, 'Pipeline error', msg[:400])


# ---------------------------------------------------------------------------
# Convert tab
# ---------------------------------------------------------------------------

class _ConvertTab(QWidget):
    def __init__(self, log_widget: QTextEdit):
        super().__init__()
        self._log    = log_widget
        self._worker = None
        layout = QVBoxLayout(self)

        io_box = QGroupBox('Input / Output')
        g = QGridLayout(io_box)

        g.addWidget(QLabel('Input file'), 0, 0)
        self.in_edit = QLineEdit()
        self.in_edit.setPlaceholderText('source.ply  /  source.splat  /  source.glb  /  source.x3d …')
        self.in_edit.textChanged.connect(self._auto_stem)
        g.addWidget(self.in_edit, 0, 1)
        in_btn = QPushButton('Browse…')
        in_btn.clicked.connect(self._browse_input)
        g.addWidget(in_btn, 0, 2)

        g.addWidget(QLabel('Output folder'), 1, 0)
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText('/path/to/output')
        g.addWidget(self.out_edit, 1, 1)
        out_btn = QPushButton('Browse…')
        out_btn.clicked.connect(self._browse_output)
        g.addWidget(out_btn, 1, 2)

        g.addWidget(QLabel('Output stem'), 2, 0)
        self.stem_edit = QLineEdit()
        self.stem_edit.setPlaceholderText('filename without extension (auto-filled from input)')
        g.addWidget(self.stem_edit, 2, 1, 1, 2)
        layout.addWidget(io_box)

        opt_box = QGroupBox('Convert Options')
        g2 = QGridLayout(opt_box)

        g2.addWidget(QLabel('Target format'), 0, 0)
        self.fmt = QComboBox()
        self.fmt.addItems(['x3d', 'x3dv', 'x3dj', 'ply', 'splat', 'glb'])
        g2.addWidget(self.fmt, 0, 1)

        g2.addWidget(QLabel('SH degree'), 1, 0)
        sh_row = QHBoxLayout()
        self.sh_auto = QCheckBox('Match source')
        self.sh_auto.setChecked(True)
        self.sh_auto.toggled.connect(lambda on: self.sh_degree.setEnabled(not on))
        self.sh_degree = QSpinBox()
        self.sh_degree.setRange(0, 3)
        self.sh_degree.setValue(3)
        self.sh_degree.setEnabled(False)
        sh_row.addWidget(self.sh_auto)
        sh_row.addWidget(self.sh_degree)
        sh_row.addStretch()
        g2.addLayout(sh_row, 1, 1)

        self.decode_sh = QCheckBox('Pre-decode SH → RGB (for viewers without SH decoding)')
        g2.addWidget(self.decode_sh, 2, 0, 1, 2)

        g2.addWidget(QLabel('Max splats'), 3, 0)
        max_row = QHBoxLayout()
        self.max_splats_enable = QCheckBox('Limit to')
        self.max_splats_enable.setChecked(True)
        self.max_splats = QSpinBox()
        self.max_splats.setRange(1_000, 10_000_000)
        self.max_splats.setSingleStep(50_000)
        self.max_splats.setValue(500_000)
        self.max_splats.setSuffix('  splats')
        self.max_splats.setGroupSeparatorShown(True)
        self.max_splats_enable.toggled.connect(self.max_splats.setEnabled)
        max_row.addWidget(self.max_splats_enable)
        max_row.addWidget(self.max_splats)
        max_row.addStretch()
        g2.addLayout(max_row, 3, 1)
        layout.addWidget(opt_box)

        self.run_btn = QPushButton('Convert')
        self.run_btn.setFixedHeight(36)
        self.run_btn.clicked.connect(self._run)
        layout.addWidget(self.run_btn)

        self.spinner = QProgressBar()
        self.spinner.setRange(0, 0)   # indeterminate / busy mode
        self.spinner.setTextVisible(False)
        self.spinner.hide()
        layout.addWidget(self.spinner)

        self.status_lbl = QLabel()
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.hide()
        layout.addWidget(self.status_lbl)
        layout.addStretch()

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select splat file', '',
            'Splat files (*.ply *.splat *.glb *.x3d *.x3dv *.x3dj);;All files (*)',
        )
        if path:
            self.in_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, 'Select output folder')
        if path:
            self.out_edit.setText(path)

    def _auto_stem(self, text: str):
        if text and not self.stem_edit.text():
            from pathlib import Path as _Path
            self.stem_edit.setText(_Path(text).stem)

    def _run(self):
        if not self.in_edit.text() or not self.out_edit.text():
            QMessageBox.warning(self, 'Missing paths', 'Input file and output folder are required.')
            return
        if not self.stem_edit.text():
            from pathlib import Path as _Path
            self.stem_edit.setText(_Path(self.in_edit.text()).stem)
        kw = dict(
            input      = self.in_edit.text(),
            output     = self.out_edit.text(),
            stem       = self.stem_edit.text(),
            fmt        = self.fmt.currentText(),
            sh_degree  = None if self.sh_auto.isChecked() else self.sh_degree.value(),
            decode_sh  = self.decode_sh.isChecked(),
            max_splats = self.max_splats.value() if self.max_splats_enable.isChecked() else None,
        )
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(2000)
        self.run_btn.setEnabled(False)
        self.spinner.show()
        self.status_lbl.setText('Loading…')
        self.status_lbl.show()
        self._log.clear()
        self._worker = _ConvertWorker(kw)
        self._worker.log_line.connect(self._append_log)
        self._worker.finished.connect(self._done)
        self._worker.start()

    def _append_log(self, text: str):
        self._log.append(text)
        self._log.moveCursor(QTextCursor.End)
        # Update status label to reflect current phase
        low = text.lower()
        if 'loaded:' in low:
            n = ''
            import re as _re
            m = _re.search(r'(\d+) splats', text)
            if m:
                n = f' ({int(m.group(1)):,} splats)'
            self.status_lbl.setText(f'Building scene{n}…')
        elif 'building x3d' in low or 'building' in low:
            self.status_lbl.setText('Building X3D scene… (may take minutes for large files)')
        elif 'writing' in low or 'splat x3d' in low or 'splat ply' in low or 'splat binary' in low or 'splat glb' in low:
            self.status_lbl.setText('Writing output file…')
        elif 'saved:' in low:
            self.status_lbl.setText('Done.')

    def _done(self, ok: bool, msg: str):
        self.spinner.hide()
        self.status_lbl.hide()
        self.run_btn.setEnabled(True)
        if ok:
            self._append_log(f'✓ Saved: {msg}')
            QMessageBox.information(self, 'Done', f'Output written to:\n{msg}')
        else:
            self._append_log(f'✗ Error: {msg[:200]}')
            QMessageBox.critical(self, 'Conversion error', msg[:400])


class _FolderSplatWorker(QThread):
    log_line = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, kwargs: dict):
        super().__init__()
        self._kw = kwargs

    def run(self):
        handler = _QtLogHandler(self.log_line)
        handler.setFormatter(logging.Formatter('%(levelname)s %(name)s %(message)s'))
        root_log = logging.getLogger()
        root_log.addHandler(handler)
        root_log.setLevel(logging.INFO)
        try:
            from rawkee.tools.lidar import FolderSplatPipeline
            kw  = self._kw
            out = FolderSplatPipeline(
                image_size               = kw['image_size'],
                sh_degree                = kw['sh_degree'],
                iterations               = kw['iterations'],
                matcher                  = kw.get('matcher', 'exhaustive') if not kw.get('use_hloc') else 'exhaustive',
                turntable_mode           = kw.get('turntable', False),
                n_sets                   = kw.get('n_sets', 1),
                turntable_elevation_deg  = kw.get('turntable_elevation_deg', 0.0),
                turntable_radius         = kw.get('turntable_radius', 0.0),
                masks_dir                = kw.get('masks_dir'),
                auto_mask                = kw.get('auto_mask', False),
                chroma_rgb               = kw.get('chroma_rgb'),
                chroma_tolerance         = kw.get('chroma_tolerance', 30.0),
                mask_erosion_px          = kw.get('mask_erosion_px', 8),
                use_hloc                 = kw.get('use_hloc', False),
                colmap_bin               = kw.get('colmap_bin', 'colmap'),
            ).run(
                image_dir         = kw['images'],
                output_dir        = kw['output'],
                output_format     = kw['fmt'],
                focal_px          = kw.get('focal_px'),
                decode_sh         = kw.get('decode_sh', False),
                frame_stride      = kw.get('frame_stride', 1),
                densify_grad_mode = kw.get('grad_mode', '2d'),
                densify_until     = kw.get('densify_until', 0),
            )
            self.finished.emit(True, str(out))
        except Exception as exc:
            import traceback
            self.log_line.emit('ERROR: ' + traceback.format_exc())
            self.finished.emit(False, str(exc))
        finally:
            root_log.removeHandler(handler)


class _FolderSplatTab(QWidget):
    def __init__(self, log_widget: QTextEdit):
        super().__init__()
        self._log    = log_widget
        self._worker = None
        layout = QVBoxLayout(self)

        io_box = QGroupBox('Input / Output')
        g = QGridLayout(io_box)

        g.addWidget(QLabel('Images folder'), 0, 0)
        self.img_edit = QLineEdit()
        self.img_edit.setPlaceholderText('/path/to/folder/of/images')
        self.img_edit.textChanged.connect(self._auto_fill)
        g.addWidget(self.img_edit, 0, 1)
        img_btn = QPushButton('Browse…')
        img_btn.clicked.connect(self._browse_images)
        g.addWidget(img_btn, 0, 2)

        g.addWidget(QLabel('Output folder'), 1, 0)
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText('/path/to/output')
        g.addWidget(self.out_edit, 1, 1)
        out_btn = QPushButton('Browse…')
        out_btn.clicked.connect(self._browse_output)
        g.addWidget(out_btn, 1, 2)
        layout.addWidget(io_box)

        opt_box = QGroupBox('Pipeline Options')
        g2 = QGridLayout(opt_box)

        g2.addWidget(QLabel('Output format'), 0, 0)
        self.fmt = QComboBox()
        self.fmt.addItems(['x3d', 'x3dv', 'x3dj', 'ply', 'splat', 'glb'])
        g2.addWidget(self.fmt, 0, 1)

        g2.addWidget(QLabel('COLMAP matcher'), 1, 0)
        self.matcher = QComboBox()
        self.matcher.addItems(['hloc (SuperPoint+LightGlue)', 'Sequential (SIFT only)', 'Exhaustive (SIFT only)'])
        self.matcher.setToolTip(
            'hloc: DISK+LightGlue deep-learned features — best for low-texture objects (default)\n'
            '  Requires: pip install git+https://github.com/cvg/Hierarchical-Localization\n'
            'Sequential (SIFT only): matches adjacent frames — fallback for ordered footage\n'
            'Exhaustive (SIFT only): tests every pair — fallback for small unordered collections'
        )
        g2.addWidget(self.matcher, 1, 1)

        g2.addWidget(QLabel('Focal length (px)'), 2, 0)
        focal_row = QHBoxLayout()
        self.focal_auto = QCheckBox('Auto from EXIF')
        self.focal_auto.setChecked(True)
        self.focal_auto.toggled.connect(lambda on: self.focal_px.setEnabled(not on))
        self.focal_px = QSpinBox()
        self.focal_px.setRange(100, 99999)
        self.focal_px.setValue(3000)
        self.focal_px.setEnabled(False)
        focal_row.addWidget(self.focal_auto)
        focal_row.addWidget(self.focal_px)
        focal_row.addStretch()
        g2.addLayout(focal_row, 2, 1)

        g2.addWidget(QLabel('Image size (px)'), 3, 0)
        img_size_row = QHBoxLayout()
        self.image_size = QSpinBox()
        self.image_size.setRange(64, 4096)
        self.image_size.setValue(1024)
        self.image_size.setSingleStep(64)
        self.image_size.setToolTip(
            'Training resolution (square). Source images are resized to this before training.\n'
            'Larger = better quality but more GPU memory.\n'
            '512: ~4 GB VRAM (safe for all GPUs)\n'
            '1024: ~8 GB VRAM (recommended for minerals / turntable)\n'
            '2048: ~24 GB VRAM (high-end GPU required)\n'
            'Tip: the paper "Virtual Mineral Collections Using 3DGS" (Web3D 25) trains\n'
            'at full source resolution (3000×2000) for best metallic/iridescent detail.'
        )
        img_size_row.addWidget(self.image_size)
        self.src_res_lbl = QLabel('')
        self.src_res_lbl.setStyleSheet('color: gray; font-size: 9px;')
        img_size_row.addWidget(self.src_res_lbl)
        img_size_row.addStretch()
        g2.addLayout(img_size_row, 3, 1)

        g2.addWidget(QLabel('SH degree'), 4, 0)
        self.sh_degree = QSpinBox()
        self.sh_degree.setRange(0, 3)
        self.sh_degree.setValue(3)
        g2.addWidget(self.sh_degree, 4, 1)

        g2.addWidget(QLabel('Iterations'), 5, 0)
        self.iterations = QSpinBox()
        self.iterations.setRange(100, 200000)
        self.iterations.setValue(30000)
        self.iterations.setSingleStep(1000)
        self.iterations.setToolTip(
            '30 000 recommended for minerals/objects (Web3D \'25 paper benchmark).\n'
            '10 000 is a fast preview; 60 000+ for highest quality.'
        )
        g2.addWidget(self.iterations, 5, 1)

        g2.addWidget(QLabel('Densify until'), 6, 0)
        self.densify_until = QSpinBox()
        self.densify_until.setRange(0, 200000)
        self.densify_until.setValue(0)
        self.densify_until.setSingleStep(1000)
        self.densify_until.setToolTip(
            '0 = auto (half of Iterations).\n'
            'Set explicitly for outdoor or large scenes:\n'
            '  Room/indoor:   20 000–30 000\n'
            '  Building:      30 000–50 000\n'
            '  Large outdoor: 50 000+'
        )
        g2.addWidget(self.densify_until, 6, 1)

        g2.addWidget(QLabel('Frame stride'), 7, 0)
        self.frame_stride = QSpinBox()
        self.frame_stride.setRange(1, 32)
        self.frame_stride.setValue(1)
        self.frame_stride.setToolTip('Use every N-th registered image for training (1 = all)')
        g2.addWidget(self.frame_stride, 7, 1)

        self.decode_sh = QCheckBox('Pre-decode SH → RGB on export')
        g2.addWidget(self.decode_sh, 8, 0, 1, 2)

        self.grad_mode_2d = QCheckBox('Screen-space density gradients (2D) — recommended')
        self.grad_mode_2d.setChecked(True)
        self.grad_mode_2d.setToolTip(
            'Use 2D screen-space gradients for density control (Kerbl et al. 2023).\n'
            'More robust than 3D world-space gradients, especially for masked training.\n'
            'Uncheck to fall back to 3D gradients (useful for debugging).'
        )
        g2.addWidget(self.grad_mode_2d, 9, 0, 1, 2)

        self.turntable = QCheckBox(
            'Turntable mode  —  use synthetic circular poses (recommended for object-on-turntable captures)'
        )
        self.turntable.setToolTip(
            'Bypasses COLMAP’s fragmented mapper.\n'
            'Estimates camera orbit geometry from the partial COLMAP model, then\n'
            'constructs synthetic 360° poses and trains on ALL images.\n\n'
            'Capture tips (Web3D 25 mineral scanning paper):\n'
            '  • BLACK MATTE background — reduces stray Gaussians\n'
            '  • Visible MARKERS on turntable surface — COLMAP needs features to track\n'
            '  • Fixed focal length; manual exposure + white balance\n'
            '  • Color-calibrate with a color checker (Darktable is free)\n'
            '  • 130–270 images per pass is the recommended sweet spot'
        )
        g2.addWidget(self.turntable, 10, 0, 1, 2)

        g2.addWidget(QLabel('Turntable sets'), 11, 0)
        self.n_sets = QSpinBox()
        self.n_sets.setRange(1, 8)
        self.n_sets.setValue(1)
        self.n_sets.setToolTip('Number of distinct turntable passes (e.g. 2 = top + flipped bottom)')
        g2.addWidget(self.n_sets, 11, 1)

        g2.addWidget(QLabel('Elevation override (°)'), 12, 0)
        self.turntable_elevation = QDoubleSpinBox()
        self.turntable_elevation.setRange(0.0, 89.0)
        self.turntable_elevation.setValue(0.0)
        self.turntable_elevation.setSingleStep(5.0)
        self.turntable_elevation.setDecimals(1)
        self.turntable_elevation.setToolTip(
            '0 = auto-estimate from COLMAP.\n'
            'Set to 20–35° if COLMAP gives a bad estimate (near-horizontal orbit).\n'
            'This is the camera elevation above the object equator for pass 1;\n'
            'pass 2 (flipped) mirrors it below.'
        )
        g2.addWidget(self.turntable_elevation, 12, 1)

        g2.addWidget(QLabel('Radius override (m)'), 13, 0)
        self.turntable_radius = QDoubleSpinBox()
        self.turntable_radius.setRange(0.0, 100.0)
        self.turntable_radius.setValue(0.0)
        self.turntable_radius.setSingleStep(0.1)
        self.turntable_radius.setDecimals(2)
        self.turntable_radius.setToolTip(
            '0 = auto-estimate from COLMAP.\n'
            'Set to the actual camera-to-object distance (metres) if COLMAP gives a wrong scale.'
        )
        g2.addWidget(self.turntable_radius, 13, 1)
        layout.addWidget(opt_box)

        # ── Background masking ────────────────────────────────────────────
        mask_box = QGroupBox('Background Masking')
        gm = QGridLayout(mask_box)

        gm.addWidget(QLabel('Masks folder'), 0, 0)
        masks_row = QHBoxLayout()
        self.masks_dir = QLineEdit()
        self.masks_dir.setPlaceholderText('Auto-detect masks/ subfolder, or browse…')
        masks_row.addWidget(self.masks_dir)
        mask_browse = QPushButton('Browse…')
        mask_browse.clicked.connect(self._browse_masks)
        masks_row.addWidget(mask_browse)
        gm.addLayout(masks_row, 0, 1)

        self.auto_mask = QCheckBox('Auto-mask with rembg (AI background removal)')
        self.auto_mask.setToolTip(
            'Uses the rembg AI model to remove backgrounds automatically.\n'
            'First run downloads the model (~170 MB).\n'
            'Masks are cached in _colmap_work/masks/ and reused on subsequent runs.\n'
            'Install: pip install rembg'
        )
        gm.addWidget(self.auto_mask, 1, 0, 1, 2)

        self.chroma_enable = QCheckBox('Chroma-key colour')
        self.chroma_enable.setToolTip(
            'Remove a specific background colour (e.g. blue screen).\n'
            'Click the colour swatch to pick the background colour.'
        )
        self.chroma_enable.toggled.connect(self._chroma_toggled)
        gm.addWidget(self.chroma_enable, 2, 0)

        chroma_ctrl = QHBoxLayout()
        self.chroma_swatch = QPushButton()
        self.chroma_swatch.setFixedWidth(40)
        self.chroma_swatch.setEnabled(False)
        self.chroma_swatch.setToolTip('Open colour palette picker')
        self._chroma_color = (0, 80, 180)   # default: blue
        self._update_chroma_swatch()
        self.chroma_swatch.clicked.connect(self._pick_chroma_color)
        chroma_ctrl.addWidget(self.chroma_swatch)
        self.chroma_eyedrop = QPushButton('🎯 Pick from image')
        self.chroma_eyedrop.setEnabled(False)
        self.chroma_eyedrop.setToolTip('Click a pixel in one of your source images to sample the background colour')
        self.chroma_eyedrop.clicked.connect(self._pick_chroma_from_image)
        chroma_ctrl.addWidget(self.chroma_eyedrop)
        chroma_ctrl.addWidget(QLabel('Tolerance'))
        self.chroma_tolerance = QSpinBox()
        self.chroma_tolerance.setRange(1, 180)
        self.chroma_tolerance.setValue(30)
        self.chroma_tolerance.setSuffix('°')
        self.chroma_tolerance.setEnabled(False)
        self.chroma_tolerance.setToolTip('Hue tolerance in degrees (lower = more precise)')
        chroma_ctrl.addWidget(self.chroma_tolerance)
        chroma_ctrl.addStretch()
        gm.addLayout(chroma_ctrl, 2, 1)

        gm.addWidget(QLabel('Edge erosion (px)'), 3, 0)
        self.mask_erosion = QSpinBox()
        self.mask_erosion.setRange(0, 100)
        self.mask_erosion.setValue(8)
        self.mask_erosion.setSingleStep(2)
        self.mask_erosion.setToolTip(
            'Shrink the foreground mask inward by this many pixels after generation.\n'
            'Removes uncertain edge pixels where background bleeds into the object.\n'
            '0 = no erosion.  8 is a safe default for typical turntable captures.'
        )
        gm.addWidget(self.mask_erosion, 3, 1)

        layout.addWidget(mask_box)

        self.run_btn = QPushButton('Run  (COLMAP → 3DGS)')
        self.run_btn.setFixedHeight(36)
        self.run_btn.clicked.connect(self._run)
        layout.addWidget(self.run_btn)

        self.spinner = QProgressBar()
        self.spinner.setRange(0, 0)
        self.spinner.setTextVisible(False)
        self.spinner.hide()
        layout.addWidget(self.spinner)

        self.status_lbl = QLabel()
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.hide()
        layout.addWidget(self.status_lbl)
        layout.addStretch()

    def _browse_images(self):
        path = QFileDialog.getExistingDirectory(self, 'Select image folder')
        if path:
            self.img_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, 'Select output folder')
        if path:
            self.out_edit.setText(path)

    def _browse_masks(self):
        path = QFileDialog.getExistingDirectory(self, 'Select masks folder')
        if path:
            self.masks_dir.setText(path)

    def _chroma_toggled(self, on: bool):
        self.chroma_swatch.setEnabled(on)
        self.chroma_eyedrop.setEnabled(on)
        self.chroma_tolerance.setEnabled(on)

    def _update_chroma_swatch(self):
        r, g, b = self._chroma_color
        self.chroma_swatch.setStyleSheet(
            f'background-color: rgb({r},{g},{b}); border: 1px solid #888;'
        )

    def _pick_chroma_color(self):
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        r, g, b = self._chroma_color
        col = QColorDialog.getColor(QColor(r, g, b), self.window(), 'Pick background colour')
        if col.isValid():
            self._chroma_color = (col.red(), col.green(), col.blue())
            self._update_chroma_swatch()

    def _pick_chroma_from_image(self):
        """Show a thumbnail of the first source image; click a pixel to sample its colour."""
        from pathlib import Path as _P
        images_folder = self.img_edit.text().strip()
        if not images_folder:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self.window(), 'No images folder',
                                    'Set the Images folder first, then use Pick from image.')
            return
        exts = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp'}
        imgs = sorted(p for p in _P(images_folder).iterdir() if p.suffix.lower() in exts)
        if not imgs:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self.window(), 'No images found',
                                f'No image files found in:\n{images_folder}')
            return

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel as _QLabel, QDialogButtonBox
        from PySide6.QtGui import QPixmap, QImage, QCursor
        from PySide6.QtCore import Qt as _Qt
        import numpy as np
        from PIL import Image as _PIL

        # Load and scale the first image to a preview size
        preview_size = 640
        img_np = np.array(_PIL.open(imgs[0]).convert('RGB'))
        h, w = img_np.shape[:2]
        scale = preview_size / max(h, w)
        pw, ph = int(w * scale), int(h * scale)
        thumb = np.array(_PIL.fromarray(img_np).resize((pw, ph), _PIL.LANCZOS))

        qimg = QImage(thumb.data, pw, ph, pw * 3, QImage.Format_RGB888).copy()
        pix  = QPixmap.fromImage(qimg)

        dlg = QDialog(self.window())
        dlg.setWindowTitle('Click on the background colour')
        lay = QVBoxLayout(dlg)
        info = _QLabel('Click anywhere on the background to sample that colour.')
        info.setWordWrap(True)
        lay.addWidget(info)

        img_lbl = _QLabel()
        img_lbl.setPixmap(pix)
        img_lbl.setCursor(QCursor(_Qt.CrossCursor))
        img_lbl.setFixedSize(pw, ph)
        lay.addWidget(img_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.Cancel)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)

        sampled = {}

        def _on_click(ev):
            x = int(ev.position().x() / scale)
            y = int(ev.position().y() / scale)
            x = max(0, min(x, w - 1))
            y = max(0, min(y, h - 1))
            r, g, b = int(img_np[y, x, 0]), int(img_np[y, x, 1]), int(img_np[y, x, 2])
            sampled['color'] = (r, g, b)
            dlg.accept()

        img_lbl.mousePressEvent = _on_click
        dlg.exec()

        if 'color' in sampled:
            self._chroma_color = sampled['color']
            self._update_chroma_swatch()

    def _auto_fill(self, text: str):
        """Pre-fill output folder and detect EXIF focal + source resolution."""
        if text and not self.out_edit.text():
            from pathlib import Path as _Path
            self.out_edit.setText(str(_Path(text).parent / (_Path(text).name + '_splat')))
        if text:
            self._detect_image_info(text)

    def _detect_image_info(self, folder: str) -> None:
        """Read the first image in the folder for resolution and EXIF focal length."""
        from pathlib import Path as _Path
        _EXTS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp'}
        candidates = sorted(p for p in _Path(folder).iterdir() if p.suffix.lower() in _EXTS)
        if not candidates:
            self.src_res_lbl.setText('')
            return
        try:
            from PIL import Image as _PIL
            with _PIL.open(candidates[0]) as im:
                w, h = im.size
            self.src_res_lbl.setText(f'source: {w}×{h} px')
            # Auto-fill focal length from EXIF if Auto is checked
            if self.focal_auto.isChecked():
                from rawkee.tools.lidar.colmap_splat_pipeline import _exif_focal_px
                result = _exif_focal_px(candidates[0])
                if result:
                    fx, _, _ = result
                    self.focal_px.setValue(int(round(fx)))
        except Exception:
            self.src_res_lbl.setText('')

    def _run(self):
        if not self.img_edit.text() or not self.out_edit.text():
            QMessageBox.warning(self, 'Missing paths', 'Images folder and output folder are required.')
            return
        kw = dict(
            images       = self.img_edit.text(),
            output       = self.out_edit.text(),
            fmt          = self.fmt.currentText(),
            use_hloc     = self.matcher.currentText().startswith('hloc'),
            matcher      = ('sequential' if self.matcher.currentText().startswith('Sequential')
                            else 'exhaustive'),  # used only when hloc unavailable (fallback)
            focal_px     = None if self.focal_auto.isChecked() else float(self.focal_px.value()),
            image_size   = self.image_size.value(),
            sh_degree    = self.sh_degree.value(),
            iterations   = self.iterations.value(),
            frame_stride = self.frame_stride.value(),
            decode_sh    = self.decode_sh.isChecked(),
            turntable    = self.turntable.isChecked(),
            n_sets                   = self.n_sets.value(),
            turntable_elevation_deg  = self.turntable_elevation.value(),
            turntable_radius         = self.turntable_radius.value(),
            masks_dir                = self.masks_dir.text() or None,
            auto_mask                = self.auto_mask.isChecked(),
            chroma_rgb               = self._chroma_color if self.chroma_enable.isChecked() else None,
            chroma_tolerance         = float(self.chroma_tolerance.value()),
            mask_erosion_px          = self.mask_erosion.value(),
            densify_until            = self.densify_until.value(),
            grad_mode                = '2d' if self.grad_mode_2d.isChecked() else '3d',
        )
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(2000)
        self.run_btn.setEnabled(False)
        self.spinner.show()
        self.status_lbl.setText('Running COLMAP…')
        self.status_lbl.show()
        self._log.clear()
        self._worker = _FolderSplatWorker(kw)
        self._worker.log_line.connect(self._append_log)
        self._worker.finished.connect(self._done)
        self._worker.start()

    def _append_log(self, text: str):
        self._log.append(text)
        self._log.moveCursor(QTextCursor.End)
        low = text.lower()
        if 'extract' in low or 'feature' in low:
            self.status_lbl.setText('COLMAP: extracting features…')
        elif 'match' in low:
            self.status_lbl.setText('COLMAP: matching features…')
        elif 'mapper' in low or 'mapping' in low or 'reconstruct' in low:
            self.status_lbl.setText('COLMAP: reconstructing…')
        elif 'registered' in low or 'initialising' in low or 'training' in low:
            self.status_lbl.setText('Training 3DGS…')
        elif 'saved:' in low or 'complete' in low:
            self.status_lbl.setText('Done.')

    def _done(self, ok: bool, msg: str):
        self.spinner.hide()
        self.status_lbl.hide()
        self.run_btn.setEnabled(True)
        if ok:
            self._append_log(f'✓ Saved: {msg}')
            QMessageBox.information(self, 'Done', f'Splat written to:\n{msg}')
        else:
            self._append_log(f'✗ Error: {msg[:200]}')
            QMessageBox.critical(self, 'Pipeline error', msg[:400])


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class ScanPipelineApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('RawKee Lidar and Scan Pipelines')
        self._tabs_widget: 'QTabWidget | None' = None
        self._build_ui()

    def _register_tabs(self, tabs: 'QTabWidget') -> None:
        self._tabs_widget = tabs

    def closeEvent(self, event):
        # Terminate all running pipeline workers before the window closes so that
        # COLMAP mapper threads don't continue consuming CPU after the GUI exits.
        if self._tabs_widget:
            for i in range(self._tabs_widget.count()):
                tab = self._tabs_widget.widget(i)
                inner = getattr(tab, 'widget', lambda: tab)()
                worker = getattr(inner, '_worker', None)
                if worker is not None and worker.isRunning():
                    worker.terminate()
                    worker.wait(3000)
        event.accept()
        import os
        os._exit(0)

    def _build_ui(self):
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
        self._log.setMinimumHeight(80)
        self._log.setMaximumHeight(120)
        log_layout.addWidget(self._log)
        root.addWidget(log_box)

        from PySide6.QtWidgets import QScrollArea

        def _scrolled(widget):
            sa = QScrollArea()
            sa.setWidget(widget)
            sa.setWidgetResizable(True)
            sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            return sa

        # Pipeline tabs
        tabs = QTabWidget()
        self._tabs_widget = tabs
        tabs.addTab(_scrolled(_MeshTab(self._shared, self._log)),   'Mesh')
        tabs.addTab(_scrolled(_SplatTab(self._shared, self._log)),  'Gaussian Splat')
        tabs.addTab(_scrolled(_ConvertTab(self._log)),              'Convert Splat')
        tabs.addTab(_scrolled(_FolderSplatTab(self._log)),          'Folder → Splat')
        root.insertWidget(1, tabs)   # insert between shared options and log


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = ScanPipelineApp()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
