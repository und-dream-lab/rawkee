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
        return "from rawkee.RKCharacterEditor import RKCharacterEditor\nrkCEWidget = RKCharacterEditor()"
        
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
        self.genericSkeletonPanel = None
        self.artPanel = None
        self.animationPanel = None 
        self.testPanel = None
        
        self.uiPaths = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
        self.uiPaths += "/auxilary/"
        
        self.hanimPath     = self.uiPaths + "RKCharacterEditorHAnimSkeletonPanel.ui"
        self.advancedPath  = self.uiPaths + "RKCharacterEditorAdvancedSkeletonPanel.ui"
        self.genericPath   = self.uiPaths + "RKCharacterEditorGenericSkeletonPanel.ui"
        self.artPath       = self.uiPaths + "RKCharacterEditor_aRT_Panel.ui"
        self.animationPath = self.uiPaths + "RKCharacterEditorAnimationPanel.ui"
        self.testPath      = self.uiPaths + "RKQSSTestPanel.ui"
        
        self.haNameText = "Eric"
        self.haLOAValue = 0
        
        self.rotOrderValue = 0
        
        self.hanimCS  = None
        self.haNameEd = None
        self.haLOA    = None
        self.rotCBGN  = None
        self.rotCBHA  = None
        self.rotCBAS  = None
        
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
        
        self.hamTransAct   = None
        self.rmHamTransAct = None
        
        self.hamRotsAct    = None
        self.rmHamRotsAct  = None
        
        self.allTrsRotsAct   = None
        self.allRotsAct      = None
        self.rmAllTrsRotsAct = None
        self.rmAllRotsAct    = None
        
        self.cDupButton = None
        self.sDupIPose  = None
        self.transToDup = None
        
        self.sAnimPack   = None
        
        self.CBIDs       = None
        
        self.sourceRoot    = ""
        self.duplicateRoot = ""
        
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
        
        self.allRotsAct      = QAction("Capture Root Translate and All Joints Rotate Animations")
        self.allTrsRotsAct   = QAction("Capture All Translate and All Joints Rotate Animations" )
        self.hamTransAct     = QAction("Capture Translate Animation - Selected Joints")
        self.hamRotsAct      = QAction("Capture Rotate Animation - Selected Joints")
        

        self.rmAllTrsRotsAct = QAction("Release All Translate and All Joints Rotate Animations")
        self.rmAllRotsAct    = QAction("Release Root Translate and All Joints Rotate Animations")
        self.rmHamTransAct   = QAction("Release Translate Animation - Selected Joints")
        self.rmHamRotsAct    = QAction("Release Rotate Animation - Selected Joints")
        
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

        # Generic Skeleton Functions
        if not self.genericSkeletonPanel:
            genericGUIFile = QtCore.QFile(self.genericPath)
            genericGUIFile.open(QtCore.QFile.ReadOnly)
            self.genericSkeletonPanel = loader.load(genericGUIFile)
        self.tab_widget.addTab(self.genericSkeletonPanel, "Generic X3D/HAnim Skeleton Functions")

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
        if mel.eval("exists asCreateGameEngineRootMotion") == True:
            if not self.advancedSkeletonPanel:
                advGUIFile = QtCore.QFile(self.advancedPath)
                advGUIFile.open(QtCore.QFile.ReadOnly)
                self.advancedSkeletonPanel = loader.load(advGUIFile)

                self.tab_widget.addTab(self.advancedSkeletonPanel, "Advanced Skeleton Functions")
        else:
            print("asCreateGameEngineRootMotion() function not found")
        
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
        
        # Attempt to load Selected Root joint
        self.loadSelectedHumanoid()
        
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
        self.rotCBAS  = self.findChild(QtWidgets.QComboBox,   'rotOrderComboBoxAS' )
        self.rotCBGN  = self.findChild(QtWidgets.QComboBox,   'rotOrderComboBoxGN' )
        self.rotCBHA  = self.findChild(QtWidgets.QComboBox,   'rotOrderComboBoxHA' )
        
        # Generic Skeleton - Tab
        self.cDupButton = self.findChild(QtWidgets.QPushButton, 'createDuplicate')
        self.cDupIPose  = self.findChild(QtWidgets.QPushButton, 'setDuplicateIPose')
        self.transToDup = self.findChild(QtWidgets.QPushButton, 'transferToDuplicate')
        
        # Advanced Skeleton - Tab
        adString = "AdvancedSkeleton"
        envString = mel.eval('getenv MAYA_SCRIPT_PATH')
        if adString in envString:
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
        
        ##############
        self.hamTransAct.triggered.connect(self.captureTranslateForHAnimMotion)
        
        ##############
        self.rmHamTransAct.triggered.connect(self.releaseTranslateForHAnimMotion)
        
        self.allRotsAct.triggered.connect(self.captureTrsAndAllRotsForHAnimMotion)
        self.allTrsRotsAct.triggered.connect(self.captureAllTrsRotsForHAnimMotion)
        self.hamRotsAct.triggered.connect(self.captureRotateForHAnimMotion)
        
        self.rmAllRotsAct.triggered.connect(self.releaseTrsAndAllRotsForHAnimMotion)
        self.rmAllTrsRotsAct.triggered.connect(self.releaseTrsAndAllRotsForHAnimMotion)
        self.rmHamRotsAct.triggered.connect(self.releaseRotateForHAnimMotion)
        
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
        
        # HAnim Joint Rotation Order
        self.rotCBAS.currentIndexChanged.connect(self.setRotOrderValue)
        self.rotCBGN.currentIndexChanged.connect(self.setRotOrderValue)
        self.rotCBHA.currentIndexChanged.connect(self.setRotOrderValue)
        
        # Generic Skeleton - Tab
        self.cDupButton.clicked.connect(self.genericStep2)
        self.cDupIPose.clicked.connect(self.genericStep4)
        self.transToDup.clicked.connect(self.genericStep5)
        
        # Advanced Skeleton - Tab
        # estIPose will be == to None if Advanced Skeleton is not found.
        adString = "AdvancedSkeleton"
        envString = mel.eval('getenv MAYA_SCRIPT_PATH')
        if adString in envString:
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
            
            self.genButton.clicked.connect(self.asGenerateHAnimCompliantSkeleton)#cmds.rkAdvancedSkeleton)
            self.ipoButton.clicked.connect(cmds.rkLoadIPoseForASGS)
            self.cpbButton.clicked.connect(cmds.rkDefPoseForASGS  )
            self.trwButton.clicked.connect(cmds.rkTransferSkinASGS)

    #################################################
    # Advnaced Skeleton Set Duplicate Skeleton
    #################################################
    def asGenerateHAnimCompliantSkeleton(self):
        cmds.rkAdvancedSkeleton()
        rotOrder = self.rotOrderValue
        self.changeSkeletonRotOrder("GameSkeletonRoot_M", rotOrder)
        
        
    #################################################
    # Generic Create Duplicate Skeleton
    #################################################
    def genericStep2(self):
        print("genericStep2")
        # Create a duplicate skeleton
        ##################################
        # Create a HAnimHumanoid transform
        ##################################
        self.duplicateRoot = ""
        
        rotOrder = self.rotOrderValue
        
        selectNames = cmds.ls(sl=True)
        if selectNames == None:
            return
        self.sourceRoot = selectNames[0]
        actualName = cmds.createNode('transform', ss=True, name='HAnimHumanoid')
        cmds.addAttr(actualName, longName='x3dGroupType', dataType='string', keyable=False)
        cmds.setAttr(actualName + '.x3dGroupType', "HAnimHumanoid", type='string', lock=True)
        cmds.addAttr(actualName, longName='levelOfArticulation', shortName='LOA', attributeType='long', keyable=False, defaultValue=0, minValue=-1, maxValue=4)
        cmds.addAttr(actualName, longName="skeletalConfiguration", dataType="string")
        cmds.setAttr(actualName+'.skeletalConfiguration', "BASIC", type="string")
        try:
            stk.put(actualName,  "x3dHAnimHumanoid.png")
        except Exception as e:
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {e}")                            
            print("Oops... Node Sticker Didn't work.")

        newRootName = cmds.duplicate(self.sourceRoot, rr=True, rc=True)
        cmds.parent(newRootName, actualName)
        
        self.changeSkeletonRotOrder(newRootName, rotOrder)
        
        # Assign parentConstraints
        self.duplicateRoot = newRootName[0]
        
        jSel = om.MSelectionList()
        jSel.add(self.sourceRoot)
        jSel.add(self.duplicateRoot)
        sRoot = om.MFnDagNode(jSel.getDagPath(0))
        nRoot = om.MFnDagNode(jSel.getDagPath(1))
        
        self.addHAnimConstraints(sRoot, nRoot)
        

    def addHAnimConstraints(self, sLeader, nFollower):
        #cmds.parentConstraint(sLeader.name(), nFollower.name(), mo=True, st=["x","y","z"], w=1)
        cmds.parentConstraint(sLeader.name(), nFollower.name(), mo=True, w=1)
        for i in range(sLeader.childCount()):
            self.addHAnimConstraints(om.MFnDagNode(sLeader.child(i)), om.MFnDagNode(nFollower.child(i)))


    #################################################
    # Set Duplicate I-Pose
    ##################################################
    def genericStep4(self):
        print("genericStep4")

        dSel = om.MSelectionList()
        dSel.add(self.duplicateRoot)
        dupDag = om.MFnDagNode(dSel.getDagPath(0))
        
        
        # Remove Constraints
        constraints = []
        self.constraintRemover(dupDag, constraints)
        for con in constraints:
            if cmds.objExists(con):
                cmds.delete(con)
        constraints.clear()
        
        # Freeze Joints
        cmds.makeIdentity(self.duplicateRoot, apply=True, t=True, r=True, s=True, n=False, pn=True, jo=True)
        
        # Transfer joint.translate values to joint.opm.translate
        self.flipTranslateToPMO(self.duplicateRoot)
        mJoints = cmds.listRelatives(self.duplicateRoot, ad=True, type="joint")
        if mJoints != None:
            for mJoint in mJoints:
                self.flipTranslateToPMO(mJoint)
        
        # Set BindPose for Duplicate skeleton
        if mJoints != None:
            mJoints.append(self.duplicateRoot)
            cmds.select(mJoints)
            poseName = cmds.dagPose(save=True, selection=True, name="iPose")
            cmds.addAttr(poseName, longName='x3dHAnimPose', dataType="string")
            cmds.setAttr(poseName + ".x3dHAnimPose", "iPose", type="string")

        
        # Assign new parentConstraints
        jSel = om.MSelectionList()
        jSel.add(self.sourceRoot)
        jSel.add(self.duplicateRoot)
        sRoot = om.MFnDagNode(jSel.getDagPath(0))
        nRoot = om.MFnDagNode(jSel.getDagPath(1))
        
        self.addHAnimConstraints(sRoot, nRoot)
        
            
    def flipTranslateToPMO(self, nodeName):
        x = cmds.getAttr(nodeName + ".translateX")
        y = cmds.getAttr(nodeName + ".translateY")
        z = cmds.getAttr(nodeName + ".translateZ")
        
        opm = []
        opm = cmds.getAttr(nodeName + ".offsetParentMatrix")
        
        opm[12] = opm[12] + x
        opm[13] = opm[13] + y
        opm[14] = opm[14] + z
        cmds.setAttr(nodeName + ".offsetParentMatrix", opm, type="matrix")
    
        cmds.setAttr(nodeName + ".translateX", 0.0)
        cmds.setAttr(nodeName + ".translateY", 0.0)
        cmds.setAttr(nodeName + ".translateZ", 0.0)

        
    def constraintRemover(self, dagNode, constraints):
        for i in range(dagNode.childCount()):
            cNode = om.MFnDagNode(dagNode.child(i))
            if cNode.typeName == "joint":
                self.constraintRemover(cNode, constraints)
            elif cNode.typeName == "parentConstraint":
                constraints.append(cNode.name())


    #################################################
    # Transfer Bound Skin to Duplicate Skeleton
    ##################################################
    def genericStep5(self):
        print("genericStep5")
        
        # Collect Bound Meshes
        skelSel = om.MSelectionList()
        skelSel.add(self.sourceRoot)
        srDag = om.MFnDagNode(skelSel.getDagPath(0))
        skins = []
        self.collectBoundSkins(srDag, skins)
        
        #Collect Skin Clusters
        skinClusters = []
        for skin in skins:
            self.collectSkinClusterFromSkin(skin, skinClusters)
        
        #Collect lists of potential Duplicate influencer dag paths per skin cluster
        #for future reattachement. 
        infDagPaths = []
        for sc in skinClusters:
            skDags = om.MDagPathArray()
            
            jtSels = om.MSelectionList()
            jtSels.add(self.duplicateRoot)
            fullDupRootName = jtSels.getDagPath(0).fullPathName()
            jtSels.clear()
            
            curInf = []
            curInf = cmds.skinCluster(sc.name(), q=True, inf=True)
            for tinf in curInf:
                cons = []
                cons = cmds.listConnections(tinf, fnn=True, type='parentConstraint')
                if cons != None:
                    if fullDupRootName in cons[0]:
                        #This add the parentConstraint's DAG parent to the MSelectionList, which allows us to get the parent's DagPath later
                        jtSels.add(cons[0].rsplit("|", 1)[0])
            
            for i in range(jtSels.length()):
                skDags.append(jtSels.getDagPath(i))
                
            infDagPaths.append(skDags)
                
            #self.getAllInfluencesForSkinCluster(sc, infDagPaths)
        
        meshWeights = []
        infLengths  = []
        for i in range(len(skins)):
            self.getWeightsFromSkin(skins[i], skinClusters[i], meshWeights, infLengths)
        
        #Select All Bound Meshes
        actList = om.MSelectionList()
        for skin in skins:
            actList.add(skin.fullPathName())
        om.MGlobal.setActiveSelectionList(actList)
        
        #Unbined Meshes
        cmds.DetachSkin(unbindAll=True, deleteHistroy=True)
        
        #Make skins identity in worldspace.
        for skin in skins:
            rels = cmds.listRelatives(skin.name(), parent=True, fullPath=True)
            ##########################################################
            # Insert code to check if parent transform is keyed.
            # if it is, break connections.
            connections = []
            connections = cmds.listConnections(rels[0], c=True, p=True)
            
            cLen = len(connections)
            cIter = 0
            while cIter < cLen:
                if "translate" in connections[cIter] or "rotate" in connections[cIter] or "scale" in connections[cIter]:
                    try:
                        cmds.disconnectAttr(connections[cIter+1], connections[cIter])
                    except:
                        print("disconnectAttr failed")
                cIter += 2
                
            # Format the mesh within the transform properly
            pv=[0, 0, 0]
            cmds.parent(rels[0], world=True)
            cmds.xform(rels[0], pivots=pv, worldSpace=True)
            cmds.makeIdentity(rels[0], apply=True, t=True, r=True, s=True, n=False, pn=True, jo=True)
        
        #Rebind Meshes to Duplicate Skeleton
        for i in range(len(skins)):
            cmds.delete(skins[i].fullPathName(), ch=True)
            cmds.skinCluster(infDagPaths[i], skins[i].fullPathName(), tsb=True)
            
            #self.bindSkinToSpecificInfluencers(skins[i], infDagPaths[i])
            
        #Set Skin weights of source skeleton to new skeleton
        self.overWriteWeights(skins, meshWeights, infDagPaths)


    def overWriteWeights(self, skins, weights, infPaths):
        for i in range(len(skins)):
            smlist = om.MSelectionList()
            smlist.add(skins[i].fullPathName())
            mpath = smlist.getDagPath(0)
            
            comp_ids   = [m for m in range(skins[i].numVertices)]
            single_fn  = om.MFnSingleIndexedComponent()
            shape_comp = single_fn.create(om.MFn.kMeshVertComponent)
            single_fn.addElements(comp_ids)
            
            sc = []
            sc = cmds.listConnections(skins[i].fullPathName(), type='skinCluster', source=True, destination=False)
            
            scList = om.MSelectionList()
            scList.add(sc[0])
            skinCluster = omAnim.MFnSkinCluster(scList.getDependNode(0))
            dagPathList = skinCluster.influenceObjects()
            dpIndices = om.MIntArray()

            infNum = len(infPaths[i])
            dpLen  = len(dagPathList)
            
            for j in range(infNum):
                for k in range(dpLen):
                    if infPaths[i][j].fullPathName() == dagPathList[k].fullPathName():
                        dpIndices.append(k)
            
            skSel = om.MSelectionList()
            skSel.add(skins[i].fullPathName())
            skinCluster.setWeights(skSel.getDagPath(0), shape_comp, dpIndices, weights[i], normalize=False, returnOldWeights=False)


    def bindSkinToSpecificInfluencers(self, skin, jointPaths):
        bindList = om.MSelectionList()
        for path in jointPaths:
            bindList.add(path)
        bindList.add(self.duplicateRoot)
        bindList.add(skin.name())
        om.MGlobal.setActiveSelectionList(bindList)
        
        cmds.skinCluster(tsb=True)
        

    def getWeightsFromSkin(self, skin, skinCluster, meshWeights, infLengths):
        smlist = om.MSelectionList()
        smlist.add(skin.fullPathName())
        mpath = smlist.getDagPath(0)
        
        comp_ids   = [m for m in range(skin.numVertices)]
        single_fn  = om.MFnSingleIndexedComponent()
        shape_comp = single_fn.create(om.MFn.kMeshVertComponent)
        single_fn.addElements(comp_ids)
        
        weights = []
        numInf  = 0
        weights, numInf = skinCluster.getWeights(mpath, shape_comp)
        
        meshWeights.append(weights)
        infLengths.append(numInf)
        

    # Deprecated
    def getAllInfluencesForSkinCluster(self, sc, idPaths):
        ancSel = om.MSelectionList()
        ancSel.add(self.duplicateRoot)
        dupRootPath = ancSel.getDagPath(0)
        dPaths = sc.influenceObjects()
        #for i in range(len(dPaths)):
        #    print("Joint DPath: " + dPaths[i].fullPathName() + ", Index: " + str(i))
        dupPaths = []

        # Find the appropriate Parent Constraint for the Influence Object
        dupSel = om.MSelectionList()
        for path in dPaths:
            joint = om.MFnDagNode(path)
            mIter = om.MItDependencyGraph(joint.object(), rkfn.kParentConstraint, om.MItDependencyGraph.kDownstream, om.MItDependencyGraph.kBreadthFirst, om.MItDependencyGraph.kNodeLevel)
            while not mIter.isDone():
                pcNode = om.MFnDagNode(mIter.currentNode())
                if dupRootPath.fullPathName() in pcNode.fullPathName():
                    dupSel.add(pcNode.fullPathName().removesuffix("|" + pcNode.name()))
                    
                mIter.next()
        
        print("SC: " + sc.name() + ", Infs: " + str(dupSel.length()))
        
        for i in range(dupSel.length()):
            tNode = om.MFnDependencyNode(dupSel.getDependNode(i))
            print("    Inf Node: " + tNode.name() + ", Type: " + tNode.typeName + ", index: " + str(i+1))
            dupPaths.append(dupSel.getDagPath(i))
        
        idPaths.append(dupPaths)                        


    def collectSkinClusterFromSkin(self, mNode, skinClusters):
        smlist = om.MSelectionList()
        smlist.add(mNode.name())
        mpath = smlist.getDagPath(0)
        
        skClusters = []
        scIter = om.MItDependencyGraph(mNode.object(), rkfn.kSkinClusterFilter, om.MItDependencyGraph.kUpstream, om.MItDependencyGraph.kBreadthFirst, om.MItDependencyGraph.kNodeLevel)
        while not scIter.isDone():
            skClusters.append(omAnim.MFnSkinCluster(scIter.currentNode()))
            scIter.next()
        
        if len(skClusters) > 0:
            skinClusters.append(skClusters[0])

        
    def collectBoundSkins(self, joint, skins):
        addCount = 0
        mIter = om.MItDependencyGraph(joint.object(), rkfn.kMesh, om.MItDependencyGraph.kDownstream, om.MItDependencyGraph.kBreadthFirst, om.MItDependencyGraph.kNodeLevel)
        while not mIter.isDone():
            mNode = om.MFnMesh(mIter.currentNode())
            hasFound = False
            for skin in skins:
                if skin.fullPathName() == mNode.fullPathName():
                    hasFound = True
            if hasFound == False:
                skins.append(mNode)
            
            mIter.next()
            
        for i in range(joint.childCount()):
            cNode = om.MFnDagNode(joint.child(i))
            if cNode.typeName == "joint":
                self.collectBoundSkins(cNode, skins)
        
            
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
                self.pMenu.addAction(self.allTrsRotsAct)
                self.pMenu.addSeparator()
                self.pMenu.addAction(self.hamTransAct)
                self.pMenu.addAction(self.hamRotsAct)
                self.pMenu.addSeparator()
                self.pMenu.addSeparator()
                self.pMenu.addAction(self.rmAllRotsAct)
                self.pMenu.addAction(self.rmAllTrsRotsAct)
                self.pMenu.addSeparator()
                self.pMenu.addAction(self.rmHamTransAct)
                self.pMenu.addAction(self.rmHamRotsAct)
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
                
                apType = cmds.getAttr(tNode + ".mimickedType")
                if apType != 0 or apType != 2:
                    rels = cmds.listRelatives(tNode, p=True)
                    if rels is not None:
                        isHumanoid = False
                        x3dType = ""
                        try:
                            x3dType = cmds.getAttr(rels[0] + ".x3dGroupType")
                            isHumanoid = True
                        except:
                            isHumanoid = False
                        
                        if isHumanoid == False:
                            tNode = rels[0]

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

            x3dType = ""
            try:
                x3dType = cmds.getAttr(hName + ".x3dGroupType")
            except:
                pass

            atSet = newNType.currentIndex() + 1
            if x3dType == "HAnimHumanoid":
                aName = cmds.createNode("rkAnimPack", n=tName, p=hName)
                self.updateAnimPackAttributes( aName, "mimickedType", atSet)
                self.populateAnimationPackages()

            elif atSet == 1 or atSet == 3 or atSet == 4:
                aName = cmds.createNode("rkAnimPack", n=tName)
                self.updateAnimPackAttributes( aName, "mimickedType", atSet)
                self.populateAnimationPackages()
            else:
                print("No HAnimMotion support for non-HAnimHumanoid characters. X3D Type: " + x3dType + "HName: " + hName)
            
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
        humanoid = self.findChild(QtWidgets.QLineEdit, 'humanoidSelected')

        oVal = cmds.getAttr(node + "." + attr)
        
        mtu = newIdx
        
        cmds.setAttr(node + "." + attr, mtu)
        
        if oVal == 0:
            if  mtu == 1:
                self.rkAnimPack_AddAudioClipAttrs(node)
                
            elif mtu == 2:
                self.rkAnimPack_AddHAnimMotionAttrs(node)
                loaValue = cmds.getAttr(humanoid.text() + ".LOA")
                cmds.setAttr(node + ".loa", loaValue)
                
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
            
        cmds.setAttr(node + ".timelineStopFrame", 10)
        
    ########################################################################
    ########################################################################
    ########################################################################

    ########################################
    # Old pre-CGESkin version
    # Load Animation information about the selected HAnimHumanoid
    ########################################
    """
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
    """

    
    #############################################################
    # Version with both HAnimHumanoid and CGESkin Support
    # Load Animation information about the selected HAnimHumanoid
    #############################################################
    def loadSelectedHumanoid(self):
        humName = ""
        isSearchingForRoot = True
        selNodes = cmds.ls(sl=True)

        if len(selNodes) > 0:
            nType = cmds.nodeType(selNodes[0])
            if nType == "transform":
                x3dType = ""
                try:
                    x3dType = cmds.getAttr(selNodes[0] + ".x3dGroupType")
                except:
                    print("x3dGroupType not found")

                if x3dType == "HAnimHumanoid":
                    humName = selNodes[0]

            elif nType == "joint":
                currentCharNode = selNodes[0]
                
                while isSearchingForRoot == True:
                    rels = cmds.listRelatives(currentCharNode, p=True)
                    
                    if rels is not None:
                        rType = cmds.nodeType(rels[0])
                        if rType == "joint":
                            currentCharNode = rels[0]
                            
                        elif rType == "transform":
                            isSearchingForRoot = False
                            x3dType = ""
                            try:
                                x3dType = cmds.getAttr(rels[0] + ".x3dGroupType")
                            except:
                                print("x3dGroupType not found")

                            if x3dType == "HAnimHumanoid":
                                currentCharNode = rels[0]

                            humName = currentCharNode
                            cmds.select(currentCharNode)
                            
                        else:
                            isSearchingForRoot = False
                            humName = currentCharNode
                            cmds.select(currentCharNode)
                    else:
                        isSearchingForRoot = False
                        humName = currentCharNode
                        cmds.select(currentCharNode)
                
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
        topName = ldhLine.text()

        topType = cmds.nodeType(topName)
        if topType == "joint":
            jList = om.MSelectionList()
            jList.add(topName)
            jNode = om.MFnDagNode(jList.getDagPath(0))
            
            pObj = jNode.parent(0)
            if pObj is not None:
                pNode = om.MFnDagNode(pObj)
                if pNode.typeName == "transform":
                    ldhLine.setText(pNode.name())
                    self.populateCharacterGraph()
                    return

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
                ntype = cmds.nodeType(testName)
                if ntype == "transform" or ntype == "joint":
                    humName = testName
                else:
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
        
    def setRotOrderValue(self, index):
        self.rotOrderValue = index

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
            cmds.setAttr(mayaJointName + '.rotateOrder', rotOrder)
            
        elif loaValue == 1 or loaValue == 2 or loaValue == 3 or loaValue == 4:
            isMore = True

        if isMore == True:
            #self.uiPaths
            melCmd  = 'file -import -type "mayaBinary" -ignoreVersion -ra true '
            melCmd += '-mergeNamespacesOnClash false -namespace ' + haNodeName + ' '#"rawkeeImport" '
            melCmd += '-options "v=0;" -pr -importFrameRate false -importTimeRange "keep" '
            melCmd += '"' + self.uiPaths + 'hanimLOA' + str(loaValue) + '_HumanoidFullSkeleton.mb";'
            
            result = mel.eval(melCmd)
            
            tSelect = cmds.ls(haNodeName + "*:hanim_LOA" + str(loaValue))
            #humanoid = haNodeName + ":" + "hanim_LOA" + str(loaValue)
            
            print("The tSelect: " + tSelect[len(tSelect)-1])
            rootJoint = self.findRootJoint(tSelect[len(tSelect)-1])
            print("Root Joint: " + rootJoint)
            self.changeSkeletonRotOrder(rootJoint, self.rotOrderValue)
            
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
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
                                    cmds.addAttr(expName, longName='receivedDataX', shortName='rdx',  at='doubleLinear', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='receivedDataY', shortName='rdy',  at='doubleLinear', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='receivedDataZ', shortName='rdz',  at='doubleLinear', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='x3dInterpolatorType', shortName='x3dIT', dataType='string')
                                    cmds.setAttr(expName + '.x3dInterpolatorType', interpolator, type='string', lock=True)
                                    print("To Node:" + toNode)
                                    cmds.connectAttr(toNode + '.' + attribute, expName + '.receivedData')

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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
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


    def captureTranslateForHAnimMotion(self):
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "HAnimMotion":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            selSGNodes = cgTree.selectedItems()
                            
                            for j in selSGNodes:
