"""
Standalone entry point for the RawKee X3D Interaction Editor.

    python -m rawkee.editor
"""
# All environment setup must happen before any Qt WebEngine DLLs are loaded.
import os
import sys

# Ensure the interpreter's own directory is on PATH so the Chromium GPU
# subprocess can find ANGLE DLLs (libEGL/libGLESv2) bundled alongside it.
# This matters for mayapy and other bundled interpreters where the DLLs sit
# next to the executable but aren't automatically inherited by child processes.
_exe_dir = os.path.dirname(os.path.abspath(sys.executable))
if _exe_dir not in os.environ.get('PATH', '').split(os.pathsep):
    os.environ['PATH'] = _exe_dir + os.pathsep + os.environ.get('PATH', '')

_platform = sys.platform
if _platform == 'win32':
    os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS',
                          '--use-gl=angle '
                          '--ignore-gpu-blacklist --ignore-gpu-blocklist')
    os.environ.setdefault('QT_D3DCREATE_MULTITHREADED', '1')
elif _platform == 'darwin':
    os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS',
                          '--use-gl=angle '
                          '--ignore-gpu-blacklist --ignore-gpu-blocklist')
else:
    os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS',
                          '--ignore-gpu-blacklist --ignore-gpu-blocklist')

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer, QtMsgType, qInstallMessageHandler
from rawkee.editor.RKSceneEditor import RKSceneEditor, apply_dark_palette as _apply_dark_palette
import signal

_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'x3d_interaction_editor3.ico')


def _qt_message_handler(msg_type, context, message):
    pass


def main():
    qInstallMessageHandler(_qt_message_handler)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setWindowIcon(QIcon(_ICON_PATH))
    _apply_dark_palette(app)
    # Allow Ctrl+C to quit the Qt app on Windows
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    _sigint_timer = QTimer()
    _sigint_timer.start(200)
    _sigint_timer.timeout.connect(lambda: None)  # wake event loop so SIGINT is processed
    editor = RKSceneEditor()
    editor.resize(1400, 900)
    editor.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
