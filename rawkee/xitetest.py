try:
    #Qt5
    from PySide2           import QtCore
    from PySide2           import QtWidgets
    from PySide2.QtWebEngineWidgets import QWebEngineView
    from PySide2           import QtGui
    from PySide2           import QMenu
    from PySide2.QtWidgets import QAction
    from PySide2.QtWidgets import QMenu, QApplication
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
    from PySide6.QtWidgets import QMenu, QApplication
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

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-logging --log-level=3 --remote-debugging-port=2345"
os.environ["QT_LOGGING_RULES"] = "qt.webenginecontext.debug=true"

url = "https://vr.csgrid.org/x_ite/"

def mayaMainWindow():
    mainWindowPtr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPtr), QtWidgets.QWidget)
    
def main(args):
   app = QApplication(args)

   settings = QWebEngineProfile.defaultProfile().settings()
   settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

   # QWebEngineView
   browser = QWebEngineView()
   browser.load(QUrl(url))
   browser.show()

   sys.exit(app.exec_())

if __name__ == "__main__":
   main(sys.argv)

   