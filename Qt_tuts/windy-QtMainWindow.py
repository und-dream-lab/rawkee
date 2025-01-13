#Chris Zurbrigg - Windows and Dialogs Tutorial

try:
    from PySide2 import QtCore
    from PySide2 import QtWidgets
    from PySide2 import QtGui
    from shiboken2 import wrapInstance
    
    from PySide2.QtWidget import QAction
except:
    from PySide6 import QtCore
    from PySide6 import QtWidgets
    from PySide6 import QtGui
    from shiboken6 import wrapInstance
    
    from PySide6.QtGui import QAction

import sys
import maya.OpenMayaUI as omui
    
def mayaMainWindow():
    mainWindowPtr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPtr), QtWidgets.QMainWindow)#.QWidget)
    

class MainToolWindow(QtWidgets.QMainWindow):
    
    def __init__(self, parent=mayaMainWindow()):
        super().__init__(parent)
        
        self.setWindowTitle("Windows and Dialogs")
        self.setMinimumSize(400,300)
        
        # On MacOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)
        
        self.creatActions()
        
        self.menuBar().addMenu("File")
        self.menuBar().addMenu("Edit")
        self.menuBar().addMenu("Barf")
    
    def creatActions():
        print("Barf!!!")
        self.addItemAction = QAction("Barf")
        self.clearAction = QAction("Barf All")
        
if __name__ == "__main__":
    win = MainToolWindow()
    win.show()
    
    
