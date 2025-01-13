try:
    #Qt5
    from PySide2           import QtCore
    from PySide2           import QtWidgets
    from PySide2           import QtWebEngineWidgets
    from PySide2           import QtGui
    from PySide2           import QMenu
    from PySide2.QtWidgets import QAction
    from PySide2.QtWidgets import QMenu
    from shiboken2         import wrapInstance

except:
    #Qt6
    from PySide6           import QtCore
    from PySide6           import QtWidgets
    from PySide6           import QtWebEngineWidgets
    from PySide6           import QtGui
    from PySide6.QtGui     import QAction
    from PySide6.QtWidgets import QMenu
    from shiboken6         import wrapInstance

import sys

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds

def mayaMainWindow():
    mainWindowPtr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPtr), QtWidgets.QWidget)
    
class RKXITE(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent=mayaMainWindow()):
        super(RKXITE, self).__init__(parent)
        
        self.setWindowTitle("RawKee with X_ITE")
        self.setMinimumSize(400,100)

        #On macOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)
            
    def createWidgets(self):
        pass
        
    def creatLayout(self):
        pass
        
    def createConnections(self):
        pass
        
        
if __name__ == "__main__":
    try:
        openImportDialog.close()
        openImportDialog.deleteLater()
    except:
        pass
        
    openImportDialog = RKXITE()
    openImportDialog.show()
        
        
    
    