"""
File Author: Thomaz Diaz, UND Dream Lab;
Description: "Rawkee Scan Studio Theme"  [DL-4]:

Librays Used: 
-Pyside6 on Python 3.14 Interpreter
-
"""

DARK_AZUL = "#18364E"
AZUL = "#008CFF"
MAIN = "#181818" 
GRIS = "#3D3D3D"
DARK_GRIS = "#1E1E1E"
BLANCO = "#eeeeee"

THEME_QSS_RAW = """
/* Root and window */
QWidget {
    background-color: {MAIN};
    color: {BLANCO};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
}
QMainWindow {
    background-color: {DARK_GRIS};
}

/* Sidebar */
QWidget#rk_sidebar {
    background-color: {DARK_GRIS};
    border-right: 1px solid {BLANCO};
    min-width: 190px;
    max-width: 190px;
}
QPushButton.rk_navButton {
    background: transparent;
    border: none;
    color: {BLANCO};
    padding: 10px 14px;
    text-align: left;
    border-left: 4px solid transparent;
}
QPushButton.rk_navButton:hover {
    background-color: {GRIS};
    color: {BLANCO};
}
QPushButton.rk_navButton:checked {
    background-color: {DARK_AZUL};
    color: {BLANCO};
    border-left: 4px solid {AZUL};
}

/* Central content */
QStackedWidget#rk_stack {
    background-color: {MAIN};
}

/* Dock and console */
QDockWidget {
    background-color: {DARK_GRIS};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}
QDockWidget#rk_console_dock {
    background-color: {DARK_GRIS};
}
QDockWidget#rk_console_dock QWidget {
    background-color: {DARK_GRIS};
}
QWidget#rk_console_titlebar {
    border-bottom: 1px solid {BLANCO};
    border-top: 1px solid {BLANCO};
}
QWidget#rk_console_titlebar QLabel, QWidget#rk_console_titlebar QToolButton {
    background-color: transparent;
}


QTextEdit#rk_console {
    background-color: {MAIN};
    color: {BLANCO};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 14px;
    border: none;
}

/* Status bar */
QStatusBar {
    background-color: {AZUL};
    color: {BLANCO};
    border-top: 1px solid {AZUL};
    min-height: 22px;
}

QStatusBar QLabel {
    color: {BLANCO};
}

/* Left status label (small badge) */
QLabel#rk_status_left {
    background-color: {AZUL};
    color: {BLANCO};
    padding: 2px 10px;
    border-radius: 2px;
}

/* Right activity badge (console idle) */
QLabel#rk_status_right {
    background-color: {AZUL};
    color: {BLANCO};
    padding: 2px 10px;
    border-radius: 2px;
}

/* Controls foundation */
QPushButton#rk_primary {
    background-color: {AZUL};
    color: {BLANCO};
    padding: 6px 12px;
    border-radius: 3px;
}
QPushButton.rk_browse {
    background-color: transparent;
    color: {BLANCO};
    border: 1px solid {BLANCO};
    padding: 4px 8px;
    border-radius: 4px;
}

QPushButton.rk_browse:hover {
    background-color: {GRIS}};
}

/* Header */
QWidget#headerContainer {
    background: transparent;
    padding: 12px 0px;
}
QLabel#pageTitle {
    font-size: 20px;
    font-weight: 600;
    color: {BLANCO};
}
QLabel#pageDescription {
    font-size: 14px;
    color: {BLANCO};
}
QLabel#headerIcon {
    background-color: {DARK_AZUL};
    border: 1px solid {AZUL};
    color: {AZUL};
    padding: 8px;
    border-radius: 6px;
}

/* Group boxes */
QGroupBox {
    background-color: {DARK_GRIS};
    border: 1px solid {BLANCO};
    border-radius: 6px;
    margin-top: 12px;
    padding: 10px;
    color: {BLANCO};
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 8px;
    color: {BLANCO};
}
QGroupBox QWidget {
    background-color: transparent;
}
QPushButton#rk_primary:disabled {
    background-color: {MAIN};
    color: #ff00b3;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: {MAIN};
    color: {BLANCO};
    border: 1px solid {BLANCO};
    padding: 4px 6px;
    min-height: 22px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid {DARK_AZUL};
}
QCheckBox {
    color: {BLANCO};
}
QCheckBox::indicator:unchecked {
    background: {MAIN}};
    border: 1px solid {BLANCO};
}
QCheckBox::indicator:checked {
    background: {AZUL};
    border: 1px solid {BLANCO};
}

/* Scrollbars: minimal, theme-aware */
QScrollBar:vertical {
    background: transparent;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: {GRIS};
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 12px;
}
QScrollBar::handle:horizontal {
    background: #ff00b3;
    min-width: 20px;
    border-radius: 6px;
}

/* Disabled */
*:disabled {
    color: #ff00b3;
}
"""


THEME_QSS = THEME_QSS_RAW.replace("{{", "{").replace("}}", "}")
THEME_QSS = THEME_QSS.replace("{MAIN}", MAIN).replace("{DARK_AZUL}", DARK_AZUL).replace("{DARK_GRIS}", DARK_GRIS).replace("{BLANCO}", BLANCO).replace("{AZUL}", AZUL).replace("{GRIS}", GRIS)


def apply_theme(app):
        """Apply the built QSS theme to the given QApplication.

        Calling code should ensure PySide6 is importable.
        """
        app.setStyleSheet(THEME_QSS)