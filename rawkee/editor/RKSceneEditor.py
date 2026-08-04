from PySide6           import QtCore
from PySide6           import QtWidgets
from PySide6.QtWebEngineWidgets import *
from PySide6           import QtGui
from PySide6.QtGui     import *
from PySide6.QtWidgets import *
from PySide6.QtWidgets import QGraphicsItem as rkgItem
from PySide6.QtCore    import *
from PySide6.QtWebEngineCore  import *

import os
import sys
import http.server
import threading
from functools import partial

import rawkee.io.RKx3d as rkx
from rawkee.io.RKLoadSceneFromFile import RKLoadSceneFromFile
from rawkee.io.RKSceneTraversal import RKSceneTraversal

# Pure outputOnly/inputOnly event fields missing from FIELD_DECLARATIONS in RKx3d.py.
# Format: {NodeTypeName: [(field_name, field_type, access)]}  access = 'inputOnly'|'outputOnly'
_EXTRA_EVENT_FIELDS = {
    'TimeSensor': [
        ('cycleTime',        'SFTime',    'outputOnly'),
        ('elapsedTime',      'SFTime',    'outputOnly'),
        ('fraction_changed', 'SFFloat',   'outputOnly'),
        ('isActive',         'SFBool',    'outputOnly'),
        ('isPaused',         'SFBool',    'outputOnly'),
        ('time',             'SFTime',    'outputOnly'),
    ],
    'PositionInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFVec3f',    'outputOnly'),
    ],
    'PositionInterpolator2D': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFVec2f',    'outputOnly'),
    ],
    'OrientationInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFRotation', 'outputOnly'),
    ],
    'ColorInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFColor',    'outputOnly'),
    ],
    'ScalarInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFFloat',    'outputOnly'),
    ],
    'NormalInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'MFVec3f',    'outputOnly'),
    ],
    'CoordinateInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'MFVec3f',    'outputOnly'),
    ],
    'CoordinateInterpolator2D': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'MFVec2f',    'outputOnly'),
    ],
    'SquadOrientationInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFRotation', 'outputOnly'),
    ],
    'SplinePositionInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFVec3f',    'outputOnly'),
    ],
    'SplinePositionInterpolator2D': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFVec2f',    'outputOnly'),
    ],
    'SplineScalarInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFFloat',    'outputOnly'),
    ],
    'EaseInEaseOut': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('modifiedFraction_changed', 'SFFloat', 'outputOnly'),
    ],
    'TouchSensor': [
        ('hitNormal_changed',   'SFVec3f',  'outputOnly'),
        ('hitPoint_changed',    'SFVec3f',  'outputOnly'),
        ('hitTexCoord_changed', 'SFVec2f',  'outputOnly'),
        ('isActive',            'SFBool',   'outputOnly'),
        ('isOver',              'SFBool',   'outputOnly'),
        ('touchTime',           'SFTime',   'outputOnly'),
    ],
    'ProximitySensor': [
        ('centerOfRotation_changed', 'SFVec3f',    'outputOnly'),
        ('isActive',                 'SFBool',     'outputOnly'),
        ('orientation_changed',      'SFRotation', 'outputOnly'),
        ('position_changed',         'SFVec3f',    'outputOnly'),
        ('enterTime',                'SFTime',     'outputOnly'),
        ('exitTime',                 'SFTime',     'outputOnly'),
    ],
    'VisibilitySensor': [
        ('isActive',   'SFBool', 'outputOnly'),
        ('enterTime',  'SFTime', 'outputOnly'),
        ('exitTime',   'SFTime', 'outputOnly'),
    ],
    'PlaneSensor': [
        ('isActive',           'SFBool',   'outputOnly'),
        ('isOver',             'SFBool',   'outputOnly'),
        ('translation_changed','SFVec3f',  'outputOnly'),
        ('trackPoint_changed', 'SFVec3f',  'outputOnly'),
    ],
    'CylinderSensor': [
        ('isActive',           'SFBool',    'outputOnly'),
        ('isOver',             'SFBool',    'outputOnly'),
        ('rotation_changed',   'SFRotation','outputOnly'),
        ('trackPoint_changed', 'SFVec3f',   'outputOnly'),
    ],
    'SphereSensor': [
        ('isActive',           'SFBool',    'outputOnly'),
        ('isOver',             'SFBool',    'outputOnly'),
        ('rotation_changed',   'SFRotation','outputOnly'),
        ('trackPoint_changed', 'SFVec3f',   'outputOnly'),
    ],
    'KeySensor': [
        ('actionKeyPress',   'SFInt32', 'outputOnly'),
        ('actionKeyRelease', 'SFInt32', 'outputOnly'),
        ('altKey',           'SFBool',  'outputOnly'),
        ('controlKey',       'SFBool',  'outputOnly'),
        ('isActive',         'SFBool',  'outputOnly'),
        ('keyPress',         'SFString','outputOnly'),
        ('keyRelease',       'SFString','outputOnly'),
        ('shiftKey',         'SFBool',  'outputOnly'),
    ],
    'StringSensor': [
        ('enteredText',  'SFString', 'outputOnly'),
        ('finalText',    'SFString', 'outputOnly'),
        ('isActive',     'SFBool',   'outputOnly'),
    ],
    'BooleanFilter': [
        ('set_boolean',    'SFBool', 'inputOnly'),
        ('inputFalse',     'SFBool', 'outputOnly'),
        ('inputNegate',    'SFBool', 'outputOnly'),
        ('inputTrue',      'SFBool', 'outputOnly'),
    ],
    'BooleanToggle': [
        ('set_boolean', 'SFBool', 'inputOnly'),
    ],
    'BooleanTrigger': [
        ('set_triggerTime', 'SFTime', 'inputOnly'),
        ('triggerTrue',     'SFBool', 'outputOnly'),
    ],
    'IntegerTrigger': [
        ('set_boolean',       'SFBool',  'inputOnly'),
        ('triggerValue',      'SFInt32', 'outputOnly'),
    ],
    'TimeTrigger': [
        ('set_boolean',  'SFBool', 'inputOnly'),
        ('triggerTime',  'SFTime', 'outputOnly'),
    ],
}
from rawkee.editor.RKXScene   import RKXScene
from rawkee.editor.RKXNodes   import RKXNode
from rawkee.editor.RKXSocket  import RKXSocket
from rawkee.editor.RKGraphics import RKGraphicsView


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


