try:
    #Qt5
    from PySide2.QtWidgets import *
    from PySide2.QtCore    import *
    from PySide2.QtGui     import *

except:
    #Qt6
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
        self.setLayout(self.layout)
        
        self.widget_label = QLabel("BoundaryEnhancementVolumeStyle")
        self.widget_label.setObjectName("X3DNodeType")
        
        self.layout.addWidget(self.widget_label)
        self.layout.addWidget(QTextEdit("Javascript:"))