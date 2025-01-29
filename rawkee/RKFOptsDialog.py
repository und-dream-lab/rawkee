#import os
#os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = "--disable-gpu"
#os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = "--enable-blink-features=InterestCohortAPI --enable-features='FederatedLearningOfCohorts:update_interval/10s/minimum_history_domain_size_required/1,FlocIdSortingLshBasedComputation,InterestCohortFeaturePolicy'"

try:
    #Qt5
    from PySide2           import QtCore
    from PySide2           import QtWidgets
    from PySide2.QtWebEngineWidgets import QWebEngineView
    from PySide2           import QtGui
    from PySide2           import QMenu
    from PySide2.QtWidgets import QAction
    from PySide2.QtWidgets import QMenu
    from PySide2.QtCore    import QUrl
    from PySide2.QtWebEngineWidgets import QWebEngineSettings
    from PySide2.QtWebEngineWidgets import QWebEnginePage
    from PySide2.QtQui import QDesktopServices

    from PySide2.QtCore import QLoggingCategory, qInstallMessageHandler
    
    from shiboken2         import wrapInstance

except:
    #Qt6
    from PySide6           import QtCore
    from PySide6           import QtWidgets
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6           import QtGui
    from PySide6.QtGui     import QAction
    from PySide6.QtWidgets import QMenu
    from PySide6.QtCore    import QUrl
    from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, qWebEngineVersion, qWebEngineChromiumVersion, qWebEngineChromiumSecurityPatchVersion
    from PySide6.QtWebEngineCore import QWebEnginePage
    from PySide6.QtGui import QDesktopServices
    
    from PySide6.QtCore import qInstallMessageHandler, QtMsgType, QMessageLogContext
    
    from shiboken6         import wrapInstance

import sys

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds

#######################################
# Don't remember why this is here
#######################################
# import inspect
# import maya.standalone as mst
# print(inspect.getfile(mst))

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-logging --log-level=3 --remote-debugging-port=2345"
os.environ["QT_LOGGING_RULES"] = "qt.webenginecontext.debug=true"


print("Qt: v", PySide6.QtCore.__version__, "\tPyQt: v", PySide6.__version__)

def mayaMainWindow():
    mainWindowPtr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPtr), QtWidgets.QWidget)
    
def handleJSConsoleMessage(msg_type, context, msg):
    # Format the message based on its type
    if msg_type == QtMsgType.QtDebugMsg:
        msg_type_str = "Debug"
    elif msg_type == QtMsgType.QtWarningMsg:
        msg_type_str = "Warning"
    elif msg_type == QtMsgType.QtCriticalMsg:
        msg_type_str = "Critical"
    elif msg_type == QtMsgType.QtFatalMsg:
        msg_type_str = "Fatal"
    else:
        msg_type_str = "Unknown"

    # Print the formatted message
    print(f"{msg_type_str}: {msg}")    
                
class RKFOptsDialog(QtWidgets.QDialog):
    def __init__(self, parent=mayaMainWindow()):
        super(RKFOptsDialog, self).__init__(parent)
        
        self.setWindowTitle("RawKee (X3D) wtih X_ITE")
        self.setMinimumSize(600,400)

        #On macOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)
            
 #       self.createLayout()
        self.createWidgets()
            
    def createWidgets(self):
        qInstallMessageHandler(handleJSConsoleMessage)

        layout = QtWidgets.QVBoxLayout()
        
        settings = QWebEngineProfile.defaultProfile().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        
        view = QWebEngineView()

#        view.javaScriptConsoleMessage.connect(handleJSConsoleMessage)
       
        layout.addWidget(view)
#        view.setHtml('<!DOCTYPE html><html><head><meta charset="utf-8"><script defer src="https://cdn.jsdelivr.net/npm/x_ite@11.0.2/dist/x_ite.min.js"></script><style>x3d-canvas{width: 768px; height: 432px;}</style></head><body><x3d-canvas src="https://www.web3d.org/x3d/content/examples/Basic/NURBS/FredTheBunny.x3d"></x3d-canvas></body></html>')
#        view.setUrl(QUrl("https://vr.csgrid.org/x_ite/pum___p.html"))
        view.setUrl(QUrl("http://localhost:8080/"))
#        view.setUrl(QUrl("https://www.x3dom.org/"))
#        view.show()
#        view.setUrl(QUrl("https://create3000.github.io/x_ite/dom-integration/"))
#        view.setUrl(QUrl("https://get.webgl.org/"))
#        view.setUrl(QUrl("chrome://gpu"))
        self.setLayout(layout)
#        view.show()
#        QDesktopServices.openUrl("https://create3000.github.io/x_ite/playground/")


        print(qWebEngineVersion())
        print(qWebEngineChromiumVersion())
    
    def printMessages(self):
        print("Blah")
        
    def createLayout(self):
        pass
        
    def createConnections(self):
        pass
        
        
if __name__ == "__main__":
    try:
        openImportDialog.close()
        openImportDialog.deleteLater()
    except:
        pass
        
    openImportDialog = RKFOptsDialog()
    openImportDialog.show()
        
        
    
    