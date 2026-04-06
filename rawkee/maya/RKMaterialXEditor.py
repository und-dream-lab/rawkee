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
    from PySide2           import QtUiTools
    from PySide2.QtGui     import QRegularExpressionValidator
    from PySide2.QtCore    import QRegularExpression
    
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
    from PySide6           import QtUiTools
    from PySide6.QtGui     import QRegularExpressionValidator
    from PySide6.QtCore    import QRegularExpression
    
    from shiboken6         import wrapInstance
    from shiboken6         import getCppPointer
    
import sys
import os
import maya.OpenMayaUI as omui
import maya.cmds       as cmds

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

class RKMaterialXEditor(MayaQWidgetDockableMixin, QWidget):
    
    OBJECT_NAME = "RKMaterialXEditor"
    
    @classmethod
    def materialx_editor_control_name(cls):
        return "{0}WorkspaceControl".format(cls.OBJECT_NAME)
        
    @classmethod
    def workspace_ui_script(cls):
        return "from rawkee.maya.RKMaterialXEditor import RKMaterialXEditor\nrkMXEWidget = RKMaterialXEditor()"
        
    @classmethod
    def workplace_close_command(cls):
        return "self.cleanUpOnEditorClose()"

    
    def __init__(self):
        super().__init__()

        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("MaterialXSurfaceShader Export Type Editor")
        self.setMinimumSize(400,300)
        self.setMaximumSize(400,300)

        self.add_to_materialx_editor_workspace_control()

        self.uiPaths = os.path.abspath(__file__)
        self.uiPaths = os.path.dirname(self.uiPaths)
        self.uiPaths += "/auxilary/RKMaterialXPanel.ui"

        loader = QtUiTools.QUiLoader()
        # loader.registerCustomWidget(RKDagPoseComboBox)
        mtlXeGUIFile = QtCore.QFile(self.uiPaths)
        mtlXeGUIFile.open(QtCore.QFile.ReadOnly)
        self.mtlXePanel = loader.load(mtlXeGUIFile, self)

        ######################################################
        # Top Level Layout                                   #
        main_layout = QtWidgets.QHBoxLayout(self)            #
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.mtlXePanel)
        
        self.setTreeContextMenu()
        
        self.updateTreeDisplay()
        

    def cleanUpOnEditorClose(self):
        print("Cleaned")


    def add_to_materialx_editor_workspace_control(self):
        materialx_editor_workspace_control = omui.MQtUtil.findControl(self.materialx_editor_control_name())
        if materialx_editor_workspace_control:
            materialx_editor_workspace_control_ptr = int(materialx_editor_workspace_control)
            materialx_editor_widget_ptr = int(getCppPointer(self)[0])
            
            omui.MQtUtil.addWidgetToMayaLayout(materialx_editor_widget_ptr, materialx_editor_workspace_control_ptr)


    def showContextMenu(self, pos):
        shaderTree  = self.findChild(QtWidgets.QTreeWidget, 'shaderTree')

        self.pMenu.addAction(self.shaderAction)
        self.pMenu.addSeparator()
        self.pMenu.addSeparator()
        self.pMenu.addAction(self.materialAction)
        
        self.pMenu.exec(shaderTree.viewport().mapToGlobal(pos))


    def setTreeContextMenu(self):
        shaderTree  = self.findChild(QtWidgets.QTreeWidget, 'shaderTree')

        self.pMenu = QtWidgets.QMenu(shaderTree)

        shaderTree.setContextMenuPolicy(Qt.CustomContextMenu)
        shaderTree.customContextMenuRequested.connect(self.showContextMenu)
        
        self.shaderAction   = QAction("Set Selected as shader export type"  )
        self.materialAction = QAction("Set Selected as material export type")
        
        self.shaderAction.triggered.connect(  self.setMayaShaderAsShaders )
        self.materialAction.triggered.connect(self.setMayaShaderAsMaterial)


    def setMayaShaderAsShaders(self):
        shaderTree  = self.findChild(QtWidgets.QTreeWidget, 'shaderTree')
        
        shaderItems = shaderTree.selectedItems()
        for item in shaderItems:
            shaderName = item.text(0).split(" - ")[0]
            try:
                cmds.setAttr(shaderName + ".asX3DShader", True)
            except:
                pass
        
        self.updateTreeDisplay()


    def setMayaShaderAsMaterial(self):
        shaderTree  = self.findChild(QtWidgets.QTreeWidget, 'shaderTree')
        
        shaderItems = shaderTree.selectedItems()
        for item in shaderItems:
            shaderName = item.text(0).split(" - ")[0]
            try:
                cmds.setAttr(shaderName + ".asX3DShader", False)
            except:
                pass
        
        self.updateTreeDisplay()


    def updateTreeDisplay(self):
        shaderTree = self.findChild(QtWidgets.QTreeWidget, 'shaderTree')
        shaderTree.clear()
        
        shaderNodes = cmds.ls(type='MaterialXSurfaceShader')
        for shader in shaderNodes:
            if cmds.objExists(shader + ".asX3DShader") == False:
                cmds.addAttr(shader, longName='asX3DShader', attributeType='bool', defaultValue=False)
            
            isShader = cmds.getAttr(shader + ".asX3DShader")
            
            itemLabel = shader + " - "
            if isShader == True:
                itemLabel += "PackagedShader/ComposedShader (both)"
            else:
                itemLabel += "PhysicalMaterial or Material (as appropriate)"
                
            item = QTreeWidgetItem(shaderTree, [itemLabel])