class RKSceneEditor(QMainWindow):
    
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

    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("RawKee PE - X3D Interaction Editor")
        self.setMinimumSize(900, 600)

        self.node_editor_name = ""

        self.setURLPaths()
        self.create_actions()
        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.bkHost  = None
        self.httpd   = None
        self._x3dObj = None  # full rkx.X3D object kept in memory


    def setX3DScene(self, x3dScene):
        """Populate the tree widget from an rkx.Scene object produced by maya2x3d()."""
        self._x3dScene = x3dScene
        self._build_scene_tree(x3dScene)
        self.node_editor_widget.set_x3d_scene(x3dScene)

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

        # USE reference — register for drag so addNodeFromX3D can resolve it to the DEF node
        use_val = getattr(node, 'USE', '')
        if use_val:
            node_type = type(node).NAME()
            item = QTreeWidgetItem(["USE '{}' ({})".format(use_val, node_type)])
            item.setData(0, Qt.UserRole, self.tree_widget.registerNode(node))
            return item

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
        # Reserved for future DCC-host integration.
        pass

    def cleanUpOnEditorClose(self):
        if self.bkHost:
            self.bkHost.stop()
            self.bkHost = None

    def closeEvent(self, event):
        self.cleanUpOnEditorClose()
        super().closeEvent(event)

    def setURLPaths(self):
        module_name = self.__class__.__module__
        self.basePath = sys.modules[module_name].__file__.replace("\\", "/").rsplit("/", 1)[0]
        
        ############################################################
        # Keep these for later use.
        #self.serverPath = self.basePath + "/x_ite/x_ite-14.1.0"
        #self.port = 8000

        self.x_itePath = "https://und-dream-lab.github.io/rawkee/rawkee/examples/x_ite.html?v=20260803"
        #self.x_itePath  = "https://create3000.github.io/x_ite/playground/?play=false&fullSize=true"
        #http://localhost:{self.port}"
        #self.x_itePath  = "https://vr.csgrid.org/x_ite/index.html"

        #self.bkHost = RKBackgroundHost(directory=self.serverPath, port=self.port)
        #self.bkHost.start()
        
        
    def create_actions(self):
        self.newX3DScene    = QAction("   New X3D Scene")
        self.openX3DFile    = QAction("   Open X3D")
        self.exportX3DAs    = QAction("   Export X3D As...")
        #self.openX3DFile.setShortcut(QtGui.QKeySequence("Ctrl+S"))

        self.clearGraphAction = QAction("   Clear Graph Editor")
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
        file_menu   = self.menuBar().addMenu("File")
        node_menu   = self.menuBar().addMenu("X3D Nodes")
        about_menu  = self.menuBar().addMenu("About RawKee") # noqa: F841
        node_menu.addAction(self.clearGraphAction)

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

        self.tree_widget = RKX3DTreeWidget()
        self.tree_widget.setHeaderLabels(['X3D Scenegraph'])
        self.tree_widget.setMaximumWidth(400)
        self.tree_widget.setMinimumWidth(250)

        self.browser = QWebEngineView()
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        self.custom_page = RKCustomWebEnginePage(self.browser)
        self.browser.setPage(self.custom_page)

        self.node_editor_widget = RKCustomNodeEditor(self.tree_widget, parent=self)

        self.console_widget = QPlainTextEdit()
        self.console_widget.setReadOnly(True)
        self.console_widget.setMaximumHeight(180)
        self.console_widget.setMinimumHeight(60)
        self.console_widget.setPlaceholderText("Output / Errors")
        self.custom_page.set_console(self.console_widget)

        self.test_route_btn = QPushButton("Test SAI Routes")
        self.test_route_btn.setMaximumHeight(24)

        self.console_container = QWidget()
        _cc_layout = QtWidgets.QVBoxLayout(self.console_container)
        _cc_layout.setContentsMargins(0, 0, 0, 0)
        _cc_layout.setSpacing(2)
        _cc_layout.addWidget(self.test_route_btn)
        _cc_layout.addWidget(self.console_widget)

        # Disabled in standalone mode — require a DCC host
        for action in (self.copySceneMaya, self.copySelectMaya,
                       self.pasteSGToMaya, self.pasteSubToMaya):
            action.setEnabled(False)

    def create_layout(self):
        # Left vertical splitter: X_ITE browser on top, graph editor on bottom
        self.left_splitter = QSplitter(QtCore.Qt.Orientation.Vertical)
        self.left_splitter.addWidget(self.browser)
        self.left_splitter.addWidget(self.node_editor_widget)
        self.left_splitter.setSizes([500, 500])

        # Top horizontal splitter: left panels | scenegraph tree
        self.top_splitter = QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.top_splitter.addWidget(self.left_splitter)
        self.top_splitter.addWidget(self.tree_widget)
        self.top_splitter.setSizes([900, 300])

        # Main vertical splitter: top panels | console
        self.main_splitter = QSplitter(QtCore.Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.top_splitter)
        self.main_splitter.addWidget(self.console_container)
        self.main_splitter.setSizes([800, 160])

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_splitter)

        self.browser.setUrl(QUrl(self.x_itePath))
        
    def create_connections(self):
        self.newX3DScene.triggered.connect(self.on_new_scene)
        self.openX3DFile.triggered.connect(self.on_open_file)
        self.exportX3DAs.triggered.connect(self.on_export_as)
        self.clearGraphAction.triggered.connect(self.on_clear_graph)
        self.closeEditor.triggered.connect(self.close)
        self.node_editor_widget.scene.set_sai_runner(
            lambda js: self.browser.page().runJavaScript(js))
        self.browser.loadFinished.connect(self._on_page_load_finished)
        self.test_route_btn.clicked.connect(self._on_test_routes)


    def _on_test_routes(self):
        js = (
            "(function(){"
            " var b=document.querySelector('x3d-canvas').browser;"
            " var s=b.currentScene;"
            " var mt=s.getNamedNode('myTransform');"
            " var ot=s.getNamedNode('otherTransform');"
            " if(!mt||!ot) return 'ERROR: nodes not found';"
            " b.addRoute(mt,'translation_changed',ot,'set_translation');"
            " mt.translation=[10,0,0];"
            " return 'Route added; myTransform=[10,0,0]; otherTransform.translation='"
            "        +JSON.stringify(Array.from(ot.translation));"
            "})()"
        )
        self.browser.page().runJavaScript(
            js, lambda r: (print(f"Route test: {r}"),
                           self.console_widget.appendPlainText(f"Route test: {r}")))

    def _on_page_load_finished(self, ok):
        if ok and self._x3dObj is not None:
            self._push_file_to_xite()

    def on_item_viewer_selection(self, index):
        pass  # player control dropdown removed

    def on_new_scene(self):
        self._x3dObj = None
        self.node_editor_widget.clearGraph()
        self.setX3DScene(None)
        self.browser.page().runJavaScript(
            "(function(){var b=document.querySelector('x3d-canvas').browser;"
            "var g=b.currentScene.getNamedNode('RKInteractionEditor');"
            "b.endUpdate();g.children=[];b.beginUpdate();})()"
        )
        self.setWindowTitle("RawKee PE - X3D Interaction Editor")

    def on_open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open X3D File", "",
            "X3D Files (*.x3d *.x3dj *.x3dv);;All Files (*)")
        if not file_path:
            return
        loader = RKLoadSceneFromFile()
        x3d = loader.disk2x3d(file_path)
        if x3d is None:
            QMessageBox.warning(self, "Open Failed", f"Could not load:\n{file_path}")
            return
        self._x3dObj = x3d
        self.node_editor_widget.clearGraph()
        scene_node = getattr(x3d, 'Scene', None)
        self.setX3DScene(scene_node)
        self._push_file_to_xite()
        self.setWindowTitle(f"RawKee PE - {os.path.basename(file_path)}")

    def _push_file_to_xite(self):
        if self._x3dObj is None:
            return
        # Confirm x3d-canvas and X_ITE browser are ready
        self.browser.page().runJavaScript(
            "(function(){var c=document.querySelector('x3d-canvas');"
            "var g=c&&c.browser?c.browser.currentScene.getNamedNode('RKInteractionEditor'):null;"
            "return g?'RKIENode: found':'RKIENode: NOT FOUND (canvas='+(c?'ok':'null')+')';})()",
            lambda r: (print(f"SAI check: {r}"),
                       self.console_widget.appendPlainText(f"SAI check: {r}"))
        )
        trv = RKSceneTraversal()
        self.browser.page().runJavaScript(trv.scene2sai(self._x3dObj))

    def on_export_as(self):
        if self._x3dObj is None:
            QMessageBox.warning(self, "Export X3D", "No X3D scene to export.")
            return
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export X3D As...", "",
            "X3D XML (*.x3d);;X3D Classic VRML (*.x3dv);;X3D JSON (*.x3dj)")
        if not file_path:
            return
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".x3dv" or "x3dv" in selected_filter:
            encoding = "x3dv"
            if not file_path.lower().endswith(".x3dv"):
                file_path += ".x3dv"
        elif ext == ".x3dj" or "x3dj" in selected_filter:
            encoding = "x3dj"
            if not file_path.lower().endswith(".x3dj"):
                file_path += ".x3dj"
        else:
            encoding = "x3d"
            if not file_path.lower().endswith(".x3d"):
                file_path += ".x3d"
        try:
            trv = RKSceneTraversal()
            trv.collectProfileFromScene(self._x3dObj)
            trv.x3d2disk(self._x3dObj, file_path, encoding)
            self.setWindowTitle(f"RawKee PE - {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def on_clear_graph(self):
        self.node_editor_widget.clearGraph()

    def stopWebserver(self):
        if self.httpd:
            print("Shutting down server...")
            # .shutdown() stops the serve_forever() loop
            self.httpd.shutdown() 
            # .server_close() closes the socket properly
            self.httpd.server_close()


class RKCustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._console = None

    def set_console(self, widget):
        self._console = widget

    def _log(self, text):
        print(text)
        if self._console is not None:
            self._console.appendPlainText(text)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceId):
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel:
            level_str = "WARNING"
        elif level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            level_str = "ERROR"
        else:
            level_str = "INFO"
        self._log(f"[{level_str}] {sourceId}:{lineNumber}: {message}")


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

    def set_x3d_scene(self, x3d_scene):
        self.scene.set_x3d_scene(x3d_scene)

    def clearGraph(self):
        self.scene.clear_graph()

    def addNodeFromX3D(self, x3d_node, scene_pos):
        """Create an RKXNode in the editor canvas from a dropped rkx node object."""
        # USE nodes are just references — resolve to the actual DEF node
        use_val = getattr(x3d_node, 'USE', '')
        if use_val:
            node_type = type(x3d_node)
            for candidate in self._tree_widget._node_registry.values():
                if type(candidate) == node_type and getattr(candidate, 'DEF', '') == use_val:
                    x3d_node = candidate
                    break

        # Prevent duplicate: same DEF already in graph
        def_val = getattr(x3d_node, 'DEF', '')
        if def_val:
            for existing in self.scene.eNodes:
                if getattr(getattr(existing, 'x3d_node', None), 'DEF', '') == def_val:
                    return

        node_type = type(x3d_node).NAME()
        def_name  = getattr(x3d_node, 'DEF', '')
        use_name  = getattr(x3d_node, 'USE', '')
        title = use_name if use_name else def_name

        _NO_ROUTE_NAMES = frozenset({'DEF', 'USE', 'IS', 'class_', 'id_', 'style_'})
        inputs  = []
        outputs = []
        if hasattr(type(x3d_node), 'FIELD_DECLARATIONS'):
            for decl in type(x3d_node).FIELD_DECLARATIONS():
                field_name = decl[0]
                try:    field_type = decl[2]()
                except Exception: field_type = ''
                try:    access_str = decl[3]()
                except Exception: access_str = ''
                if field_name in _NO_ROUTE_NAMES:
                    continue
                if access_str in ('inputOnly', 'inputOutput'):
                    inputs.append((field_name, field_type))
                if access_str in ('outputOnly', 'inputOutput'):
                    outputs.append((field_name, field_type))

        # Merge spec event fields absent from FIELD_DECLARATIONS
        existing_in  = {fn for fn, _ in inputs}
        existing_out = {fn for fn, _ in outputs}
        for (fname, ftype, access) in _EXTRA_EVENT_FIELDS.get(node_type, []):
            if access == 'inputOnly' and fname not in existing_in:
                inputs.append((fname, ftype))
            elif access == 'outputOnly' and fname not in existing_out:
                outputs.append((fname, ftype))

        new_node = RKXNode(self.scene, title, inputs=inputs, outputs=outputs, x3d_node=x3d_node, node_type=node_type)
        new_node.setPos(scene_pos.x(), scene_pos.y())
        self._sync_routes_to_edges()

    def _sync_routes_to_edges(self):
        if self.scene._x3d_scene is None:
            return

        def base(name):
            if name.endswith('_changed'): return name[:-8]
            if name.startswith('set_'):   return name[4:]
            return name

        def_map = {getattr(n.x3d_node, 'DEF', ''): n
                   for n in self.scene.eNodes
                   if getattr(n, 'x3d_node', None) and getattr(n.x3d_node, 'DEF', '')}
        existing_pairs = {(id(e.start_socket), id(e.end_socket))
                          for e in self.scene.eEdges if e.start_socket and e.end_socket}
        for child in self.scene._x3d_scene.children:
            if not hasattr(child, 'fromNode'):
                continue
            from_enode = def_map.get(child.fromNode)
            to_enode   = def_map.get(child.toNode)
            if from_enode is None or to_enode is None:
                continue
            rf = base(child.fromField)
            rt = base(child.toField)
            start_sock = next((from_enode.outputs[i]
                               for i, (fn, _) in enumerate(from_enode.output_fields)
                               if base(fn) == rf and i < len(from_enode.outputs)), None)
            end_sock   = next((to_enode.inputs[i]
                               for i, (fn, _) in enumerate(to_enode.input_fields)
                               if base(fn) == rt and i < len(to_enode.inputs)), None)

            # Field not in FIELD_DECLARATIONS (pure event field) — create a socket on the fly
            if start_sock is None:
                start_sock = self._add_dynamic_socket(from_enode, child.fromField, is_output=True)
            if end_sock is None:
                end_sock = self._add_dynamic_socket(to_enode, child.toField, is_output=False)

            if start_sock is None or end_sock is None:
                continue
            pair = (id(start_sock), id(end_sock))
            if pair in existing_pairs:
                continue
            from rawkee.editor.RKXEdge import RKXEdge
            RKXEdge(self.scene, start_sock, end_sock)
            existing_pairs.add(pair)

    def _add_dynamic_socket(self, enode, field_name, is_output):
        """Create a socket for a field not present in FIELD_DECLARATIONS (pure event field)."""
        from rawkee.editor.RKXSocket import RKXSocket, LEFT_BOTTOM, RIGHT_TOP
        if is_output:
            idx = len(enode.outputs)
            enode.output_fields.append((field_name, ''))
            enode._resize_for_sockets()
            sock = RKXSocket(eNode=enode, index=idx, position=RIGHT_TOP,
                             isOutput=True, field_name=field_name)
            enode.outputs.append(sock)
        else:
            idx = len(enode.inputs)
            enode.input_fields.append((field_name, ''))
            enode._resize_for_sockets()
            sock = RKXSocket(eNode=enode, index=idx, position=LEFT_BOTTOM,
                             isOutput=False, field_name=field_name)
            enode.inputs.append(sock)
        return sock

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
