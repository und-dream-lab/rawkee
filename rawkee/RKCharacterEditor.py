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

        
        #self.create_actions()

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


    #def create_actions(self):
    #    pass

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
        

    def setHaNameText(self, text):
        if text == "":
            self.haNameEd.setText(self.haNameText)
        else:
            self.haNameText = text
        
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
        

    def buildHAnimAnimationTree(self):
        pass

        
    def putAnimationOptions(self, node):
        pass


    def getAnimationOptions(self, node):
        pass

            
    