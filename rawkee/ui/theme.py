"""New RawKee Scan Studio theme.

This file defines a bespoke dark QSS theme authored from scratch.
Do not copy or reference legacy RawKee QSS.
"""

ACCENT = "#0a84ff"
BACKGROUND = "#0f1113"
SURFACE = "#16181a"
FOREGROUND = "#d6d6d6"
SECONDARY = "#9aa4ad"

THEME_QSS_RAW = """
/* Root and window */
QWidget {
    background-color: {BACKGROUND};
    color: {FOREGROUND};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px;
}

QMainWindow {
    background-color: {BACKGROUND};
}

/* Sidebar */
QWidget#rk_sidebar {
    background-color: {SURFACE};
    border-right: 1px solid #222426;
    min-width: 190px;
    max-width: 190px;
}

QPushButton.rk_navButton {
    background: transparent;
    border: none;
    color: {SECONDARY};
    padding: 10px 14px;
    text-align: left;
    border-left: 4px solid transparent;
}

QPushButton.rk_navButton:hover {
    background-color: #1b1c1d;
    color: {FOREGROUND};
}

QPushButton.rk_navButton:checked {
    background-color: #111317;
    color: {FOREGROUND};
    border-left: 4px solid {ACCENT};
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

QDockWidget::title {
    background: transparent;
    padding: 6px 8px;
    color: {SECONDARY};
}

QTextEdit#rk_console {
    background-color: #0b0b0b;
    color: {FOREGROUND};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    border: none;
}

/* Status bar */
QStatusBar {
    background-color: {ACCENT};
    color: #ffffff;
    border-top: 1px solid #0a6fe0;
    min-height: 22px;
}

QStatusBar QLabel {
    color: #ffffff;
}

/* Left status label (small badge) */
QLabel#rk_status_left {
    background-color: {ACCENT};
    color: #ffffff;
    padding: 2px 10px;
    border-radius: 2px;
}

/* Right activity badge (console idle) */
QLabel#rk_status_right {
    background-color: {ACCENT};
    color: #ffffff;
    padding: 2px 10px;
    border-radius: 2px;
}

/* Controls foundation */
QPushButton#rk_primary {
    background-color: {ACCENT};
    color: white;
    padding: 6px 12px;
    border-radius: 3px;
}

QPushButton.rk_browse {
    background-color: transparent;
    color: {FOREGROUND};
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
    color: {FOREGROUND};
}

QLabel#pageDescription {
    font-size: 12px;
    color: {SECONDARY};
}

QLabel#headerIcon {
    background-color: #0d2b3f;
    border: 1px solid {ACCENT};
    color: {FOREGROUND};
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
    color: {SECONDARY};
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 8px;
    color: {FOREGROUND};
}

QPushButton#rk_primary:disabled {
    background-color: #2b2c2e;
    color: #6f777f;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #121314;
    color: {FOREGROUND};
    border: 1px solid #1f2123;
    padding: 4px 6px;
    min-height: 22px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid {ACCENT};
}

QCheckBox {
    color: {FOREGROUND};
}

QCheckBox::indicator:unchecked {
    background: #101213;
    border: 1px solid #232526;
}

QCheckBox::indicator:checked {
    background: {ACCENT};
    border: 1px solid {ACCENT};
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
THEME_QSS = THEME_QSS.replace("{BACKGROUND}", BACKGROUND).replace("{SURFACE}", SURFACE).replace("{ACCENT}", ACCENT).replace("{FOREGROUND}", FOREGROUND).replace("{SECONDARY}", SECONDARY)


def apply_theme(app):
        """Apply the built QSS theme to the given QApplication.

        Calling code should ensure PySide6 is importable.
        """
        app.setStyleSheet(THEME_QSS)