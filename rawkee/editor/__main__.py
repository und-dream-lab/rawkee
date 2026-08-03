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
                          '--use-gl=angle --in-process-gpu '
                          '--ignore-gpu-blacklist --ignore-gpu-blocklist')
    os.environ.setdefault('QT_D3DCREATE_MULTITHREADED', '1')
elif _platform == 'darwin':
    os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS',
                          '--use-gl=angle --in-process-gpu '
                          '--ignore-gpu-blacklist --ignore-gpu-blocklist')
else:
    os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS',
                          '--in-process-gpu '
                          '--ignore-gpu-blacklist --ignore-gpu-blocklist')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QPalette, QColor
from rawkee.editor.RKSceneEditor import RKSceneEditor


def _qt_message_handler(msg_type, context, message):
    # Suppress noisy Qt painter/rendering warnings that don't affect functionality
    _suppressed = (
        'QPainter::',
        'QBackingStore::',
        'QOpenGLContext::',
        'updateRequestSent',
    )
    if any(message.startswith(s) for s in _suppressed):
        return
    if msg_type in (QtMsgType.QtDebugMsg, QtMsgType.QtInfoMsg):
        return


def _apply_dark_palette(app):
    app.setStyle('Fusion')
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,               QColor(45,  45,  45))
    p.setColor(QPalette.ColorRole.WindowText,           QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Base,                 QColor(30,  30,  30))
    p.setColor(QPalette.ColorRole.AlternateBase,        QColor(45,  45,  45))
    p.setColor(QPalette.ColorRole.ToolTipBase,          QColor(30,  30,  30))
    p.setColor(QPalette.ColorRole.ToolTipText,          QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Text,                 QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Button,               QColor(55,  55,  55))
    p.setColor(QPalette.ColorRole.ButtonText,           QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.BrightText,           QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.Link,                 QColor(0,   154,  68))   # UND green
    p.setColor(QPalette.ColorRole.Highlight,            QColor(0,   154,  68))   # UND green
    p.setColor(QPalette.ColorRole.HighlightedText,      QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.PlaceholderText,      QColor(120, 120, 120))
    # Disabled state
    disabled = QPalette.ColorGroup.Disabled
    p.setColor(disabled, QPalette.ColorRole.WindowText, QColor(120, 120, 120))
    p.setColor(disabled, QPalette.ColorRole.Text,       QColor(120, 120, 120))
    p.setColor(disabled, QPalette.ColorRole.ButtonText, QColor(120, 120, 120))
    p.setColor(disabled, QPalette.ColorRole.Highlight,  QColor(60,  100,  60))
    app.setPalette(p)


def main():
    qInstallMessageHandler(_qt_message_handler)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication.instance() or QApplication(sys.argv)
    _apply_dark_palette(app)
    editor = RKSceneEditor()
    editor.resize(1400, 900)
    editor.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
