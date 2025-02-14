try:
    #Qt5
    from PySide2           import QtCore
    from PySide2           import QtWidgets
    from PySide2.QtWebEngineWidgets import *
    from PySide2           import QtGui
    from PySide2.QtGui     import *
    from PySide2           import QMenu
    from PySide2.QtWidgets import *
    from PySide2.QtWidgets import QGraphicsItem as rkgItem
    from PySide2.QtCore    import *
    
    from shiboken2         import wrapInstance
    from shiboken2         import getCppPointer

except:
    #Qt6
    from PySide6           import QtCore
    from PySide6           import QtWidgets
    from PySide6.QtWebEngineWidgets import *
    from PySide6           import QtGui
    from PySide6.QtGui     import *
    from PySide6.QtWidgets import *
    from PySide6.QtWidgets import QGraphicsItem as rkgItem
    from PySide6.QtCore    import *
    from PySide6.QtWebEngineCore  import *
    
    from shiboken6         import wrapInstance
    from shiboken6         import getCppPointer
    
import sys

from screeninfo import get_monitors

########################################
# Not sure why I imported this
########################################
# from functools import partial

#Python API 1.0 needed to access MQtUtil
import maya.OpenMayaUI as omui
import maya.cmds as cmds

#Python API 2.0 needed to register command with API 2.0 plugin
import maya.api.OpenMaya as aom

#To get local file path for html file
from rawkee import RKWeb3D

#To geth other items from 'rawkee'
from rawkee.RKXScene   import RKXScene
from rawkee.RKXNodes   import RKXNode #notice the missing 's' - RKXNode is a test class
from rawkee.RKXSocket  import RKXSocket
from rawkee.RKGraphics import RKGraphicsView


from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

global rkWeb3D

class RKSceneEditor(MayaQWidgetDockableMixin, QWidget):
    
    OBJECT_NAME = "RKSceneEditor"
    
    @classmethod
    def scene_editor_control_name(cls):
        return "{0}WorkspaceControl".format(cls.OBJECT_NAME)
        
    @classmethod
    def workspace_ui_script(cls):
        return "from rawkee.RKSceneEditor import RKSceneEditor\nrkSEWidget = RKSceneEditor()"
        
    @classmethod
    def workplace_close_command(cls):
        return "self.cleanUpOnEditorClose()"

    
    def __init__(self):
        super().__init__()
        
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("RawKee X3D - Interaction Editor - Now with MORE X_ITE-ment AND x3dom (Freedom)!")
        self.setMinimumSize(600,400)
        
        self.node_editor_name = ""
        
        self.add_to_scene_editor_workspace_control()
        
        self.setURLPaths()
        
        self.create_actions()

        self.create_widgets()
        
        self.create_layout()
        
        self.create_connections()
        
        self.rkWeb3D = None
        
        self.node_editor_widget.centerView()
        
    def setRKWeb3D(self, rkWeb3D):
        # Maybe this should be moved to the constructor.
        # This is here so that the RKSceneEditor panel
        # can send and receive x3d.X3D objects with the 
        # MainMayaWindow RawKee GUI/Menu system.
        self.rkWeb3D = rkWeb3D
            
    def cleanUpOnEditorClose(self):
        # Release the RKWeb3D object, otherwise it will not
        # later be deleteable when the plugin unloads. If
        # the object is not deletable, then the __del__ 
        # method for that object will never be called during
        # the plugin unload, and thus the 'RawKee (X3D)' 
        # menu won't be removed from the MayaMainWindow
        # menubar.
        self.rkWeb3D = None

    def add_to_scene_editor_workspace_control(self):
        scene_editor_workspace_control = omui.MQtUtil.findControl(self.scene_editor_control_name())
        if scene_editor_workspace_control:
            scene_editor_workspace_control_ptr = int(scene_editor_workspace_control)
            scene_editor_widget_ptr = int(getCppPointer(self)[0])
            
            omui.MQtUtil.addWidgetToMayaLayout(scene_editor_widget_ptr, scene_editor_workspace_control_ptr)

    def setURLPaths(self):
        self.basePath = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
        
        ############################################################
        # Keep these for later use.
        # self.x_itePath = self.basePath + "/public/index.html"
        # self.x3domPath = self.basePath + "/auxilary/x3dom.html"
        
        self.x_itePath = "https://vr.csgrid.org/x_ite/index.html"
        self.x3domPath = "https://vr.csgrid.org/x3dom/index.html"
        
    def create_actions(self):
        #:menu_options.png
        self.newX3DScene    = QAction("   New X3D Scene")
        self.openX3DFile    = QAction("   Open X3D")
        self.exportX3DAs    = QAction("   Export X3D As...")
        #self.openX3DFile.setShortcut(QtGui.QKeySequence("Ctrl+S"))

        self.copySceneMaya  = QAction("   Copy Entire Maya Scene")
        self.copySelectMaya = QAction("   Copy Selected Maya Nodes")
        self.pasteSGToMaya  = QAction("   Paste Entire X3D Scenegraph")
        self.pasteSubToMaya = QAction("   Paste Selected X3D Subgraph")
        
        self.sendToSunrise  = QAction("   Sunrize X3D Editor")
        self.sendToCastle   = QAction("   Castle Game Engine")
        self.closeEditor    = QAction("   Close Editor")