#                            skChildren = cmds.listRelatives(humanoid.text(), ad=True, type='joint')
#                            if skChildren != None:
#                                for j in skChildren:
    
                                if j.text(0).split("] ")[1] == humanoid.text():
                                    continue
                                    
                                conFound = False
                                
                                nodes = cmds.listConnections(j.text(0).split("] ")[1] + ".translate", d=True, et=True, type="expression")
                                if nodes != None:
                                    for node in nodes:

                                        rkAnPks = cmds.listConnections(node, s=True, et=True, sh=True, type="rkAnimPack")
                                        if rkAnPks != None:
                                            for pack in rkAnPks:
                                                if pack == fromNode:
                                                    conFound = True
                                    
                                if conFound == False:
                                    toNode = j.text(0).split("] ")[1]
                                    melCmd  = "string $msg;"

                                    interpolator = "HAnimMotion"
                                    attribute    = "translate"
                                    melCmd += "$msg=" + fromNode + ".message;"

                                    expName = cmds.createNode('expression')
                                    cmds.addAttr(expName, longName='receivedData', at='double3')
                                    cmds.addAttr(expName, longName='receivedDataX', shortName='rdx',  at='doubleLinear', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='receivedDataY', shortName='rdy',  at='doubleLinear', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='receivedDataZ', shortName='rdz',  at='doubleLinear', k=True, p='receivedData')
                                    cmds.addAttr(expName, longName='x3dInterpolatorType', shortName='x3dIT', dataType='string')
                                    cmds.setAttr(expName + '.x3dInterpolatorType', interpolator, type='string', lock=True)
                                    cmds.connectAttr(toNode + '.' + attribute, expName + '.receivedData')

                                    cmds.setAttr( expName + '.expression', melCmd, type='string')
                                    
                                    self.addWatcher(fromNode, toNode)

        self.populateCharacterGraph()


    def captureRotateForHAnimMotion(self):
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "HAnimMotion":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            selSGNodes = cgTree.selectedItems()
                            
                            for j in selSGNodes:
