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
import maya.mel  as mel

#Python API 2.0 needed to register command with API 2.0 plugin
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omAnim

#To get local file path for html file
from rawkee import RKWeb3D

#To geth other items from 'rawkee'
### from rawkee.RKXScene   import RKXScene
### from rawkee.RKXNodes   import RKXNode #notice the missing 's' - RKXNode is a test class
### from rawkee.RKXSocket  import RKXSocket
### from rawkee.RKGraphics import RKGraphicsView


from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

global rkWeb3D

class RKCharacterEditor(MayaQWidgetDockableMixin, QWidget):
    
    OBJECT_NAME = "RKCharacterEditor"
    
    @classmethod
    def character_editor_control_name(cls):
        return "{0}WorkspaceControl".format(cls.OBJECT_NAME)
        
    @classmethod
    def workspace_ui_script(cls):
        return "from rawkee.RKCharacterEditor import RKCharacterEditor\nrkSEWidget = RKCharacterEditor()"
        
    @classmethod
    def workplace_close_command(cls):
        return "self.cleanUpOnEditorClose()"

    
    def __init__(self):
        super().__init__()
        
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("RawKee PE - X3D Character and Animation Editor")
        self.setMinimumSize(800,400)
        
        self.add_to_character_editor_workspace_control()
        
        self.create_actions()

        self.create_widgets()
        
        self.create_layout()
        
        self.create_connections()

##################################
#        Probably not needed
##################################        
#        self.rkWeb3D = None

#    def setRKWeb3D(self, rkWeb3D):
        # Maybe this should be moved to the constructor.
        # This is here so that the RKCharacterEditor panel
        # can send and receive x3d.X3D objects with the 
        # MainMayaWindow RawKee GUI/Menu system.
#        self.rkWeb3D = rkWeb3D

    def cleanUpOnEditorClose(self):
        pass
        # Release the RKWeb3D object, otherwise it will not
        # later be deleteable when the plugin unloads. If
        # the object is not deletable, then the __del__ 
        # method for that object will never be called during
        # the plugin unload, and thus the 'RawKee (X3D)' 
        # menu won't be removed from the MayaMainWindow
        # menubar.