#        self.testMenu       = QMenu()
#        self.qtBut          = QtWidgets.QPushButton()
#        self.qIcon          = QtGui.QIcon(":menu_options.png")
#        self.qIcon.setFixedSize(20, 20)
#        self.qtBut.setIcon(self.qIcon)
#        self.qtBut.setText("Push my button")
        
    def create_widgets(self):
        self.menu_bar    = QMenuBar()
        file_menu = self.menu_bar.addMenu("File")
    
        node_menu   = self.menu_bar.addMenu("X3D Nodes")
        about_menu  = self.menu_bar.addMenu("About RawKee")
        
        file_menu.addAction(self.newX3DScene)
        file_menu.addAction(self.openX3DFile)
        file_menu.addAction(self.exportX3DAs)
        file_menu.addSection("Maya Copy/Paste")
        file_menu.addAction(self.copySceneMaya)
        file_menu.addAction(self.copySelectMaya)
        file_menu.addSection(" ")
        file_menu.addAction(self.pasteSGToMaya)
        file_menu.addAction(self.pasteSubToMaya)
        file_menu.addSection("Send to External")
        file_menu.addAction(self.sendToSunrise)
        file_menu.addAction(self.sendToCastle)
        file_menu.addSeparator()
        file_menu.addAction(self.closeEditor)
        #file_menu.addAction(self.widget_action)
        #file_menu.addMenu(self.testMenu)
        
        self.splitter = QSplitter()
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setLineWidth(4)
        
        #############################################
        # X3D Tree Panel Widgets
        #self.treePanel = QGroupBox()
        #self.treePanelLabel = QLabel("X3D SceneGraph")
        #self.treePanelLabel.setMaximumHeight(20)
        #self.treePanelLabel.setMinimumHeight(20)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(['X3D Scenegraph'])
        self.tree_widget.setMaximumWidth(400)
        self.tree_widget.setMinimumWidth(250)

        child_item1 = QTreeWidgetItem(["Transform DEF='First'"])
        child_item2 = QTreeWidgetItem(["children"])
        child_item3 = QTreeWidgetItem(["Transform DEF='Second'"])
        child_item1.addChild(child_item2)
        child_item2.addChild(child_item3)        
        self.tree_widget.addTopLevelItem(child_item1)
        
        #############################################
        # X3D Player Panel Widgets
        self.view = QWebEngineView()

        # Box that holds the WebGL X_ITE / X3DOM canvas and the player controls
        self.playerPanel   = QGroupBox()

        self.playerControl = QGroupBox()
        
        self.plcLabel      = QLabel("X3D Player Controls")
        self.plcLabel.setMinimumHeight(25)
        self.plcLabel.setMaximumHeight(25)
        
        self.combo_box = QComboBox()
        self.combo_box.setMaximumWidth(450)
        self.combo_box.setMinimumWidth(250)
        self.combo_box.setMinimumHeight(25)
        self.combo_box.setMaximumHeight(25)
        self.combo_box.addItem("X_ITE - https://create3000.github.io/x_ite/")
        self.combo_box.addItem("X3DOM - https://www.x3dom.org/")
        
        ##############################################
        # Grabing the Maya Node Editor Panel
        ##### node_editor_panel = cmds.scriptedPanel(type="nodeEditorPanel")
        #self.node_editor_control = omui.MQtUtil.findControl(self.node_editor_panel)
        ##### print(node_editor_panel)
        ##### node_editor_control = omui.MQtUtil.findControl(node_editor_panel)
        
        self.node_editor_widget = RKCustomNodeEditor(parent=self)
        ##############################################
        # Creating a Tabbed Panel Widget to hold it all
        self.tab_widget = QTabWidget()
        
    def create_layout(self):
        #####################################################
        # X3D Player and Node Editor Layout                 #
        plr_layout = QtWidgets.QVBoxLayout()           #
                                                            #
        plrCtrl_layout  = QtWidgets.QHBoxLayout()
        plrCtrl_layout.addWidget(self.plcLabel)
        plrCtrl_layout.addWidget(self.combo_box)
        plrCtrl_layout.setContentsMargins(0,0,0,0)
        
        self.playerControl.setLayout(plrCtrl_layout)
        plr_layout.setContentsMargins(0,0,0,0)
        plr_layout.setSpacing(0)
        plr_layout.addWidget(self.playerControl)
        plr_layout.addWidget(self.view)
        self.playerPanel.setLayout(plr_layout)
        
        plr_layout.addLayout(plrCtrl_layout)
        plr_layout.addWidget(self.view, stretch=1)
        
        self.tab_widget.addTab(self.node_editor_widget, "X3D Node Editor")
        self.tab_widget.addTab(self.playerPanel, "X3D Player - X_ITE/X3DOM")
        
        ######################################################
        # Top Level Layout                                   #
        main_layout = QtWidgets.QHBoxLayout(self)            #
        main_layout.setMenuBar(self.menu_bar)                #
        
        self.splitter.addWidget(self.tab_widget)
        self.splitter.addWidget(self.tree_widget)
        main_layout.addWidget(self.splitter)
        #main_layout.addWidget(self.tab_widget)
        main_layout.setContentsMargins(0,0,0,0)
        
        #######################################################
        # Keep for later use.
        # self.playerURL = QUrl.fromLocalFile(self.x_itePath)
        self.playerURL = QUrl(self.x_itePath)
        self.view.setUrl(self.playerURL)
        
    def create_connections(self):

        # Adds functionality to switch between X_ITE and X3DOM
        self.combo_box.activated.connect(self.on_item_viewer_selection)


    def on_item_viewer_selection(self, index):

        # Get selected index for viewer
        # selected_text = self.combo_box.itemText(index)
        # print("Selected:", selected_text)
        if index == 0:
            self.playerURL = QUrl(self.x_itePath)
            #####################################################
            # Keep for later use.
            # self.playerURL = QUrl.fromLocalFile(self.x_itePath)
        elif index == 1:
            self.playerURL = QUrl(self.x3domPath)
            #####################################################
            # Keep for later use.
            # self.playerURL = QUrl.fromLocalFile(self.x3domPath)
            
        self.view.load(self.playerURL)


