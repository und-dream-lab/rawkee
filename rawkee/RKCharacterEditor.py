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
        
        self.hanimSkeletonPanel = None
        self.advancedSkeletonPanel = None
        self.artPanel = None
        self.animationPanel = None 
        self.testPanel = None
        
        self.uiPaths = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
        self.uiPaths += "/auxilary/"
        
        self.hanimPath     = self.uiPaths + "RKCharacterEditorHAnimSkeletonPanel.ui"
        self.advancedPath  = self.uiPaths + "RKCharacterEditorAdvancedSkeletonPanel.ui"
        self.artPath       = self.uiPaths + "RKCharacterEditor_aRT_Panel.ui"
        self.animationPath = self.uiPaths + "RKCharacterEditorAnimationPanel.ui"
        self.testPath      = self.uiPaths + "RKQSSTestPanel.ui"
        
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
        print("cleanup")
        #pass
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
        # Creating a Tabbed Panel Widget to hold it all
        self.tab_widget = QTabWidget()


    def create_layout(self):
        loader = QtUiTools.QUiLoader()
        #self.testfile = QtCore.QFile(testPath)
        #self.testfile.open(QtCore.QFile.ReadOnly)


        
        # Character Animation Tools
        if not self.animationPanel:
            animGUIFile = QtCore.QFile(self.animationPath)
            animGUIFile.open(QtCore.QFile.ReadOnly)
            self.animationPanel = loader.load(animGUIFile)
        self.tab_widget.addTab(self.animationPanel, "Character Animation Setup for X3D Export")
        
        # Create Standard HAnim Skeleton
        if not self.hanimSkeletonPanel:
            hanimGUIFile = QtCore.QFile(self.hanimPath)
            hanimGUIFile.open(QtCore.QFile.ReadOnly)
            self.hanimSkeletonPanel = loader.load(hanimGUIFile)
        self.tab_widget.addTab(self.hanimSkeletonPanel, "X3D/HAnim Skeleton Creator")

        # antCGI Rigging Toolkit
        try:
            from aRT import aRTUI
            print("aRT was found")
            #Old
            #self.tab_widget.addTab(self.artPanel, "aRT Rigging and Animation Toolkit")
            
            #New
            if not self.artPanel:
                artGUIFile = QtCore.QFile(self.artPath)
                #artGUIFile.open(QtCore.QFile.ReadOnly)
                #self.artPanel = loader.load(artGUIFile)
            #self.tab_widget.addTab(self.artPanel, "aRT Rigging and Animation Toolkit")
            
        except:
            print("aRT not found")
            
        # Advanced Skeleton Functions
        asExists = mel.eval("exists asCreateGameEngineRootMotion")
        if asExists == True:
            if not self.advancedSkeletonPanel:
                advGUIFile = QtCore.QFile(self.advancedPath)
                advGUIFile.open(QtCore.QFile.ReadOnly)
                self.advancedSkeletonPanel = loader.load(advGUIFile)
            self.tab_widget.addTab(self.advancedSkeletonPanel, "Advanced Skeleton Functions")
        
        # QSS Testing Tab
        #if not self.testPanel:
        #    testFile = QtCore.QFile(self.testPath)
        #    testFile.open(QtCore.QFile.ReadOnly)
        #    self.testPanel = loader.load(testFile)
        #self.tab_widget.addTab(self.testPanel, "QSS Test Panel")
        
        ######################################################
        # Top Level Layout                                   #
        main_layout = QtWidgets.QHBoxLayout(self)            #
        main_layout.addWidget(self.tab_widget)


    def create_connections(self):
        
        estIPose  = self.findChild(QtWidgets.QPushButton, 'estIPose')
        estAPose  = self.findChild(QtWidgets.QPushButton, 'estAPose')
        estTPose  = self.findChild(QtWidgets.QPushButton, 'estTPose')

        saveIPose  = self.findChild(QtWidgets.QPushButton, 'saveIPose')
        saveAPose  = self.findChild(QtWidgets.QPushButton, 'saveAPose')
        saveTPose  = self.findChild(QtWidgets.QPushButton, 'saveTPose')

        gtIPose   = self.findChild(QtWidgets.QPushButton, 'gtIPose'   )
        gtTPose   = self.findChild(QtWidgets.QPushButton, 'gtTPose'   )
        gtAPose   = self.findChild(QtWidgets.QPushButton, 'gtAPose'   )
        asPose    = self.findChild(QtWidgets.QPushButton, 'asPose'    )
        haDefPose = self.findChild(QtWidgets.QPushButton, 'haDefPose' )

        genButton = self.findChild(QtWidgets.QPushButton, 'genButton'         )
        ipoButton = self.findChild(QtWidgets.QPushButton, 'iposeButton'       )
        cpbButton = self.findChild(QtWidgets.QPushButton, 'defPoseButton'     )
        trwButton = self.findChild(QtWidgets.QPushButton, 'transferSkinButton')

        estIPose.clicked.connect(cmds.rkEstimateIPoseForASGS)
        estAPose.clicked.connect(cmds.rkEstimateAPoseForASGS)
        estTPose.clicked.connect(cmds.rkEstimateTPoseForASGS)
        
        saveIPose.clicked.connect(cmds.rkSaveIPoseForASGS)
        saveAPose.clicked.connect(cmds.rkSaveAPoseForASGS)
        saveTPose.clicked.connect(cmds.rkSaveTPoseForASGS)
        
        gtIPose.clicked.connect(cmds.rkLoadIPoseForASGS)
        gtAPose.clicked.connect(cmds.rkLoadAPoseForASGS)
        gtTPose.clicked.connect(cmds.rkLoadTPoseForASGS)
        
        asPose.clicked.connect(cmds.rkSetASPoseForASGS)
        haDefPose.clicked.connect(cmds.rkLoadDefPoseForHAnim)
        
        genButton.clicked.connect(cmds.rkAdvancedSkeleton)
        ipoButton.clicked.connect(cmds.rkLoadIPoseForASGS)
        cpbButton.clicked.connect(cmds.rkDefPoseForASGS  )
        trwButton.clicked.connect(cmds.rkTransferSkinASGS)
        

    def buildHAnimAnimationTree(self):
        pass

        
    def putAnimationOptions(self, node):
        pass


    def getAnimationOptions(self, node):
        pass

            
    