#                            skChildren = cmds.listRelatives(humanoid.text(), ad=True, type='joint')
#                            if skChildren != None:
#                                for j in skChildren:
                                if j.text(0).split("] ")[1] == humanoid.text():
                                    continue
                                    
                                conFound = False
                                
                                nodes = cmds.listConnections(j.text(0).split("] ")[1] + ".rotate", d=True, et=True, type="expression")
                                if nodes != None:
                                    for node in nodes:

                                        rkAnPks = cmds.listConnections(node, s=True, et=True, sh=True, type="rkAnimPack")
                                        if rkAnPks != None:
                                            for pack in rkAnPks:
                                                if pack == fromNode:
                                                    conFound = True
                                    
                                if conFound == False:
                                    toNode = j.text(0).split("] ")[1]
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


    def findRootJoint(self, node):
        nodeType = cmds.nodeType(node)
        if nodeType == "joint":
            return node
        else:
            jChildren = cmds.listRelatives(node, children=True)
            if jChildren != None:
                for jChild in jChildren:
                    name = self.findRootJoint(jChild)
                    if name != "":
                        return name
        
        return ""
        
    def changeSkeletonRotOrder(self, jointName, rotOrder):
        cmds.setAttr(jointName + ".rotateOrder", rotOrder)
        children = cmds.listRelatives(jointName, children=True)
        if children != None:
            for child in children:
                slist = om.MSelectionList()
                slist.add(child)
                dagNode = om.MFnDagNode(slist.getDependNode(0))
                if dagNode.typeName == "joint":
                    self.changeSkeletonRotOrder(child, rotOrder)


    def captureAllTrsRotsForHAnimMotion(self):
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "HAnimMotion":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            skChildren = cmds.listRelatives(humanoid.text(), ad=True, type='joint')
                            if skChildren != None:

                                ### Add Translate for Root Joint Node
                                for l in skChildren:
                                    conFound = False
                                    
                                    nodes = cmds.listConnections(l + ".translate", d=True, et=True, type="expression")
                                    if nodes != None:
                                        for node in nodes:
                                            
                                            rkAnPks = cmds.listConnections(node, s=True, et=True, sh=True, type="rkAnimPack")
                                            if rkAnPks != None:
                                                for pack in rkAnPks:
                                                    if pack == fromNode:
                                                        conFound = True
                                        
                                    if conFound == False:
                                        toNode = l
                                        melCmd  = "string $msg;"

                                        interpolator = "HAnimMotion"
                                        attribute    = "translate"
                                        melCmd += "$msg=" + fromNode + ".message;"

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

                                ### Add Rotate for all Joint Nodes                               
                                for k in skChildren:
                                    conFound = False
                                    
                                    nodes = cmds.listConnections(k + ".rotate", d=True, et=True, type="expression")
                                    if nodes != None:
                                        for node in nodes:

                                            rkAnPks = cmds.listConnections(node, s=True, et=True, sh=True, type="rkAnimPack")
                                            if rkAnPks != None:
                                                for pack in rkAnPks:
                                                    if pack == fromNode:
                                                        conFound = True
                                        
                                    if conFound == False:
                                        toNode = k
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
        
        
    def captureTrsAndAllRotsForHAnimMotion(self):
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "HAnimMotion":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            skChildren = cmds.listRelatives(humanoid.text(), ad=True, type='joint')
                            if skChildren != None:

                                ### Add Translate for Root Joint Node
                                joint = self.findRootJoint(humanoid.text())
                                if joint != "":
                                    conFound = False
                                    
                                    nodes = cmds.listConnections(joint + ".translate", d=True, et=True, type="expression")
                                    if nodes != None:
                                        for node in nodes:
                                            rkAnPks = cmds.listConnections(node, s=True, et=True, sh=True, type="rkAnimPack")
                                            if rkAnPks != None:
                                                for pack in rkAnPks:
                                                    if pack == fromNode:
                                                        conFound = True
                                        
                                    if conFound == False:
                                        toNode = joint
                                        melCmd  = "string $msg;"

                                        interpolator = "HAnimMotion"
                                        attribute    = "translate"
                                        melCmd += "$msg=" + fromNode + ".message;"

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

                                ### Add Rotate for all Joint Nodes                               
                                for k in skChildren:
                                    conFound = False
                                    
                                    nodes = cmds.listConnections(k + ".rotate", d=True, et=True, type="expression")
                                    if nodes != None:
                                        for node in nodes:

                                            rkAnPks = cmds.listConnections(node, s=True, et=True, sh=True, type="rkAnimPack")
                                            if rkAnPks != None:
                                                for pack in rkAnPks:
                                                    if pack == fromNode:
                                                        conFound = True
                                        
                                    if conFound == False:
                                        toNode = k
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


    def releaseTranslateForHAnimMotion(self):
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "HAnimMotion":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            selSGNodes = cgTree.selectedItems()
                            
                            for j in selSGNodes:

                                if j.text(0).split("] ")[1] == humanoid.text():
                                    continue
                                    
                            #skChildren = cmds.listRelatives(humanoid.text(), ad=True, type='joint')
                            #if skChildren != None:

                            #    for j in skChildren:
                                expName = ""

                                expNodes = cmds.listConnections(j.text(0).split("] ")[1] + ".translate", d=True, et=True, type="expression")
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


    def releaseRotateForHAnimMotion(self):
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "HAnimMotion":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            selSGNodes = cgTree.selectedItems()
                            
                            for j in selSGNodes:

                                if j.text(0).split("] ")[1] == humanoid.text():
                                    continue
                                    
                            #skChildren = cmds.listRelatives(humanoid.text(), ad=True, type='joint')
                            #if skChildren != None:

                            #    for j in skChildren:
                                expName = ""

                                expNodes = cmds.listConnections(j.text(0).split("] ")[1] + ".rotate", d=True, et=True, type="expression")
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
        
                                        
    def releaseTrsAndAllRotsForHAnimMotion(self):
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
                ntype = cmds.nodeType(humanoid.text())
                if ntype == "transform":
                    x3dType = "Transform"
                elif ntype == "joint":
                    x3dType = "HAnimJoint"# humName = testName
                
            if x3dType == "HAnimHumanoid" or x3dType == "Transform" or x3dType == "HAnimJoint":
                selPacks = aPackTree.selectedItems()
                
                if len(selPacks) > 0:
                    if selPacks[0].text(0) == "HAnimMotion":
                        fromNode = selPacks[0].text(1)
                        
                        if cmds.objExists(fromNode):
                            skChildren = cmds.listRelatives(humanoid.text(), ad=True, type='joint')
                            if skChildren != None:
                                
                                ### Add Translate for Root Joint Node
                                for j in skChildren:
                                    expName = ""

                                    expNodes = cmds.listConnections(j + ".translate", d=True, et=True, type="expression")
                                    if expNodes != None:

                                        for expNode in expNodes:
                                            
                                            rkAnPks = cmds.listConnections(expNode, s=True, et=True, sh=True, type="rkAnimPack")
                                            if rkAnPks != None:

                                                for pack in rkAnPks:

                                                    if pack == fromNode:
                                                        expName = expNode

                                    if expName != "":
                                        cmds.delete(expName)
                                        
                                
                                for k in skChildren:
                                    expName = ""

                                    expNodes = cmds.listConnections(k + ".rotate", d=True, et=True, type="expression")
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
                connections = cmds.listConnections(expNode, p=True, s=True, et=True, sh=True)
                
                for i in range(len(connections)):
                    cons = connections[i].split('.')
                    if cons[1] != "message":
                        if cons[1] == "translate":
                            tStr[0] = "T"
                        elif cons[1] == "rotate":
                            tStr[2] = "R"
#                return "HAnMo"
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