#####################################################################
# Implemented by following the NodeEditor Tutorial of BlenderFreak
# https://www.blenderfreak.com/tutorials/node-editor-tutorial-series/
#####################################################################
class RKCustomNodeEditor(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        #self.basePath = parent.basePath
        #self.stylesheet_filename = self.basePath + "/auxilary/rkNodeStyle.qss"
        #self.loadStyleSheet(self.stylesheet_filename)
        
        self.initUI()
        
    def initUI(self):
        self.layout = QVBoxLayout()
        self.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        self.scene = RKXScene()

        #Create Graphics View
        self.view = RKGraphicsView(self.scene.grScene, self)
        #self.view.setAlignment(Qt.AlignCenter)
        #self.view.setAlignment(Qt.AlignTop)
        self.layout.addWidget(self.view)
        
        # Adding an RKXNode for Development / Testing purposes.
        self.node1 = RKXNode(self.scene, "RawKeeNode 1", inputs=[1, 2, 3], outputs=[1])
        self.node1.setPos(0,0)
        node2 = RKXNode(self.scene, "RawKeeNode 2", inputs=[1, 2, 3], outputs=[1])
        node2.setPos(300,0)
        node3 = RKXNode(self.scene, "RawKeeNode 3", inputs=[1, 2, 3], outputs=[1])
        node3.setPos(600,0)
        
    def centerView(self):
        m = get_monitors()
        #s = self.geometry() #self.view.geometry()
        n = len(m)
        x = m[n-1].width  / 2
        y = m[n-1].height / 2
        
        self.view.centerOn(x+(y/2), y/2)
        
        for m in get_monitors():
            print(str(m))

        '''
        print("Viewport - Width: " + str(x2) + ", Height: " + str(y2))
        mPoint = self.view.mapFromScene(QPointF(0.0,0.0))
        
        pstr = "X: " + str(mPoint.x()) + ", Y: " + str(mPoint.y())
        
        mRect = self.view.sceneRect()
        print(pstr)
        print(mRect)
        '''
        
        
    def addDebugContent(self):
        greenBrush = QBrush(Qt.green)
        outlinePen = QPen(Qt.black)
        outlinePen.setWidth(2)
        
        myRect = self.grScene.addRect(-100, -100, 80, 100, outlinePen, greenBrush)
        myRect.setFlag(rkgItem.ItemIsMovable)
        
        myText = self.grScene.addText("This is my Text!", QFont("Broadway"))
        myText.setFlag(rkgItem.ItemIsSelectable)
        myText.setFlag(rkgItem.ItemIsMovable)
        myText.setDefaultTextColor(QColor.fromRgbF(1.0, 1.0, 1.0))
        
        widget1 = QPushButton("Don't Push!")
        proxy1  = self.grScene.addWidget(widget1)
        proxy1.setFlag(rkgItem.ItemIsMovable)
        proxy1.setPos(0, 30)
        
        widget2 = QTextEdit()
        proxy2  = self.grScene.addWidget(widget2)
        proxy2.setFlag(rkgItem.ItemIsSelectable)
        proxy2.setPos(0, 60)
        
        myLine = self.grScene.addLine(-200, -200, 400, -100, outlinePen)
        myLine.setFlag(rkgItem.ItemIsSelectable)
        myLine.setFlag(rkgItem.ItemIsMovable)
        
    #def loadStyleSheet(self, filename):
    #    print('STYLE loading', filename)
    #    
    #    file = QFile(filename)
    #    file.open(QFile.ReadOnly | QFile.Text)
    #    stylesheet = file.readAll()
    #    
    #    #self.setStyleSheet(str(stylesheet, encoding='utf-8'))
    #    QApplication.instance().setStyleSheet(str(stylesheet, encoding='utf-8'))
        

'''
if __name__ == "__main__":

    sceneEditorControlName = RKSceneEditor.scene_editor_control_name()

    if cmds.workspaceControl(sceneEditorControlName, exists=True):
        #Must Close before Delete
        cmds.workspaceControl(sceneEditorControlName, e=True, close=True)
        cmds.deleteUI(sceneEditorControlName)
    
    rkSEditor = RKSceneEditor()
    rkSEditor.show(dockable=True, uiScript=RKSceneEditor.workspace_ui_script())
'''
