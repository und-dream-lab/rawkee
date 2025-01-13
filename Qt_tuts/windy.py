#Chris Zurbrigg - Windows and Dialogs Tutorial

try:
    from PySide2 import QtCore
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance
except:
    from PySide6 import QtCore
    from PySide6 import QtWidgets
    from shiboken6 import wrapInstance

import maya.OpenMayaUI as omui
    
def mayaMainWindow():
    mainWindowPtr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPtr), QtWidgets.QWidget)
    

class MainToolWindow(QtWidgets.QDialog):
    
    def __init__(self, parent=mayaMainWindow()):
        super().__init__(parent)
        
        self.setWindowTitle("Windows and Dialogs")
        self.setMinimumSize(400,300)
        
if __name__ == "__main__":
    win = MainToolWindow()
    win.show()
    
    
