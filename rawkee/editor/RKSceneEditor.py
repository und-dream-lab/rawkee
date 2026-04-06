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
from rawkee.maya import RKWeb3D

#To geth other items from 'rawkee'
import rawkee.io.RKx3d as rkx
from rawkee.editor.RKXScene   import RKXScene
from rawkee.editor.RKXNodes   import RKXNode #notice the missing 's' - RKXNode is a test class
from rawkee.editor.RKXSocket  import RKXSocket
from rawkee.editor.RKGraphics   import RKGraphicsView

# Needed to run a local server for X_ITE 14.1.0
import http.server
import threading
from   functools import partial

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

global rkWeb3D


###########################################################################
# Custom QTreeWidget that enables dragging X3D nodes into the node editor.
###########################################################################
class RKX3DTreeWidget(QTreeWidget):

    MIME_TYPE = "application/x-rawkee-x3d-node"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._node_registry = {}  # str(id(node)) -> rkx node object
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def registerNode(self, node):
        """Store node in registry and return its key string."""
        key = str(id(node))
        self._node_registry[key] = node
        return key

    def nodeForKey(self, key):
        return self._node_registry.get(key)

    def clearRegistry(self):
        self._node_registry.clear()

    def mimeData(self, items):
        mime = QMimeData()
        # Only drag items that carry a node key (ignore field-group items)
        for item in items:
            key = item.data(0, Qt.UserRole)
            if key:
                mime.setData(self.MIME_TYPE, key.encode('utf-8'))
                break
        return mime


