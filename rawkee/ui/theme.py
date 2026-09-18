"""
File Author: Thomaz Diaz, UND Dream Lab;
Description: "Rawkee Scan Studio Theme"  [DL-4]:

Librays Used: 
-Pyside6 on Python 3.14 Interpreter
-
"""

DARK_BLUE = "#18364E"
BLUE = "#008CFF"
BACKGROUND = "#0f1113"
SURFACE = "#16181a"
DARK_GREY = "#1F1F1F"
WHITE = "#ffffff"

THEME_QSS_RAW = """
/* Root and window */
QWidget {
    background-color: {BACKGROUND};
    color: {WHITE};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: {DARK_GREY};
}

/* Sidebar */
QWidget#rk_sidebar {
    background-color: {DARK_GREY};
    border-right: 1px solid #222426;
    min-width: 190px;
    max-width: 190px;
}

QPushButton.rk_navButton {
    background: transparent;
    border: none;
    color: {WHITE};
    padding: 10px 14px;
    text-align: left;
    border-left: 4px solid transparent;
}

QPushButton.rk_navButton:hover {
    background-color: #4b4d50;
    color: {WHITE};
}

QPushButton.rk_navButton:checked {
    background-color: {DARK_BLUE};
    color: {WHITE};
    border-left: 4px solid {BLUE};
}

/* Central content */
QStackedWidget#rk_stack {
    background-color: {BACKGROUND};
}

/* Dock and console */
QDockWidget {
    background-color: {SURFACE};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
    border-top: 1px solid #222426;
}

QTextEdit#rk_console {
    background-color: #0b0b0b;
    color: {WHITE};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 14px;
    border: none;
}

/* Status bar */
QStatusBar {
    background-color: {BLUE};
    color: {WHITE};
    border-top: 1px solid {BLUE};
    min-height: 22px;
}

QStatusBar QLabel {
    color: {WHITE};
}

/* Left status label (small badge) */
QLabel#rk_status_left {
    background-color: {DARK_BLUE};
    color: {WHITE};
    padding: 2px 10px;
    border-radius: 2px;
}

/* Right activity badge (console idle) */
QLabel#rk_status_right {
    background-color: {DARK_BLUE};
    color: {WHITE};
    padding: 2px 10px;
    border-radius: 2px;
}

/* Controls foundation */
QPushButton#rk_primary {
    background-color: {BLUE};
    color: {WHITE};
    padding: 6px 12px;
    border-radius: 3px;
}

QPushButton.rk_browse {
    background-color: transparent;
    color: {DARK_GREY};
    border: 1px solid #2a2b2c;
    padding: 4px 8px;
    border-radius: 4px;
}

QPushButton.rk_browse:hover {
    background-color: #1b1c1d;
}

/* Header */
QWidget#headerContainer {
    background: transparent;
    padding: 12px 0px;
}

QLabel#pageTitle {
    font-size: 20px;
    font-weight: 600;
    color: {WHITE};
}

QLabel#pageDescription {
    font-size: 14px;
    color: {WHITE};
}

QLabel#headerIcon {
    background-color: #0d2b3f;
    border: 1px solid {DARK_BLUE};
    color: {BLUE};
    padding: 8px;
    border-radius: 6px;
}

/* Group boxes */
QGroupBox {
    background-color: #0f1113;
    border: 1px solid #232526;
    border-radius: 6px;
    margin-top: 12px;
    padding: 10px;
    color: {WHITE};
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 8px;
    color: {WHite};
}

QPushButton#rk_primary:disabled {
    background-color: #2b2c2e;
    color: #6f777f;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #121314;
    color: {DARK_GREY};
    border: 1px solid #1f2123;
    padding: 4px 6px;
    min-height: 22px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid {DARK_BLUE};
}

QCheckBox {
    color: {DARK_GREY};
}

QCheckBox::indicator:unchecked {
    background: #101213;
    border: 1px solid #232526;
}

QCheckBox::indicator:checked {
    background: {DARK_BLUE};
    border: 1px solid {DARK_BLUE};
}

/* Scrollbars: minimal, theme-aware */
QScrollBar:vertical {
    background: transparent;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #232526;
    min-height: 20px;
    border-radius: 6px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 12px;
}
QScrollBar::handle:horizontal {
    background: #232526;
    min-width: 20px;
    border-radius: 6px;
}

/* Disabled */
*:disabled {
    color: #5a6065;
}
"""


THEME_QSS = THEME_QSS_RAW.replace("{{", "{").replace("}}", "}")
THEME_QSS = THEME_QSS.replace("{BACKGROUND}", BACKGROUND).replace("{SURFACE}", SURFACE).replace("{DARK_BLUE}", DARK_BLUE).replace("{DARK_GREY}", DARK_GREY).replace("{WHITE}", WHITE).replace("{BLUE}", BLUE)


def apply_theme(app):
        """Apply the built QSS theme to the given QApplication.

        Calling code should ensure PySide6 is importable.
        """
        app.setStyleSheet(THEME_QSS)