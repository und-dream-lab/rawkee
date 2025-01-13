#Chris Zurbrigg - Windows and Dialogs Tutorial

try:
    from PySide2 import QtCore
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance
except:
    from PySide6 import QtCore
    from PySide6 import QtWidgets
    from shiboken6 import wrapInstance

import sys
import maya.OpenMayaUI as omui
    
def mayaMainWindow():
    mainWindowPtr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPtr), QtWidgets.QMainWindow) #.QWidget)
    

class MainToolWindow(QtWidgets.QDialog):
    
    def __init__(self, parent=mayaMainWindow()):
        super().__init__(parent)
        
        self.setWindowTitle("Windows and Dialogs")
        self.setMinimumSize(400,300)
        
        # On MacOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)
            
        self.button_a = QtWidgets.QPushButton("Button A")
        self.button_b = QtWidgets.QPushButton("Button B")
        
        main_layout = QtWidgets.QVBoxLayout()
        
        self.setLayout(main_layout)
        
        main_layout.addStretch()
        main_layout.addWidget(self.button_a)
        main_layout.addWidget(self.button_b)
        main_layout.addStretch()
        
            
        
if __name__ == "__main__":
    win = MainToolWindow()
    win.show()
    
    
