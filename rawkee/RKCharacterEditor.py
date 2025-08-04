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
from   maya.api.OpenMaya import MFn as rkfn
import maya.api.OpenMayaAnim as omAnim

#Sticker App for applying Outliner icons
import rawkee.nodes.sticker    as stk

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
        
        self.haNameText = "Eric"
        self.haLOAValue = 0
        
        self.hanimCS  = None
        self.haNameEd = None
        self.haLOA    = None
        
        self.estIPose  = None
        self.estAPose  = None
        self.estTPose  = None

        self.saveIPose = None
        self.saveAPose = None
        self.saveTPose = None

        self.gtIPose   = None
        self.gtTPose   = None
        self.gtAPose   = None
        self.asPose    = None
        self.haDefPose = None

        self.genButton = None
        self.ipoButton = None
        self.cpbButton = None
        self.trwButton = None
        
        self.loadHuman = None
        self.hmnSelect = None
        self.apTree    = None
        self.cgTree    = None
        self.newTName  = None
        self.addRKAP   = None
        self.delRKAP   = None
        self.newNType  = None
        
        self.pMenu     = None
        self.trAction  = None
        self.roAction  = None
        self.scAction  = None

        self.allAction = None
        self.troAction = None
        
        self.rmtrAction = None
        self.rmroAction = None

        self.rmscAction = None

        self.rmAllAction = None
        self.rmrtoAction = None
        
        self.allRotsAct  = None
        self.rmAllRotsAct = None
        
        self.sAnimPack   = None
        
        self.CBIDs       = None
        
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
        cgTree        = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        
        self.trAction = QAction("Capture Translate Animation", cgTree)
        self.roAction = QAction("Capture Rotate Animation", cgTree)
        self.scAction = QAction("Capture Scale Animation", cgTree)

        self.allAction = QAction("Capture T/R/S Animation", cgTree)
        self.troAction = QAction("Capture T/R Animation", cgTree)
        
        self.rmtrAction = QAction("Release Translate Animation", cgTree)
        self.rmroAction = QAction("Release Rotate Animation", cgTree)

        self.rmscAction = QAction("Release Scale Animation", cgTree)

        self.rmAllAction = QAction("Release T/R/S Animation", cgTree)
        self.rmrtoAction = QAction("Release T/R Animation", cgTree)
        
        self.sAnimPack = QAction("Select an Animation Package", cgTree)
        
        self.allRotsAct = QAction("Capture Rotate Animation - All Joints")

        self.rmAllRotsAct = QAction("Release Rotate Animation - All Joints")
        
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
        
        # Character Animation Setup Panel - Tab
        self.loadHuman = self.findChild(QtWidgets.QPushButton, 'loadHumanoidButton')
        self.hmnSelect = self.findChild(QtWidgets.QLineEdit,   'humanoidSelected'  )
        self.newTName  = self.findChild(QtWidgets.QLineEdit,   'newTimerName'      )
        self.apTree    = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes')
        self.apTree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cgTree  = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        self.cgTree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.apTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.addRKAP   = self.findChild(QtWidgets.QPushButton, 'addRKAnimPack')
        self.delRKAP   = self.findChild(QtWidgets.QPushButton, 'delRKAnimPack')
        self.newNType  = self.findChild(QtWidgets.QComboBox,   'newNodeType'  )
        
        self.pMenu = QtWidgets.QMenu(self.cgTree)

        
        self.populateAnimationPackages()

        # HAnim Compliant Skeleton - Tab
        self.hanimCS  = self.findChild(QtWidgets.QPushButton, 'createHAnimSkeleton')
        self.haNameEd = self.findChild(QtWidgets.QLineEdit,   'haNameEdit'         )
        self.haLOA    = self.findChild(QtWidgets.QComboBox,   'loaComboBox'        )
        
        # Advanced Skeleton - Tab
        self.estIPose  = self.findChild(QtWidgets.QPushButton, 'estIPose')
        self.estAPose  = self.findChild(QtWidgets.QPushButton, 'estAPose')
        self.estTPose  = self.findChild(QtWidgets.QPushButton, 'estTPose')

        self.saveIPose  = self.findChild(QtWidgets.QPushButton, 'saveIPose')
        self.saveAPose  = self.findChild(QtWidgets.QPushButton, 'saveAPose')
        self.saveTPose  = self.findChild(QtWidgets.QPushButton, 'saveTPose')

        self.gtIPose   = self.findChild(QtWidgets.QPushButton, 'gtIPose'   )
        self.gtTPose   = self.findChild(QtWidgets.QPushButton, 'gtTPose'   )
        self.gtAPose   = self.findChild(QtWidgets.QPushButton, 'gtAPose'   )
        self.asPose    = self.findChild(QtWidgets.QPushButton, 'asPose'    )
        self.haDefPose = self.findChild(QtWidgets.QPushButton, 'haDefPose' )

        self.genButton = self.findChild(QtWidgets.QPushButton, 'genButton'         )
        self.ipoButton = self.findChild(QtWidgets.QPushButton, 'iposeButton'       )
        self.cpbButton = self.findChild(QtWidgets.QPushButton, 'defPoseButton'     )
        self.trwButton = self.findChild(QtWidgets.QPushButton, 'transferSkinButton')


    def create_connections(self):
        # Context menu
        cgTree        = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        cgTree.setContextMenuPolicy(Qt.CustomContextMenu)
        cgTree.customContextMenuRequested.connect(self.showContextMenu)
        self.allRotsAct.triggered.connect(self.captureRotateForHAnimMotion)
        self.rmAllRotsAct.triggered.connect(self.releaseRotateForHAnimMotion)
        
        self.trAction.triggered.connect(lambda: self.captureTranslateGeneral(True))
        self.roAction.triggered.connect(lambda: self.captureRotateGeneral(True))
        self.scAction.triggered.connect(lambda: self.captureScaleGeneral(True))
        self.troAction.triggered.connect(lambda: self.captureTRGeneral(True))
        self.allAction.triggered.connect(lambda: self.captureAllGeneral(True))
        
        self.rmtrAction.triggered.connect(lambda: self.releaseTranslateGeneral(True))
        self.rmroAction.triggered.connect(lambda: self.releaseRotateGeneral(True))
        self.rmscAction.triggered.connect(lambda: self.releaseScaleGeneral(True))
        self.rmrtoAction.triggered.connect(lambda: self.releaseTRGeneral(True))
        self.rmAllAction.triggered.connect(lambda: self.releaseAllGeneral(True))
        
        aPackTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes')
        aPackTree.itemSelectionChanged.connect(self.populateCharacterGraph)


        # Character Animation Setup Panel - Tab
        self.loadHuman.clicked.connect(self.loadSelectedHumanoid)
        self.addRKAP.clicked.connect(self.addAnimationTimingPackage)
        self.delRKAP.clicked.connect(self.delAnimationTimingPackage)