###########################################################################
# RKGraphicsView subclass that accepts X3D node drops from the tree widget.
###########################################################################
class RKNodeEditorDropView(RKGraphicsView):

    def __init__(self, grScene, tree_widget, parent=None):
        super().__init__(grScene, parent)
        self._tree_widget = tree_widget
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(RKX3DTreeWidget.MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(RKX3DTreeWidget.MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(RKX3DTreeWidget.MIME_TYPE):
            key = bytes(event.mimeData().data(RKX3DTreeWidget.MIME_TYPE)).decode('utf-8')
            x3d_node = self._tree_widget.nodeForKey(key)
            if x3d_node is not None:
                scene_pos = self.mapToScene(event.pos())
                parent_editor = self.parent()
                if parent_editor and hasattr(parent_editor, 'addNodeFromX3D'):
                    parent_editor.addNodeFromX3D(x3d_node, scene_pos)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class RKSceneEditor(MayaQWidgetDockableMixin, QWidget):
    
    OBJECT_NAME = "RKSceneEditor"
    
    @classmethod
    def scene_editor_control_name(cls):
        return "{0}WorkspaceControl".format(cls.OBJECT_NAME)
        
    @classmethod
    def workspace_ui_script(cls):
        return "from rawkee.editor.RKSceneEditor import RKSceneEditor\nrkSEWidget = RKSceneEditor()"
        
    @classmethod
    def workplace_close_command(cls):
        return "self.cleanUpOnEditorClose()"

    
    def __init__(self):
        super().__init__()
        
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("RawKee PE - X3D Graph Editor (Scene and Interactions) with X_ITE Display - Under Development")
        self.setMinimumSize(600,400)
        
        self.node_editor_name = ""
        
        self.add_to_scene_editor_workspace_control()
        
        self.setURLPaths()
        
        self.create_actions()

        self.create_widgets()
        
        self.create_layout()
        
        self.create_connections()
        
        self.rkWeb3D = None
        self.bkHost  = None
        self.httpd   = None


    def setX3DScene(self, x3dScene):
        """Populate the tree widget from an rkx.Scene object produced by maya2x3d()."""
        self._x3dScene = x3dScene
        self._build_scene_tree(x3dScene)

    def _build_scene_tree(self, scene):
        self.tree_widget.clearRegistry()
        self.tree_widget.clear()
        if scene is None:
            return
        for node in scene.children:
            item = self._make_tree_item(node)
            if item:
                self.tree_widget.addTopLevelItem(item)

    def _make_tree_item(self, node):
        # Skip ROUTE statements — they are not displayed in the tree
        if isinstance(node, rkx.ROUTE):
            return None

        # USE reference — shown read-only, not draggable
        use_val = getattr(node, 'USE', '')
        if use_val:
            node_type = type(node).NAME()
            return QTreeWidgetItem(["USE '{}' ({})".format(use_val, node_type)])

        # Regular node — register it so it can be dragged into the node editor
        node_type = type(node).NAME()
        def_name  = getattr(node, 'DEF', '')
        label = "{} DEF='{}'".format(node_type, def_name) if def_name else node_type
        item  = QTreeWidgetItem([label])
        item.setData(0, Qt.UserRole, self.tree_widget.registerNode(node))

        # Recurse into child node fields using FIELD_DECLARATIONS
        if hasattr(type(node), 'FIELD_DECLARATIONS'):
            _SKIP = {'class_', 'id_', 'style_', 'IS'}
            for decl in type(node).FIELD_DECLARATIONS():
                field_name = decl[0]
                if field_name in _SKIP:
                    continue
                # decl[2] is FieldType.<Type> — call it to get the type string
                try:
                    field_type = decl[2]()
                except Exception:
                    field_type = ''
                if field_type not in ('SFNode', 'MFNode'):
                    continue
                try:
                    value = getattr(node, field_name, None)
                except Exception:
                    continue
                if value is None:
                    continue
                if isinstance(value, list):
                    child_nodes = [v for v in value if hasattr(v, 'NAME')]
                    if child_nodes:
                        field_item = QTreeWidgetItem([field_name])
                        for child_node in child_nodes:
                            child_item = self._make_tree_item(child_node)
                            if child_item:
                                field_item.addChild(child_item)
                        item.addChild(field_item)
                elif hasattr(value, 'NAME'):
                    field_item = QTreeWidgetItem([field_name])
                    child_item = self._make_tree_item(value)
                    if child_item:
                        field_item.addChild(child_item)
                    item.addChild(field_item)
        return item

    def centerNodeEditor(self, qpoint=QPointF(0,0)):
        self.node_editor_widget.centerViewOn(qpoint)

        
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
        if self.bkHost:
            self.bkHost.stop()
            self.bkHost  = None
        self.rkWeb3D = None


    def add_to_scene_editor_workspace_control(self):
        scene_editor_workspace_control = omui.MQtUtil.findControl(self.scene_editor_control_name())
        if scene_editor_workspace_control:
            scene_editor_workspace_control_ptr = int(scene_editor_workspace_control)
            scene_editor_widget_ptr = int(getCppPointer(self)[0])
            
            omui.MQtUtil.addWidgetToMayaLayout(scene_editor_widget_ptr, scene_editor_workspace_control_ptr)

    def setURLPaths(self):
        module_name = self.__class__.__module__
        self.basePath = sys.modules[module_name].__file__.replace("\\", "/").rsplit("/", 1)[0]
        
        ############################################################
        # Keep these for later use.
        self.serverPath = self.basePath + "/x_ite/x_ite-14.1.0"
        self.port = 8000

        self.x_itePath  = "https://create3000.github.io/x_ite/playground/?play=false&fullSize=true"
        #http://localhost:{self.port}"
        #self.x_itePath  = "https://vr.csgrid.org/x_ite/index.html"

        #self.bkHost = RKBackgroundHost(directory=self.serverPath, port=self.port)
        #self.bkHost.start()
        
        
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
        
        self.tree_widget = RKX3DTreeWidget()
        self.tree_widget.setHeaderLabels(['X3D Scenegraph'])
        self.tree_widget.setMaximumWidth(400)
        self.tree_widget.setMinimumWidth(250)
        
        #############################################
        # X3D Player Panel Widgets
        self.view = QWebEngineView()
        print(self.view.page().profile().httpUserAgent())
        
        self.custom_page = RKCustomWebEnginePage(self.view)
        self.view.setPage(self.custom_page)

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
        self.combo_box.addItem("X_ITE - https://create3000.github.io/x_ite/playground/?play=false&fullSize=true")
        #self.combo_box.addItem("X3DOM - https://www.x3dom.org/")
        
        ##############################################
        # Grabing the Maya Node Editor Panel
        ##### node_editor_panel = cmds.scriptedPanel(type="nodeEditorPanel")
        #self.node_editor_control = omui.MQtUtil.findControl(self.node_editor_panel)
        ##### print(node_editor_panel)
        ##### node_editor_control = omui.MQtUtil.findControl(node_editor_panel)
        
        self.node_editor_widget = RKCustomNodeEditor(self.tree_widget, parent=self)
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
        
        self.tab_widget.addTab(self.node_editor_widget, "X3D Graph Editor")
        self.tab_widget.addTab(self.playerPanel, "X3D Player - X_ITE")
        
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
        #elif index == 1:
        #    self.playerURL = QUrl(self.x3domPath)
            #####################################################
            # Keep for later use.
            # self.playerURL = QUrl.fromLocalFile(self.x3domPath)
            
        self.view.load(self.playerURL)
        
    
    def stopWebserver(self):
        if self.httpd:
            print("Shutting down server...")
            # .shutdown() stops the serve_forever() loop
            self.httpd.shutdown() 
            # .server_close() closes the socket properly
            self.httpd.server_close()


class RKCustomWebEnginePage(QWebEnginePage):
    """
    A custom QWebEnginePage to capture and display console messages.
    """
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceId):
        """
        Overrides the method to print JavaScript console messages to the console.
        """
        # Format the output for clarity
        level_str = "INFO"
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel:
            level_str = "WARNING"
        elif level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            level_str = "ERROR"
        
        print(f"WEB_CONSOLE [{level_str}] {sourceId}:{lineNumber}: {message}")


class RKBackgroundHost:
    def __init__(self, directory=".", port=8000):
        self.port = port
        self.directory = directory
        self.handler = partial(http.server.SimpleHTTPRequestHandler, directory=directory)
        self.httpd = http.server.HTTPServer(("", port), self.handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def start(self):
        self.thread.start()
        print(f"Server started at http://localhost:{self.port} (Root: {self.directory})")

    def stop(self):
        print("Shutting down server...")
        self.httpd.shutdown() # Stops the serve_forever loop
        self.httpd.server_close() # Releases the port
        self.thread.join() # Ensures the thread has finished
        print("Server stopped.")    


#####################################################################
# Implemented by following the NodeEditor Tutorial of BlenderFreak
# https://www.blenderfreak.com/tutorials/node-editor-tutorial-series/
#####################################################################
class RKCustomNodeEditor(QWidget):
    
    def __init__(self, tree_widget=None, parent=None):
        super().__init__(parent)
        self._tree_widget = tree_widget
        
        #self.basePath = parent.basePath
        #self.stylesheet_filename = self.basePath + "/auxilary/rkNodeStyle.qss"
        #self.loadStyleSheet(self.stylesheet_filename)
        
        self.initUI()
        
    def initUI(self):
        self.layout = QVBoxLayout()
        self.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        self.scene = RKXScene()

        # Use the drop-enabled view if a tree widget was provided
        if self._tree_widget is not None:
            self.view = RKNodeEditorDropView(self.scene.grScene, self._tree_widget, self)
        else:
            self.view = RKGraphicsView(self.scene.grScene, self)
        self.layout.addWidget(self.view)
        
        # Adding an RKXNode for Development / Testing purposes.
        self.node1 = RKXNode(self.scene, "RawKeeNode 1", inputs=[1, 2, 3], outputs=[1])
        self.node1.setPos(0,0)
        node2 = RKXNode(self.scene, "RawKeeNode 2", inputs=[1, 2, 3], outputs=[1])
        node2.setPos(300,0)
        node3 = RKXNode(self.scene, "RawKeeNode 3", inputs=[1, 2, 3], outputs=[1])
        node3.setPos(600,0)

    def addNodeFromX3D(self, x3d_node, scene_pos):
        """Create an RKXNode in the editor canvas from a dropped rkx node object."""
        node_type = type(x3d_node).NAME()
        def_name  = getattr(x3d_node, 'DEF', '')
        title = "{} DEF='{}'".format(node_type, def_name) if def_name else node_type

        inputs  = []
        outputs = []
        if hasattr(type(x3d_node), 'FIELD_DECLARATIONS'):
            for decl in type(x3d_node).FIELD_DECLARATIONS():
                field_name = decl[0]
                try:
                    access_str = decl[3]()
                except Exception:
                    access_str = ''
                if access_str in ('inputOnly', 'inputOutput'):
                    inputs.append(field_name)
                if access_str in ('outputOnly', 'inputOutput'):
                    outputs.append(field_name)

        new_node = RKXNode(self.scene, title, inputs=inputs, outputs=outputs)
        new_node.setPos(scene_pos.x(), scene_pos.y())

    def centerViewOn(self, qpoint=QPointF(0,0)):
        self.view.centerOn(qpoint)
        
        
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
