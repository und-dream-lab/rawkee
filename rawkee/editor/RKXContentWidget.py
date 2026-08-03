from PySide6.QtWidgets import *
from PySide6.QtCore    import *
from PySide6.QtGui     import *

class RKXContentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.initUI()
        
    def initUI(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        
        self.widget_label = QLabel()
        self.widget_label.setObjectName("X3DNodeType")
        self.widget_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.widget_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.widget_label.setStyleSheet(
            "background-color: #2a2a2a; color: #39FF14;"
            "font-weight: bold; padding: 3px 4px 6px 4px;"
        )
        
        self.layout.addWidget(self.widget_label)
        self.layout.addStretch()

    def setNodeType(self, type_name):
        self.widget_label.setText(type_name)