#        self.rkWeb3D = None

    def add_to_character_editor_workspace_control(self):
        character_editor_workspace_control = omui.MQtUtil.findControl(self.character_editor_control_name())
        if character_editor_workspace_control:
            character_editor_workspace_control_ptr = int(character_editor_workspace_control)
            character_editor_widget_ptr = int(getCppPointer(self)[0])
            
            omui.MQtUtil.addWidgetToMayaLayout(character_editor_widget_ptr, character_editor_workspace_control_ptr)


    def create_actions(self):
        pass
        

    def create_widgets(self):
        ##############################################
        # 
        self.gsfLabel = QLabel("Advanced Skeleton Configuration Functions")
        self.gsfLabel.setMinimumHeight(30)
        self.gsfLabel.setMaximumHeight(30)

        ##############################################
        # 
        self.cgsLabel = QLabel("     X3D/HAnim Compatible GameSkeleton")
        self.cgsLabel.setMinimumHeight(30)
        self.cgsLabel.setMaximumHeight(30)
        self.cgsLabel.setMinimumWidth(250)
        self.cgsLabel.setMinimumWidth(250)
        
        self.cgsButton = QtWidgets.QPushButton("Create")
        self.cgsButton.setMinimumHeight(30)
        self.cgsButton.setMaximumHeight(30)
        self.cgsButton.setMinimumWidth(40)
        self.cgsButton.setMinimumWidth(40)

        ##############################################
        # 
        self.agcLabel = QLabel("     Align GameSkeleton Configuration")
        self.agcLabel.setMinimumHeight(30)
        self.agcLabel.setMaximumHeight(30)
        self.agcLabel.setMinimumWidth(250)
        self.agcLabel.setMinimumWidth(250)
        
        self.agcButton = QtWidgets.QPushButton("Set I-Pose")
        self.agcButton.setMinimumHeight(30)
        self.agcButton.setMaximumHeight(30)
        self.agcButton.setMinimumWidth(40)
        self.agcButton.setMinimumWidth(40)

        ##############################################
        # 
        self.asmLabel = QLabel("     Assign Selected Meshes to GameSkeleton")
        self.asmLabel.setMinimumHeight(30)
        self.asmLabel.setMaximumHeight(30)
        self.asmLabel.setMinimumWidth(250)
        self.asmLabel.setMinimumWidth(250)
        
        self.asmButton = QtWidgets.QPushButton("Copy and Bind")
        self.asmButton.setMinimumHeight(30)
        self.asmButton.setMaximumHeight(30)
        self.asmButton.setMinimumWidth(40)
        self.asmButton.setMinimumWidth(40)

        ##############################################
        # 
        self.aswLabel = QLabel("     Assign SkinWeights to GameSkeleton")
        self.aswLabel.setMinimumHeight(30)
        self.aswLabel.setMaximumHeight(30)
        self.aswLabel.setMinimumWidth(250)
        self.aswLabel.setMinimumWidth(250)
        
        self.aswButton = QtWidgets.QPushButton("Transfer Weights")
        self.aswButton.setMinimumHeight(30)
        self.aswButton.setMaximumHeight(30)
        self.aswButton.setMinimumWidth(40)
        self.aswButton.setMinimumWidth(40)

        
        
        ##############################################
        # 
        self.humLabel = QLabel("     Humanoid Node DEF:")
        self.humLabel.setMinimumHeight(40)
        self.humLabel.setMaximumHeight(40)
        self.humLabel.setMinimumWidth(250)
        self.humLabel.setMinimumWidth(250)
        
        self.humLEdit = QtWidgets.QLineEdit("HAnimHumanoid_01")
        self.humLEdit.setMinimumHeight(40)
        self.humLEdit.setMaximumHeight(40)
        self.humLEdit.setMinimumWidth(100)
        self.humLEdit.setMinimumWidth(100)

        ##############################################
        # 
        self.x3dLabel = QLabel("     X3D/HAnim Fields:")
        self.x3dLabel.setMinimumHeight(30)
        self.x3dLabel.setMaximumHeight(30)
        self.x3dLabel.setMinimumWidth(250)
        self.x3dLabel.setMinimumWidth(250)
        
        ##############################################
        # 
        self.scfLabel = QLabel("          SkeletonConfiguration:")
        self.scfLabel.setMinimumHeight(40)
        self.scfLabel.setMaximumHeight(40)
        self.scfLabel.setMinimumWidth(250)
        self.scfLabel.setMinimumWidth(250)
        
        self.scfLEdit = QtWidgets.QLineEdit("BASIC")
        self.scfLEdit.setEnabled(False)
        self.scfLEdit.setMinimumHeight(40)
        self.scfLEdit.setMaximumHeight(40)
        self.scfLEdit.setMinimumWidth(40)
        self.scfLEdit.setMinimumWidth(40)

        ##############################################
        # 
        self.loaLabel = QLabel("          Level of Articulation:")
        self.loaLabel.setMinimumHeight(30)
        self.loaLabel.setMaximumHeight(30)
        self.loaLabel.setMinimumWidth(250)
        self.loaLabel.setMinimumWidth(250)
        
        self.loaQCBox = QtWidgets.QComboBox()
        self.loaQCBox.addItems(["LOA 0", "LOA 1", "LOA 2", "LOA 3", "LOA 4"])
        self.loaQCBox.setFixedWidth(80)
        self.loaQCBox.setMinimumHeight(30)
        self.loaQCBox.setMaximumHeight(30)
        self.loaQCBox.setMinimumWidth(130)
        self.loaQCBox.setMinimumWidth(130)

        ##############################################
        # 
        self.cacLabel = QLabel("          ")
        self.cacLabel.setMinimumHeight(30)
        self.cacLabel.setMaximumHeight(30)

        self.cacButton = QtWidgets.QPushButton("Create HAnim Compliant Skeleton")
        self.cacButton.setMinimumHeight(30)
        self.cacButton.setMaximumHeight(30)
        self.cacButton.setMinimumWidth(200)
        self.cacButton.setMinimumWidth(200)

        ##############################################
        # HAnim Skeleton GUI Panel
        self.hanimPanel = QGroupBox()
        
        ##############################################
        # Advanced Skeleton GUI Panel
        self.advPanel   = QGroupBox()
        
        ##############################################
        # Advanced Skeleton GUI Panel
        self.antPanel   = QGroupBox()
        
        ##############################################
        # Skeleton Animation GUI Panel
        self.animationPanel   = QGroupBox()
        self.splitter = QSplitter()
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setLineWidth(4)
        self.splitter.addWidget(QtWidgets.QLabel("Side A"))
        self.splitter.addWidget(QtWidgets.QLabel("Side B"))

        
        ##############################################
        # Creating a Tabbed Panel Widget to hold it all
        self.tab_widget = QTabWidget()


    def create_layout(self):
        self.advancedLayout = QtWidgets.QVBoxLayout()
        self.createGSRow    = QtWidgets.QHBoxLayout()
        self.setIPoseRow    = QtWidgets.QHBoxLayout()
        self.bindMeshRow    = QtWidgets.QHBoxLayout()
        self.tWeightsRow    = QtWidgets.QHBoxLayout()
        
        self.animPanelLt    = QtWidgets.QHBoxLayout()
        self.animPanelLt.setContentsMargins(0,0,0,0)
        self.animPanelLt.setSpacing(0)
        self.animPanelLt.addWidget(self.splitter)

        self.createGSRow.setContentsMargins(10,10,10,20)
        self.createGSRow.setSpacing(10)
        self.createGSRow.addWidget(self.cgsLabel)
        self.createGSRow.addWidget(self.cgsButton)
        self.createGSRow.addStretch()

        self.setIPoseRow.setContentsMargins(10,10,10,20)
        self.setIPoseRow.setSpacing(10)
        self.setIPoseRow.addWidget(self.agcLabel)
        self.setIPoseRow.addWidget(self.agcButton)
        self.setIPoseRow.addStretch()

        self.bindMeshRow.setContentsMargins(10,10,10,20)
        self.bindMeshRow.setSpacing(10)
        self.bindMeshRow.addWidget(self.asmLabel)
        self.bindMeshRow.addWidget(self.asmButton)
        self.bindMeshRow.addStretch()

        self.tWeightsRow.setContentsMargins(10,10,10,20)
        self.tWeightsRow.setSpacing(10)
        self.tWeightsRow.addWidget(self.aswLabel)
        self.tWeightsRow.addWidget(self.aswButton)
        self.tWeightsRow.addStretch()

        self.advancedLayout.setContentsMargins(10,10,10,10)
        self.advancedLayout.setSpacing(0)
        ############### self.advancedLayout.addWidget(self.gsfLabel)
        self.advancedLayout.addLayout(self.createGSRow)
        self.advancedLayout.addLayout(self.setIPoseRow)
        self.advancedLayout.addLayout(self.bindMeshRow)
        self.advancedLayout.addLayout(self.tWeightsRow)
        self.advancedLayout.addStretch()
        
        self.advPanel.setLayout(self.advancedLayout)


        self.hanimLayout    = QtWidgets.QVBoxLayout()
        self.humanoidRow    = QtWidgets.QHBoxLayout()
        self.x3dFieldRow    = QtWidgets.QHBoxLayout()
        self.skelConfRow    = QtWidgets.QHBoxLayout()
        self.levelOfARow    = QtWidgets.QHBoxLayout()
        self.createSKRow    = QtWidgets.QHBoxLayout()
        
        self.humanoidRow.setContentsMargins(10,10,10,10)
        self.humanoidRow.setSpacing(10)
        self.humanoidRow.addWidget(self.humLabel)
        self.humanoidRow.addWidget(self.humLEdit)
        self.humanoidRow.addStretch()

        self.x3dFieldRow.setContentsMargins(10,10,10,10)
        self.x3dFieldRow.setSpacing(10)
        self.x3dFieldRow.addWidget(self.x3dLabel)
        self.x3dFieldRow.addStretch()

        self.skelConfRow.setContentsMargins(10,10,10,10)
        self.skelConfRow.setSpacing(10)
        self.skelConfRow.addWidget(self.scfLabel)
        self.skelConfRow.addWidget(self.scfLEdit)
        self.skelConfRow.addStretch()

        self.levelOfARow.setContentsMargins(10,10,20,20)
        self.levelOfARow.setSpacing(10)
        self.levelOfARow.addWidget(self.loaLabel)
        self.levelOfARow.addWidget(self.loaQCBox)
        self.levelOfARow.addStretch()

        self.createSKRow.setContentsMargins(10,10,10,10)
        self.createSKRow.setSpacing(10)
        self.createSKRow.addWidget(self.cacLabel)
        self.createSKRow.addWidget(self.cacButton)
        self.createSKRow.addStretch()

        self.hanimLayout.setContentsMargins(10,10,10,10)
        self.hanimLayout.setSpacing(10)
        self.hanimLayout.addLayout(self.humanoidRow)
        self.hanimLayout.addLayout(self.x3dFieldRow)
        self.hanimLayout.addLayout(self.skelConfRow)
        self.hanimLayout.addLayout(self.levelOfARow)
        self.hanimLayout.addLayout(self.createSKRow)
        self.hanimLayout.addStretch()

        self.hanimPanel.setLayout(self.hanimLayout)
        
        # HAnim Skeleton GUI
        self.tab_widget.addTab(self.hanimPanel,     "X3D/HAnim Skeleton Creator")
        
        # Advanced Skeleton Functions
        asExists = mel.eval("exists asCreateGameEngineRootMotion")
        if asExists == True:
            self.tab_widget.addTab(self.advPanel,   "Advanced Skeleton Functions")
            
        # antCGI Rigging Toolkit
        try:
            from aRT import aRTUI
            print("aRT was found")
            self.tab_widget.addTab(self.antPanel, "antCGi Rigging Toolkit")
        except:
            print("aRT not found")
        
        self.animationPanel.setLayout(self.animPanelLt)
        
        # Character Animation Tools
        self.tab_widget.addTab(self.animationPanel, "Character Animation Setup for X3D Export")

        ######################################################
        # Top Level Layout                                   #
        main_layout = QtWidgets.QHBoxLayout(self)            #
        main_layout.addWidget(self.tab_widget)


    def create_connections(self):
        pass
        

    def buildHAnimAnimationTree(self):
        pass

        
    def putAnimationOptions(self, node):
        pass


    def getAnimationOptions(self, node):
        pass