#        self.newNType  = self.findChild(QtWidgets.QComboBox,   'newNodetype'  )

        # HAnim Compliant Skeleton - Tab
        self.hanimCS.clicked.connect(self.createHAnimCompliantSkeleton)
        self.haLOA.currentIndexChanged.connect(self.setHaLOAValue)
        self.haNameEd.textEdited.connect(self.setHaNameText)
        
        # Advanced Skeleton - Tab
        self.estIPose.clicked.connect(cmds.rkEstimateIPoseForASGS)
        self.estAPose.clicked.connect(cmds.rkEstimateAPoseForASGS)
        self.estTPose.clicked.connect(cmds.rkEstimateTPoseForASGS)
        
        self.saveIPose.clicked.connect(cmds.rkSaveIPoseForASGS)
        self.saveAPose.clicked.connect(cmds.rkSaveAPoseForASGS)
        self.saveTPose.clicked.connect(cmds.rkSaveTPoseForASGS)
        
        self.gtIPose.clicked.connect(cmds.rkLoadIPoseForASGS)
        self.gtAPose.clicked.connect(cmds.rkLoadAPoseForASGS)
        self.gtTPose.clicked.connect(cmds.rkLoadTPoseForASGS)
        
        self.asPose.clicked.connect(cmds.rkSetASPoseForASGS)
        self.haDefPose.clicked.connect(cmds.rkLoadDefPoseForHAnim)
        
        self.genButton.clicked.connect(cmds.rkAdvancedSkeleton)
        self.ipoButton.clicked.connect(cmds.rkLoadIPoseForASGS)
        self.cpbButton.clicked.connect(cmds.rkDefPoseForASGS  )
        self.trwButton.clicked.connect(cmds.rkTransferSkinASGS)
        

    # Context Menu Stuff
    #################################################
    #
    #################################################
    def showContextMenu(self, pos):
        self.cgTree = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        self.apTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes'     )
        
        selList = []
        selList = self.apTree.selectedItems()
        
        self.pMenu.clear()
        
        if len(selList) > 0:
            nType = selList[0].text(0)
            print("Menu Option - " + nType)
            if nType == "HAnimMotion":
                self.pMenu.addAction(self.allRotsAct)
                self.pMenu.addSeparator()
                self.pMenu.addAction(self.rmAllRotsAct)
            else:
                #self.pMenu.addSection("Capture Animation")
                self.pMenu.addAction(self.trAction)
                self.pMenu.addAction(self.roAction)
                self.pMenu.addSeparator()
                self.pMenu.addAction(self.scAction)
                self.pMenu.addSeparator()
                self.pMenu.addAction(self.allAction)
                self.pMenu.addAction(self.troAction)
                self.pMenu.addSeparator()
                #self.pMenu.addSection("Remove Animation")
                self.pMenu.addAction(self.rmtrAction)
                self.pMenu.addAction(self.rmroAction)
                self.pMenu.addSeparator()
                self.pMenu.addAction(self.rmscAction)
                self.pMenu.addSeparator()
                self.pMenu.addAction(self.rmAllAction)
                self.pMenu.addAction(self.rmrtoAction)
        else:
            self.pMenu.addAction(self.sAnimPack)
            
        
        self.pMenu.exec(self.cgTree.viewport().mapToGlobal(pos))


    # Character Animation Setup Panel - Tab
    ##############################################################################################
    # Delete the selected timing node - aka rkAnimPack (TimeSensor, HAnimMotion, AudioClip, 
    # or MovieTexture)
    ##############################################################################################
    def delAnimationTimingPackage(self):
        apTree    = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes')
        selItems  = apTree.selectedItems()
        
        tNode = ""
        if len(selItems) > 0:
            for item in selItems:
                tNode = item.text(1)
                
            if cmds.objExists(tNode):
                selList = om.MSelectionList()
                selList.add(tNode)
                apNode = selList.getDependNode(0)
                
                eNames = []
                mIter = om.MItDependencyGraph(apNode, rkfn.kExpression, om.MItDependencyGraph.kDownstream, om.MItDependencyGraph.kBreadthFirst, om.MItDependencyGraph.kNodeLevel)
                while not mIter.isDone():
                    eNode = om.MFnDependencyNode(mIter.currentNode())
                    eNames.append(eNode.name())
                    
                    mIter.next()
                    
                for eName in eNames:
                    if cmds.objExists(eName):
                        cmds.delete(eName)
                
                cmds.delete(tNode)
                
        self.populateAnimationPackages()

        
    ##############################################################################################
    # Add a new timing node - aka rkAnimPack (TimeSensor, HAnimMotion, AudioClip, or MovieTexture)
    ##############################################################################################
    def addAnimationTimingPackage(self):
        human     = self.findChild(QtWidgets.QLineEdit, 'humanoidSelected')
        newNType  = self.findChild(QtWidgets.QComboBox, 'newNodeType'     )
        newTName  = self.findChild(QtWidgets.QLineEdit, 'newTimerName'    )
        
        hName = human.text()
        tName = newTName.text()
        hBool = cmds.objExists(hName)
        if hBool == True and tName != "":
            atSet = newNType.currentIndex() + 1
            aName = cmds.createNode("rkAnimPack", n=tName, p=hName)
            
            self.updateAnimPackAttributes( aName, "mimickedType", atSet)
            
            self.populateAnimationPackages()
            
    ##########################################################################
    ## Functions reproducng the functions found in AErkAnimPackTemplate.mel ##
    ##########################################################################
    # List of functions:                                                     #
    #       rkAnimPack_AddAudioClipAttrs                                     #
    #       rkAnimPack_AddHAnimMotionAttrs                                   #
    #       rkAnimPack_AddMovieTextureAttrs                                  #
    #       rkAnimPack_AddTimeSensorAttrs                                    #
    #                                                                        #
    #       rkAnimPack_ClearConnectedFile                                    #
    #                                                                        #
    #       rkAnimPack_SubAudioClipAttrs                                     #
    #       rkAnimPack_SubHAnimMotionAttrs                                   #
    #       rkAnimPack_SubMovieTextureAttrs                                  #
    #       rkAnimPack_SubTimeSensorAttrs                                    #
    #                                                                        #
    #       updateAnimPackAttributes                                         #
    ##########################################################################
    def rkAnimPack_AddAudioClipAttrs(self, node):
        mel.eval('addAttr -ln "autoRefresh" -sn "aRefresh" -hasMinValue true -minValue 0.0 -storable true -at "float" ' + node + ';')

        mel.eval('addAttr -ln "autoRefreshTimeLimit" -sn "arTimeLimit" -hasMinValue true -minValue 0.0 -storable true -at "float" ' + node + ';')
        mel.eval('setAttr ' + node + '.autoRefreshTimeLimit 3600.0;')

        mel.eval('addAttr -ln "gain" -sn "gn" -storable true -at "float" ' + node + ';')
        mel.eval('setAttr ' + node + '.gain 1.0;')

        mel.eval('addAttr -ln "load" -sn "ld" -storable true -at bool ' + node + ';')
        mel.eval('setAttr ' + node + '.load true;')
        
        mel.eval('addAttr -ln "pauseTime" -sn "paTime" -storable true -at "float" ' + node + ';')
        mel.eval('addAttr -ln "pitch" -sn "ptch" -hasMinValue true -minValue 0.0 -storable true -at "float" ' + node + ';')
        
        mel.eval('setAttr ' + node + '.pitch 1.0;')

        mel.eval('addAttr -ln "resumeTime" -sn "reTime" -storable true -at "float" ' + node + ';')
        mel.eval('addAttr -ln "startTime" -sn "staTime" -storable true -at "float" ' + node + ';')
        mel.eval('addAttr -ln "stopTime" -sn "staoTime" -storable true -at "float" ' + node + ';')
        
        
    def rkAnimPack_AddHAnimMotionAttrs(self, node):
        mel.eval('addAttr -ln "channels" -sn "chnls" -storable true -dt "string" ' + node + ';')

        mel.eval('addAttr -ln "endFrame" -sn "dFrame" -hasMinValue true -minValue 0 -storable true -at long ' + node + ';')

        mel.eval('addAttr -ln "frameDuration" -sn "frDuration" -hasMinValue true -minValue 0.0 -storable true -at "float" ' + node + ';')
        mel.eval('setAttr ' + node + '.frameDuration 0.1;')

        mel.eval('addAttr -ln "frameIncrement" -sn "frInc" -storable true -at long ' + node + ';')
        mel.eval('setAttr ' + node + '.frameIncrement 1;')

        mel.eval('addAttr -ln "frameIndex" -sn "frIdx" -hasMinValue true -minValue 0 -storable true -at long ' + node + ';')
        mel.eval('addAttr -ln "joints" -sn "jnts" -storable true -dt "string" ' + node + ';')
        mel.eval('addAttr -ln "levelOfArticulation" -sn "loa" -hasMinValue true -minValue -1 -hasMaxValue true -maxValue 4 -storable true -at long ' + node + ';')
        mel.eval('setAttr ' + node + '.levelOfArticulation -1;')

        mel.eval('addAttr -ln "name" -sn "ne" -storable true -at bool ' + node + ';')
        mel.eval('addAttr -ln "startFrame" -sn "staFrame" -hasMinValue true -minValue 0 -storable true -at long ' + node + ';')

    def rkAnimPack_AddMovieTextureAttrs(self, node):
        mel.eval('addAttr -ln "autoRefresh" -sn "aRefresh" -hasMinValue true -minValue 0.0 -storable true -at "float" ' + node + ';')

        mel.eval('addAttr -ln "autoRefreshTimeLimit" -sn "arTimeLimit" -hasMinValue true -minValue 0.0 -storable true -at "float" ' + node + ';')
        mel.eval('setAttr ' + node + '.autoRefreshTimeLimit 3600.0;')

        mel.eval('addAttr -ln "gain" -sn "gn" -storable true -at "float" ' + node + ';')
        mel.eval('setAttr ' + node + '.gain 1.0;')

        mel.eval('addAttr -ln "load" -sn "ld" -storable true -at bool ' + node + ';')
        mel.eval('setAttr ' + node + '.load true;')

        mel.eval('addAttr -ln "pauseTime" -sn "paTime" -storable true -at "float" ' + node + ';')
        mel.eval('addAttr -ln "speed" -sn "spd" -storable true -at "float" ' + node + ';')
        mel.eval('setAttr ' + node + '.speed 1.0;')

        mel.eval('addAttr -ln "resumeTime" -sn "reTime" -storable true -at "float" ' + node + ';')
        mel.eval('addAttr -ln "startTime" -sn "staTime" -storable true -at "float" ' + node + ';')
        mel.eval('addAttr -ln "stopTime" -sn "stoTime" -storable true -at "float" ' + node + ';')
        
    def rkAnimPack_AddTimeSensorAttrs(self, node):
        mel.eval('addAttr -ln "cycleInterval" -sn "cInt" -hasMinValue true -minValue 0.0 -storable true -at "float" ' + node + ';')
        mel.eval('setAttr ' + node + '.cycleInterval 1.0;')

        mel.eval('addAttr -ln "pauseTime" -sn "paTime" -storable true -at "float" ' + node + ';')
        mel.eval('addAttr -ln "resumeTime" -sn "reTime" -storable true -at "float" ' + node + ';')
        mel.eval('addAttr -ln "startTime" -sn "staTime" -storable true -at "float" ' + node + ';')
        mel.eval('addAttr -ln "stopTime" -sn "stoTime" -storable true -at "float" ' + node + ';')

    def rkAnimPack_ClearConnectedFile(self, nodeAttr, nType):
        conList = cmds.listConnections(nodeAttr, d=False, s=True)

        for cons in conList:
            if nType == "AudioClip":
                cmds.disconnectAttr(cons + ".filename", nodeAttr)
                cmds.setAttr(nodeAttr, "", type="string")
            elif nType == "MovieTexture":
                cmds.disconnectAttr(cons + ".fileTextureName", nodeAttr)
                cmds.setAttr(nodeAttr, "", type="string")


    def rkAnimPack_SubAudioClipAttrs(self, node, mtu):
        aRefresh = cmds.getAttr (node + ".autoRefresh")
        arLimit  = cmds.getAttr (node + ".autoRefreshTimeLimit")
        rkGain   = cmds.getAttr (node + ".gain")
        rkLoad   = cmds.getAttr (node + ".load")
        rkPTime  = cmds.getAttr (node + ".pauseTime")
        rkRTime  = cmds.getAttr (node + ".resumeTime")
        rkStaTi  = cmds.getAttr (node + ".startTime")
        rkStoTi  = cmds.getAttr (node + ".stopTime")
        
        cmds.deleteAttr (node + ".autoRefresh")
        cmds.deleteAttr (node + ".autoRefreshTimeLimit")
        cmds.deleteAttr (node + ".gain")
        cmds.deleteAttr (node + ".load")
        cmds.deleteAttr (node + ".pitch")
        cmds.deleteAttr (node + ".pauseTime")
        cmds.deleteAttr (node + ".resumeTime")
        cmds.deleteAttr (node + ".startTime")
        cmds.deleteAttr (node + ".stopTime")
    
        self.rkAnimPack_ClearConnectedFile(node + ".connectedFile", "AudioClip")

        if mtu == 2:
            self.rkAnimPack_AddHAnimMotionAttrs (node)
        elif mtu == 3:
            self.rkAnimPack_AddMovieTextureAttrs(node)
            cmds.setAttr (node + ".autoRefresh", aRefresh)
            cmds.setAttr (node + ".autoRefreshTimeLimit", arLimit)
            cmds.setAttr (node + ".gain", rkGain)
            cmds.setAttr (node + ".load", rkLoad)
            cmds.setAttr (node + ".pauseTime", rkPTime)
            cmds.setAttr (node + ".resumeTime", rkRTime)
            cmds.setAttr (node + ".startTime", rkStaTi)
            cmds.setAttr (node + ".stopTime", rkStoTi)
        elif mtu == 4:
            self.rkAnimPack_AddTimeSensorAttrs  (node)

            cmds.setAttr (node + ".pauseTime", rkPTime)
            cmds.setAttr (node + ".resumeTime", rkRTime)
            cmds.setAttr (node + ".startTime", rkStaTi)
            cmds.setAttr (node + ".stopTime", rkStoTi)
        
    def rkAnimPack_SubHAnimMotionAttrs(self, node, mtu):
        cmds.deleteAttr (node + ".channels")
        cmds.deleteAttr (node + ".endFrame")
        cmds.deleteAttr (node + ".frameDuration")
        cmds.deleteAttr (node + ".frameIncrement")
        cmds.deleteAttr (node + ".frameIndex")
        cmds.deleteAttr (node + ".joints")
        cmds.deleteAttr (node + ".levelOfArticulation")
        cmds.deleteAttr (node + ".name")
        cmds.deleteAttr (node + ".startFrame")

        if mtu == 1:
            self.rkAnimPack_AddAudioClipAttrs(node)
        elif mtu == 3:
            self.rkAnimPack_AddMovieTextureAttrs(node)
        elif mtu == 4:
            self.rkAnimPack_AddTimeSensorAttrs(node)
        
    def rkAnimPack_SubMovieTextureAttrs(self, node, mtu):
        aRefresh = cmds.getAttr (node + ".autoRefresh")
        arLimit  = cmds.getAttr (node + ".autoRefreshTimeLimit")
        rkGain   = cmds.getAttr (node + ".gain")
        rkLoad   = cmds.getAttr (node + ".load")
        rkPTime  = cmds.getAttr (node + ".pauseTime")
        rkRTime  = cmds.getAttr (node + ".resumeTime")
        rkStaTi  = cmds.getAttr (node + ".startTime")
        rkStoTi  = cmds.getAttr (node + ".stopTime")
        
        cmds.deleteAttr (node + ".autoRefresh")
        cmds.deleteAttr (node + ".autoRefreshTimeLimit")
        cmds.deleteAttr (node + ".gain")
        cmds.deleteAttr (node + ".load")
        cmds.deleteAttr (node + ".speed")
        cmds.deleteAttr (node + ".pauseTime")
        cmds.deleteAttr (node + ".resumeTime")
        cmds.deleteAttr (node + ".startTime")
        cmds.deleteAttr (node + ".stopTime")
        
        self.rkAnimPack_ClearConnectedFile(node + ".connectedFile", "MovieTexture")
        
        if mtu == 1:
            self.rkAnimPack_AddAudioClipAttrs(node)
            cmds.setAttr (node + ".autoRefresh", aRefresh)
            cmds.setAttr (node + ".autoRefreshTimeLimit", arLimit)
            cmds.setAttr (node + ".gain", rkGain)
            cmds.setAttr (node + ".load", rkLoad)
            cmds.setAttr (node + ".pauseTime", rkPTime)
            cmds.setAttr (node + ".resumeTime", rkRTime)
            cmds.setAttr (node + ".startTime", rkStaTi)
            cmds.setAttr (node + ".stopTime", rkStoTi)
        elif mtu == 2:
            self.rkAnimPack_AddHAnimMotionAttrs  (node)
        elif mtu == 4:
            self.rkAnimPack_AddTimeSensorAttrs  (node)

            cmds.setAttr (node + ".pauseTime", rkPTime)
            cmds.setAttr (node + ".resumeTime", rkRTime)
            cmds.setAttr (node + ".startTime", rkStaTi)
            cmds.setAttr (node + ".stopTime", rkStoTi)
        
    def rkAnimPack_SubTimeSensorAttrs(self, node, mtu):
        rkPTime  = cmds.getAttr (node + ".pauseTime")
        rkRTime  = cmds.getAttr (node + ".resumeTime")
        rkStaTi  = cmds.getAttr (node + ".startTime")
        rkStoTi  = cmds.getAttr (node + ".stopTime")
        
        cmds.deleteAttr (node + ".cycleInterval")
        cmds.deleteAttr (node + ".pauseTime")
        cmds.deleteAttr (node + ".resumeTime")
        cmds.deleteAttr (node + ".startTime")
        cmds.deleteAttr (node + ".stopTime")

        if mtu == 2:
            self.rkAnimPack_AddHAnimMotionAttrs(node)
        elif mtu == 3:
            self.rkAnimPack_AddMovieTextureAttrs(node)
            cmds.setAttr (node + ".pauseTime", rkPTime)
            cmds.setAttr (node + ".resumeTime", rkRTime)
            cmds.setAttr (node + ".startTime", rkStaTi)
            cmds.setAttr (node + ".stopTime", rkStoTi)
        elif mtu == 4:
            self.rkAnimPack_AddTimeSensorAttrs  (node)

            cmds.setAttr (node + ".pauseTime", rkPTime)
            cmds.setAttr (node + ".resumeTime", rkRTime)
            cmds.setAttr (node + ".startTime", rkStaTi)
            cmds.setAttr (node + ".stopTime", rkStoTi)


    def updateAnimPackAttributes(self, node, attr, newIdx):
        oVal = cmds.getAttr(node + "." + attr)
        
        mtu = newIdx
        
        cmds.setAttr(node + "." + attr, mtu)
        
        if oVal == 0:
            if  mtu == 1:
                self.rkAnimPack_AddAudioClipAttrs(node)
                
            elif mtu == 2:
                self.rkAnimPack_AddHAnimMotionAttrs(node)
                
            elif mtu == 3:
                self.rkAnimPack_AddMovieTextureAttrs(node)

            elif mtu == 4:
                self.rkAnimPack_AddTimeSensorAttrs(node)

        elif oVal == 1:
            self.rkAnimPack_SubAudioClipAttrs(node, mtu)
            
        elif oVal == 2:
            self.rkAnimPack_SubHAnimMotionAttrs(node, mtu)
            
        elif oVal == 3:
            self.rkAnimPack_SubMovieTextureAttrs(node, mtu)
            
        elif oVal == 4:
            self.rkAnimPack_SubTimeSensorAttrs(node, mtu)
    ########################################################################
    ########################################################################
    ########################################################################

    ########################################
    # Load Animation information about the selected HAnimHumanoid
    ########################################
    def loadSelectedHumanoid(self):
        selNodes = cmds.ls(sl=True)
        
        humName = ""
        for nds in selNodes:
            if humName == "":
                ntype = cmds.nodeType(nds)
                if ntype == "transform":
                    x3dType = ""
                    try:
                        x3dType = cmds.getAttr(nds + ".x3dGroupType")
                    except:
                        pass
                    if x3dType == "HAnimHumanoid":
                        humName = nds
        if humName == "":
            self.hmnSelect = self.findChild(QtWidgets.QLineEdit,   'humanoidSelected'  )
            hmnBool = cmds.objExists(self.hmnSelect.text())
            
            if hmnBool == False:
                self.hmnSelect.setText("ERROR: Select HAnimHumanoid")
        else:
            self.hmnSelect = self.findChild(QtWidgets.QLineEdit,   'humanoidSelected'  )
            self.hmnSelect.setText(humName)
            
        self.populateAnimationPackages()
    
    #############################################
    # Populate the Character Graph QTreeWidget
    #############################################
    def populateCharacterGraph(self):
        # Grab the the QLineEdit widget that contains the name of the selected
        # humanoid.
        ldhLine = self.findChild(QtWidgets.QLineEdit,   'humanoidSelected')

        # Grab the QTreeWidget that will list all of the timing nodes
        # aka - rkAnimPack nodes (as TimeSensor, AudioClip, Movie, HAnimMotion)
        apTree  = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes')
        
        # Grab the QTreeWidget that will list all of descendents of the
        # HAnimHumanoid node except for any child timing nodes, 
        # aka - rkAnimPack nodes (as TimeSensor, AudioClip, Movie, HAnimMotion)
        cgTree  = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        cgTree.clear()
        
        selItems = apTree.selectedItems()
        
        animName = ""
        for item in selItems:
            animName = item.text(1)

        humName = ldhLine.text()
        interps = self.listAnimationType(humName)
        hItem = QtWidgets.QTreeWidgetItem(["[" + interps + "] " + humName])
        cgTree.addTopLevelItem(hItem)
        hItem.setExpanded(True)
        
        self.traverseCharacterGraph(hItem, humName, animName)
        
    def traverseCharacterGraph(self, pItem, pName, animName):
        cgTree    = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        jChildren = cmds.listRelatives(pName, children=True)
        
        if jChildren != None:
            for jChild in jChildren:
                nodeType = cmds.nodeType(jChild)
                if nodeType == "joint":
                    interps = self.listAnimationType(jChild)
                    jItem = QtWidgets.QTreeWidgetItem(["[" + interps + "] " + jChild])
                    pItem.addChild(jItem)
                    jItem.setExpanded(True)
            
                    self.traverseCharacterGraph(jItem, jChild, animName)
        
        
    #############################################
    # Populate the Animation Packages QTreeWidget
    #############################################
    def populateAnimationPackages(self):
        # Grab the QTreeWidget that will list all of the timing nodes
        # aka - rkAnimPack nodes (as TimeSensor, AudioClip, Movie, HAnimMotion)
        apTree  = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes')
        apTree.clear()
        
        # Grab the the QLineEdit widget that contains the name of the selected
        # humanoid.
        ldhLine = self.findChild(QtWidgets.QLineEdit,   'humanoidSelected')

        humName = ""
        testName = ldhLine.text()
        humExist = cmds.objExists(testName)
        if humExist == True:
            try:
                x3dType = cmds.getAttr(testName + ".x3dGroupType")
                if x3dType == "HAnimHumanoid":
                    humName = testName
            except Exception as e:
                print(f"Exception Type: {type(e).__name__}")
                print(f"Exception Message: {e}")                            

        # List all rkAnimPack nodes
        apNodes = cmds.ls(type='rkAnimPack')
        
        # Populate the QTreeWidget with the list.
        for apn in apNodes:
            x3dType  = cmds.getAttr(apn + '.mimickedType')
            maskHAnimMotion = False
            
            typeText = "Not Designated"
            if  x3dType == 1:
                typeText = "AudioClip"
            elif x3dType == 2:
                typeText = "HAnimMotion"
                if humName != "":
                    findMe = False
                    children = cmds.listRelatives(humName, c=True)
                    for child in children:
                        if apn == child:
                            findMe = True
                    if findMe == False:
                        maskHAnimMotion = True
                else:
                    maskHAnimMotion = True
            elif x3dType == 3:
                typeText = "MovieTexture"
            elif x3dType == 4:
                typeText = "TimeSensor"
         
            if maskHAnimMotion == False:
                nodeItem = QtWidgets.QTreeWidgetItem(apTree)
                nodeItem.setText(0, typeText)
                nodeItem.setText(1, apn     )
        
        if humName != "":
            self.populateCharacterGraph()
        else:
            cgTree  = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
            cgTree.clear()
            
    

    # HAnim Compliant Skeleton - Tab Functions
    def setHaNameText(self, text):
        if text != "":
            self.haNameText = text
        #if text == "":
        #    self.haNameEd.setText(self.haNameText)
        #else:
        #    self.haNameText = text


    def setHaLOAValue(self, index):
        self.haLOAValue = index


    def createHAnimCompliantSkeleton(self):
        isMore = False
        
        haNodeName = self.haNameText
        loaValue   = self.haLOAValue
        
        if loaValue == 0:
            mayaNodeName = cmds.createNode('transform', n=haNodeName)
        
            cmds.select(mayaNodeName)
            cmds.addAttr(longName='x3dGroupType', dataType='string', keyable=False)
            cmds.setAttr(mayaNodeName + '.x3dGroupType', "HAnimHumanoid", type='string', lock=True)

            cmds.addAttr(longName='levelOfArticulation', shortName='LOA', attributeType='long', keyable=False, defaultValue=-1, minValue=-1, maxValue=4)
            cmds.setAttr(mayaNodeName + '.LOA', 0)
            
            cmds.addAttr(longName="skeletalConfiguration", dataType="string")
            cmds.setAttr(mayaNodeName + ".skeletalConfiguration", "BASIC", type="string")

            # This uses the 'sticker' script to update the Maya node's image in the Outliner. 
            # This just gives it a visual queue to the content author that this Maya 'transform'
            # node is not a typical transform node and will be exported as an HAnimNode.
            try:
                stk.put(mayaNodeName, "x3dHAnimHumanoid.png")
            except Exception as e:
                print(f"Exception Type: {type(e).__name__}")
                print(f"Exception Message: {e}")                            
                print("Oops... Node Sticker Didn't work.")
            
            nodeExists = True
            mainName = "hanim_humanoid_root"
            suffix   = 0
            compName = mainName
            while nodeExists == True:
                nodeExists = cmds.objExists(compName)
                if nodeExists == True:
                    compName = mainName + "_" + str(suffix)
                    suffix += 1
                    
            mayaJointName = cmds.createNode('joint', n=compName, p=mayaNodeName)
            
            #centerValue = [0, 30.530001,-0.707600] * 0.0254
            pivot = [0.0, 0.902462, -0.01797304]

            cmds.setAttr(mayaJointName + '.offsetParentMatrix', 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, pivot[0], pivot[1], pivot[2], 1.0, type='matrix')
            
        elif loaValue == 1 or loaValue == 2 or loaValue == 3 or loaValue == 4:
            isMore = True

        if isMore == True:
            #self.uiPaths
            melCmd  = 'file -import -type "mayaBinary" -ignoreVersion -ra true '
            melCmd += '-mergeNamespacesOnClash false -namespace ' + haNodeName + ' '#"rawkeeImport" '
            melCmd += '-options "v=0;" -pr -importFrameRate false -importTimeRange "keep" '
            melCmd += '"' + self.uiPaths + 'hanimLOA' + str(loaValue) + '_HumanoidFullSkeleton.mb";'
            
            mel.eval(melCmd)
            
            stk.reveal()


    def captureTranslateGeneral(self, updateQTree=True):
        print("capTraGen: " + str(updateQTree))
        # The 'fromNode' is the RawKee 'rkAnimPack' node
        # The 'toNode' is the Maya 'joint' node
        aPackTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes'      )
        cgTree    = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        humanoid  = self.findChild(QtWidgets.QLineEdit, 'humanoidSelected')
        humanBool = cmds.objExists(humanoid.text())
        
        if humanBool == True:
            x3dType = ""
            try:
                x3dType = cmds.getAttr(humanoid.text() + ".x3dGroupType")
            except:
                pass
                
            if x3dType == "HAnimHumanoid":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "AudioClip" or selPacks[0].text(0) == "MovieTexture" or selPacks[0].text(0) == "TimeSensor":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            selSGNodes = cgTree.selectedItems()
                            
                            for sgNode in selSGNodes:
                                conFound = False
                                
                                nodes = cmds.listConnections(sgNode.text(0).split("] ")[1] + ".translate", d=True, et=True, type="expression")
                                if nodes != None:
                                    for node in nodes:

                                        rkAnPks = cmds.listConnections(node, s=True, et=True, sh=True, type="rkAnimPack")
                                        if rkAnPks != None:
                                            for pack in rkAnPks:
                                                if pack == fromNode:
                                                    conFound = True
                                    
                                if conFound == False:
                                    toNode = sgNode.text(0).split("] ")[1]
                                    melCmd  = "string $msg;"
                                    melCmd += "$msg=" + fromNode + ".message;"

                                    interpolator = "PositionInterpolator"
                                    attribute    = "translate"

                                    expName = cmds.createNode('expression')
                                    cmds.addAttr(expName, longName='receivedData', at='double3')
                                    cmds.addAttr(expName, longName='receivedDataX', shortName='rdx',  at='double', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='receivedDataY', shortName='rdy',  at='double', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='receivedDataZ', shortName='rdz',  at='double', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='x3dInterpolatorType', shortName='x3dIT', dataType='string')
                                    cmds.setAttr(expName + '.x3dInterpolatorType', interpolator, type='string', lock=True)
                                    cmds.connectAttr(toNode + '.translate', expName + '.receivedData')

                                    cmds.setAttr( expName + '.expression', melCmd, type='string')
                                    
                                    self.addWatcher(fromNode, toNode)
        if updateQTree == True:
            self.populateCharacterGraph()
        else:
            print("Translate: Didn't run populateCharacterGraph()")


    def captureRotateGeneral(self, updateQTree=True):
        print("capRotGen: " + str(updateQTree))
        # The 'fromNode' is the RawKee 'rkAnimPack' node
        # The 'toNode' is the Maya 'joint' node
        aPackTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes'      )
        cgTree    = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        humanoid  = self.findChild(QtWidgets.QLineEdit, 'humanoidSelected')
        humanBool = cmds.objExists(humanoid.text())
        
        if humanBool == True:
            x3dType = ""
            try:
                x3dType = cmds.getAttr(humanoid.text() + ".x3dGroupType")
            except:
                pass
                
            if x3dType == "HAnimHumanoid":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "AudioClip" or selPacks[0].text(0) == "MovieTexture" or selPacks[0].text(0) == "TimeSensor":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            selSGNodes = cgTree.selectedItems()
                            
                            for sgNode in selSGNodes:
                                conFound = False
                                
                                nodes = cmds.listConnections(sgNode.text(0).split("] ")[1] + ".rotate", d=True, et=True, type="expression")
                                if nodes != None:
                                    for node in nodes:

                                        rkAnPks = cmds.listConnections(node, s=True, et=True, sh=True, type="rkAnimPack")
                                        if rkAnPks != None:
                                            for pack in rkAnPks:
                                                if pack == fromNode:
                                                    conFound = True
                                    
                                if conFound == False:
                                    toNode = sgNode.text(0).split("] ")[1]
                                    melCmd  = "string $msg;"
                                    melCmd += "$msg=" + fromNode + ".message;"

                                    interpolator = "OrientationInterpolator"
                                    attribute    = "rotate"

                                    expName = cmds.createNode('expression')
                                    cmds.addAttr(expName, longName='receivedData', at='double3')
                                    cmds.addAttr(expName, longName='receivedDataX', shortName='rdx',  at='doubleAngle', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='receivedDataY', shortName='rdy',  at='doubleAngle', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='receivedDataZ', shortName='rdz',  at='doubleAngle', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='x3dInterpolatorType', shortName='x3dIT', dataType='string')
                                    cmds.setAttr(expName + '.x3dInterpolatorType', interpolator, type='string', lock=True)
                                    cmds.connectAttr(toNode + '.rotate', expName + '.receivedData')

                                    cmds.setAttr( expName + '.expression', melCmd, type='string')

                                    self.addWatcher(fromNode, toNode)

        if updateQTree == True:
            self.populateCharacterGraph()
        else:
            print("Rotate: Didn't run populateCharacterGraph()")


    def captureScaleGeneral(self, updateQTree=True):
        print("capScaGen: " + str(updateQTree))
        # The 'fromNode' is the RawKee 'rkAnimPack' node
        # The 'toNode' is the Maya 'joint' node
        aPackTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes'      )
        cgTree    = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        humanoid  = self.findChild(QtWidgets.QLineEdit, 'humanoidSelected')
        humanBool = cmds.objExists(humanoid.text())
        
        if humanBool == True:
            x3dType = ""
            try:
                x3dType = cmds.getAttr(humanoid.text() + ".x3dGroupType")
            except:
                pass
                
            if x3dType == "HAnimHumanoid":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "AudioClip" or selPacks[0].text(0) == "MovieTexture" or selPacks[0].text(0) == "TimeSensor":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            selSGNodes = cgTree.selectedItems()
                            
                            for sgNode in selSGNodes:
                                conFound = False
                                
                                nodes = cmds.listConnections(sgNode.text(0).split("] ")[1] + ".scale", d=True, et=True, type="expression")
                                if nodes != None:
                                    for node in nodes:

                                        rkAnPks = cmds.listConnections(node, s=True, et=True, sh=True, type="rkAnimPack")
                                        if rkAnPks != None:
                                            for pack in rkAnPks:
                                                if pack == fromNode:
                                                    conFound = True
                                    
                                if conFound == False:
                                    toNode = sgNode.text(0).split("] ")[1]
                                    melCmd  = "string $msg;"
                                    melCmd += "$msg=" + fromNode + ".message;"

                                    interpolator = "PositionInterpolator"
                                    attribute    = "scale"

                                    expName = cmds.createNode('expression')
                                    cmds.addAttr(expName, longName='receivedData', at='double3')
                                    cmds.addAttr(expName, longName='receivedDataX', shortName='rdx',  at='double', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='receivedDataY', shortName='rdy',  at='double', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='receivedDataZ', shortName='rdz',  at='double', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='x3dInterpolatorType', shortName='x3dIT', dataType='string')
                                    cmds.setAttr(expName + '.x3dInterpolatorType', interpolator, type='string', lock=True)
                                    cmds.connectAttr(toNode + '.scale', expName + '.receivedData')

                                    cmds.setAttr( expName + '.expression', melCmd, type='string')
                                    
                                    self.addWatcher(fromNode, toNode)
                                    
        if updateQTree == True:
            self.populateCharacterGraph()
        else:
            print("Scale: Didn't run populateCharacterGraph()")
        
        
    def releaseTranslateGeneral(self, updateQTree=True):
        print("reTraGen: " + str(updateQTree))
        # The 'fromNode' is the RawKee 'rkAnimPack' node
        # The 'toNode' is the Maya 'joint' node
        aPackTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes'      )
        cgTree    = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        humanoid  = self.findChild(QtWidgets.QLineEdit, 'humanoidSelected')
        humanBool = cmds.objExists(humanoid.text())
        
        if humanBool == True:
            x3dType = ""
            try:
                x3dType = cmds.getAttr(humanoid.text() + ".x3dGroupType")
            except:
                pass
                
            if x3dType == "HAnimHumanoid":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "AudioClip" or selPacks[0].text(0) == "MovieTexture" or selPacks[0].text(0) == "TimeSensor":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            
                            selSGNodes = cgTree.selectedItems()
                            
                            for sgNode in selSGNodes:
                                expName = ""

                                expNodes = cmds.listConnections(sgNode.text(0).split("] ")[1] + ".translate", d=True, et=True, type="expression")
                                if expNodes != None:
                                    for expNode in expNodes:
                                        rkAnPks = cmds.listConnections(expNode, s=True, et=True, sh=True, type="rkAnimPack")
                                        if rkAnPks != None:
                                            for pack in rkAnPks:
                                                if pack == fromNode:
                                                    expName = expNode

                                if expName != "":
                                    cmds.delete(expName)
        if updateQTree == True:
            self.populateCharacterGraph()


    def releaseRotateGeneral(self, updateQTree=True):
        print("reRotGen: " + str(updateQTree))
        # The 'fromNode' is the RawKee 'rkAnimPack' node
        # The 'toNode' is the Maya 'joint' node
        aPackTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes'      )
        cgTree    = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        humanoid  = self.findChild(QtWidgets.QLineEdit, 'humanoidSelected')
        humanBool = cmds.objExists(humanoid.text())
        
        if humanBool == True:
            x3dType = ""
            try:
                x3dType = cmds.getAttr(humanoid.text() + ".x3dGroupType")
            except:
                pass
                
            if x3dType == "HAnimHumanoid":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "AudioClip" or selPacks[0].text(0) == "MovieTexture" or selPacks[0].text(0) == "TimeSensor":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            
                            selSGNodes = cgTree.selectedItems()
                            
                            for sgNode in selSGNodes:
                                expName = ""

                                expNodes = cmds.listConnections(sgNode.text(0).split("] ")[1] + ".rotate", d=True, et=True, type="expression")
                                if expNodes != None:
                                    for expNode in expNodes:
                                        rkAnPks = cmds.listConnections(expNode, s=True, et=True, sh=True, type="rkAnimPack")
                                        if rkAnPks != None:
                                            for pack in rkAnPks:
                                                if pack == fromNode:
                                                    expName = expNode

                                if expName != "":
                                    cmds.delete(expName)
        if updateQTree == True:
            self.populateCharacterGraph()


    def releaseScaleGeneral(self, updateQTree=True):
        print("reScaGen: " + str(updateQTree))
        # The 'fromNode' is the RawKee 'rkAnimPack' node
        # The 'toNode' is the Maya 'joint' node
        aPackTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes'      )
        cgTree    = self.findChild(QtWidgets.QTreeWidget, 'characterTree')
        humanoid  = self.findChild(QtWidgets.QLineEdit, 'humanoidSelected')
        humanBool = cmds.objExists(humanoid.text())
        
        if humanBool == True:
            x3dType = ""
            try:
                x3dType = cmds.getAttr(humanoid.text() + ".x3dGroupType")
            except:
                pass
                
            if x3dType == "HAnimHumanoid":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "AudioClip" or selPacks[0].text(0) == "MovieTexture" or selPacks[0].text(0) == "TimeSensor":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            
                            selSGNodes = cgTree.selectedItems()
                            
                            for sgNode in selSGNodes:
                                expName = ""

                                expNodes = cmds.listConnections(sgNode.text(0).split("] ")[1] + ".scale", d=True, et=True, type="expression")
                                if expNodes != None:
                                    for expNode in expNodes:
                                        rkAnPks = cmds.listConnections(expNode, s=True, et=True, sh=True, type="rkAnimPack")
                                        if rkAnPks != None:
                                            for pack in rkAnPks:
                                                if pack == fromNode:
                                                    expName = expNode

                                if expName != "":
                                    cmds.delete(expName)
        if updateQTree == True:
            self.populateCharacterGraph()
        
    def captureTRGeneral(self, updateQTree=True):
        print("TRGen: " + str(updateQTree))
        self.captureTranslateGeneral(False)
        self.captureRotateGeneral(updateQTree)
        
    def captureAllGeneral(self, updateQTree=True):
        print("AllGen: " + str(updateQTree))
        self.captureTRGeneral(False)
        self.captureScaleGeneral(updateQTree)
        
    def releaseTRGeneral(self, updateQTree=True):
        print("reTRGen: " + str(updateQTree))
        self.releaseTranslateGeneral(False)
        self.releaseRotateGeneral(updateQTree)
        
    def releaseAllGeneral(self, updateQTree=True):
        print("reAllGen: " + str(updateQTree))
        self.releaseTRGeneral(False)
        self.releaseScaleGeneral(updateQTree)


    def captureRotateForHAnimMotion(self):
        # The 'fromNode' is the RawKee 'rkAnimPack' node
        # The 'toNode' is the Maya 'joint' node
        aPackTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes'      )
        humanoid  = self.findChild(QtWidgets.QLineEdit, 'humanoidSelected')
        humanBool = cmds.objExists(humanoid.text())
        
        if humanBool == True:
            x3dType = ""
            try:
                x3dType = cmds.getAttr(humanoid.text() + ".x3dGroupType")
            except:
                pass
                
            if x3dType == "HAnimHumanoid":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "HAnimMotion":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            
                            skChildren = cmds.listRelatives(humanoid.text(), ad=True, type='joint')
                            if skChildren != None:
                                for j in skChildren:
                                    conFound = False
                                    
                                    nodes = cmds.listConnections(j + ".rotate", d=True, et=True, type="expression")
                                    if nodes != None:
                                        for node in nodes:

                                            rkAnPks = cmds.listConnections(node, s=True, et=True, sh=True, type="rkAnimPack")
                                            if rkAnPks != None:
                                                for pack in rkAnPks:
                                                    if pack == fromNode:
                                                        conFound = True
                                        
                                    if conFound == False:
                                        toNode = j
                                        melCmd  = "string $msg;"

                                        interpolator = "HAnimMotion"
                                        attribute    = "rotate"
                                        melCmd += "$msg=" + fromNode + ".message;"

                                        expName = cmds.createNode('expression')
                                        cmds.addAttr(expName, longName='receivedData', at='double3')
                                        cmds.addAttr(expName, longName='receivedDataX', shortName='rdx',  at='doubleAngle', k=True, p='receivedData')
                                        cmds.addAttr(expName, longName='receivedDataY', shortName='rdy',  at='doubleAngle', k=True, p='receivedData')
                                        cmds.addAttr(expName, longName='receivedDataZ', shortName='rdz',  at='doubleAngle', k=True, p='receivedData')
                                        cmds.addAttr(expName, longName='x3dInterpolatorType', shortName='x3dIT', dataType='string')
                                        cmds.setAttr(expName + '.x3dInterpolatorType', interpolator, type='string', lock=True)
                                        cmds.connectAttr(toNode + '.rotate', expName + '.receivedData')

                                        cmds.setAttr( expName + '.expression', melCmd, type='string')

                                        self.addWatcher(fromNode, toNode)

        self.populateCharacterGraph()


    def releaseRotateForHAnimMotion(self):
        # The 'fromNode' is the RawKee 'rkAnimPack' node
        # The 'toNode' is the Maya 'joint' node
        aPackTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes'      )
        humanoid  = self.findChild(QtWidgets.QLineEdit, 'humanoidSelected')
        humanBool = cmds.objExists(humanoid.text())
        
        if humanBool == True:
            x3dType = ""
            try:
                x3dType = cmds.getAttr(humanoid.text() + ".x3dGroupType")
            except:
                pass
                
            if x3dType == "HAnimHumanoid":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "HAnimMotion":
                        fromNode = selPacks[0].text(1)
                        pass
                        
                        if cmds.objExists(fromNode):
                            
                            skChildren = cmds.listRelatives(humanoid.text(), ad=True, type='joint')
                            if skChildren != None:

                                for j in skChildren:
                                    expName = ""

                                    expNodes = cmds.listConnections(j + ".rotate", d=True, et=True, type="expression")
                                    if expNodes != None:

                                        for expNode in expNodes:
                                            
                                            rkAnPks = cmds.listConnections(expNode, s=True, et=True, sh=True, type="rkAnimPack")
                                            if rkAnPks != None:

                                                for pack in rkAnPks:

                                                    if pack == fromNode:
                                                        expName = expNode

                                    if expName != "":
                                        cmds.delete(expName)
        self.populateCharacterGraph()
        
                                        
    def listAnimationType(self, animatedNode):
        animText = " NONE"
        aPackTree = self.findChild(QtWidgets.QTreeWidget, 'x3dNodes')
        selPacks = aPackTree.selectedItems()
        
        timingName = ""
        
        if len(selPacks) > 0:
            timingName = selPacks[0].text(1)
        else:
            return "  NA "
            
        #nTypeIdx = cmds.getAttr(timingName + ".mimickedType")
        
        relExpNodes = []
        expNodes = cmds.listConnections(animatedNode, d=True, et=True, type="expression")
        if expNodes != None:
            for expNode in expNodes:
                rkAnPks = cmds.listConnections(expNode, s=True, et=True, sh=True, type="rkAnimPack")
                if rkAnPks != None:
                    for pack in rkAnPks:
                        if pack == timingName:
                            relExpNodes.append(expNode)
        
        tStr = ["-", "/", "-", "/", "-"]
        for expNode in relExpNodes:
            interp = cmds.getAttr(expNode + ".x3dInterpolatorType")
            if interp == "HAnimMotion":
                return "HAnMo"
            elif interp == "PositionInterpolator":
                connections = cmds.listConnections(expNode, p=True, s=True, et=True, sh=True)
                
                for i in range(len(connections)):
                    cons = connections[i].split('.')
                    if cons[1] != "message":
                        if cons[1] == "translate":
                            tStr[0] = "T"
                        elif cons[1] == "scale":
                            tStr[4] = "S"
                    
            elif interp == "OrientationInterpolator":
                tStr[2] = "R"
        
        if len(relExpNodes) > 0:
            animText = tStr[0] + tStr[1] + tStr[2] + tStr[3] + tStr[4]
        
        return animText
        
    def addWatcher(self, fromNode, toNode):
        selList = om.MSelectionList()
        selList.add(fromNode)
        selList.add(toNode)
        fromObj = selList.getDependNode(0)
        toObj   = selList.getDependNode(1)

        fromID = om.MNodeMessage.addNodeAboutToDeleteCallback(fromObj, self.deleteRouteExpression)
        #fDelID = om.MNodeMessage.addNodeDestroyedCallback(    fromObj, self.nodeDeletedUpdateGUI, clientData="stuff" )
        self.CBIDs.append(fromID)
        #self.CBIDs.append(fDelID)
        #cmds.addAttr(fromNode, longName='rkMessageId', at='double', defaultValue=fromID)

        toID   = om.MNodeMessage.addNodeAboutToDeleteCallback(  toObj, self.deleteRouteExpression)
        #tDelID = om.MNodeMessage.addNodeDestroyedCallback(      toObj, self.nodeDeletedUpdateGUI, clientData="stuff" )
        self.CBIDs.append(toID)
        #self.CBIDs.append(tDelID)
        #cmds.addAttr(toNode, longName='rkMessageId', at='double', defaultValue=toID)
                
    def deleteRouteExpression(self, nodeObj, dgMod, clientData):
        mIter = om.MItDependencyGraph(nodeObj, rkfn.kExpression, om.MItDependencyGraph.kDownstream, om.MItDependencyGraph.kBreadthFirst, om.MItDependencyGraph.kNodeLevel)
        while not mIter.isDone():
            dgMod.deleteNode(mIter.currentNode())
            
            mIter.next()

        dgMod.doIt()
    
    def nodeDeletedUpdateGUI(self, node, clientData):
        try:
            self.populateAnimationPackages()
        except:
            pass
            
        #myID = cmds.getAttr(nodeObj.name() + ".rkMessageId")
        #om.MMessage.removeCallback(myID)