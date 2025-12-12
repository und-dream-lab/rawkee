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

########################################
# Not sure why I imported this
########################################
# from functools import partial

#Python API 1.0 needed to access MQtUtil
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel  as mel

#Python API 2.0 needed to register command with API 2.0 plugin
import maya.api.OpenMaya as aom
from   maya.api.OpenMaya import MFn as rkfn
import maya.api.OpenMayaAnim as omAnim

#Sticker App for applying Outliner icons
import rawkee.nodes.sticker    as stk

#To get local file path for html file
from rawkee import RKWeb3D

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


#################################################################
# Custom Pyside QComboBox so that it will display
# the current dagPose nodes in the file.
# Tried to implement it using callbacks, but the widgets 
# were deleted... somehow outide of scope. However, the 
# custom ComboBox achieved the same thing.
class RKDagPoseComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rootJoint = ""
        self.rkPoses = []
        self.otPoses = []

    def showPopup(self):
        
        self.clear()
        self.rkPoses.clear()
        self.otPoses.clear()
        
        poses = cmds.ls(type='dagPose')
        
        selNodes = cmds.ls(sl=True)
        if len(selNodes) > 0:
            if   cmds.nodeType(selNodes[0]) == "transform":
                try:
                    x3dType = cmds.getAttr(selNodes[0] + ".x3dGroupType")
                    if x3dType == "HAnimHumanoid":
                        hRels = cmds.listRelatives(c=True, type="joint")
                        if hRels is not None:
                            self.rootJoint = hRels[0]
                except:
                    pass
            elif cmds.nodeType(selNodes[0]) == "joint":
                self.rootJoint = self.getRoot(selNodes[0])

        if cmds.objExists(self.rootJoint) == True:
            cmds.select(self.rootJoint)
        else:
            self.rootJoint = ""
        
        if self.rootJoint != "" and len(poses) > 0:
            connectedPoses = cmds.listConnections(self.rootJoint, p=False, t='dagPose')
            
            if connectedPoses is not None:
                for cPose in connectedPoses:
                    pSplit = cPose.split('_')
                    if "ASFalse" in cPose and pSplit[0] == "rk" and pSplit[1] != "IPose" and pSplit[1] != "APose" and pSplit[1] != "TPose" and pSplit[1] != "EPose":
                        self.rkPoses.append(pSplit[1])
                        self.otPoses.append(cPose)
            
            self.addItems(self.rkPoses)
        
        # 3. Call the original implementation to finally display the list to the user
        super().showPopup()

        
    def getRoot(self, joint):
        currentCharNode = joint
        isSearchingForRoot = True
        
        while isSearchingForRoot == True:
            rels = cmds.listRelatives(currentCharNode, p=True)
            
            if rels is not None:
                rType = cmds.nodeType(rels[0])
                if rType == "joint":
                    currentCharNode = rels[0]
                else:
                    isSearchingForRoot = False
            else:
                isSearchingForRoot = False
                
        return currentCharNode


class RKBindPoseEditor(MayaQWidgetDockableMixin, QWidget):
    
    OBJECT_NAME = "RKBindPoseEditor"
    
    @classmethod
    def bindpose_editor_control_name(cls):
        return "{0}WorkspaceControl".format(cls.OBJECT_NAME)
        
    @classmethod
    def workspace_ui_script(cls):
        return "from rawkee.RKBindPoseEditor import RKBindPoseEditor\nrkBPEWidget = RKBindPoseEditor()"
        
    @classmethod
    def workplace_close_command(cls):
        return "self.cleanUpOnEditorClose()"

    
    def __init__(self):
        super().__init__()
        
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("RawKee Bind Pose Editor")
        self.setMinimumSize(300,300)

        self.add_to_bindpose_editor_workspace_control()
        
        self.rkDefaultPoses = ["", "", "", ""]
        self.rootJoint = ""
        self.newPoseNameValue = ""

        self.uiPaths = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
        self.uiPaths += "/auxilary/"
        self.bpePath = self.uiPaths + "RKBindPoseEditorPanel.ui"
        
        loader = QtUiTools.QUiLoader()
        loader.registerCustomWidget(RKDagPoseComboBox)
        
        bpeGUIFile = QtCore.QFile(self.bpePath)
        bpeGUIFile.open(QtCore.QFile.ReadOnly)
        self.bpePanel = loader.load(bpeGUIFile, self)
        
        ######################################################
        # Top Level Layout                                   #
        main_layout = QtWidgets.QHBoxLayout(self)            #
        main_layout.addWidget(self.bpePanel)
        
        ######################################################
        # Set ComboBox and Load Button for a Bind Poses      #
        self.bpToLoad = "List of RawKee Bind Poses"
        self.bpComboBox = self.findChild(RKDagPoseComboBox, 'poseComboBox')
        self.bpComboBox.currentTextChanged.connect(self.setCurrentSelection)

        self.restorePoseButton = self.findChild(QtWidgets.QPushButton, 'restorePoseButton')
        self.restorePoseButton.clicked.connect(self.restoreSelectedBindPose)
        
        self.deletePoseButton = self.findChild(QtWidgets.QPushButton, 'deletePoseButton')
        self.deletePoseButton.clicked.connect(self.deleteSelectedBindPose)
        
        self.newPoseName    = self.findChild(QtWidgets.QLineEdit, 'newPoseName'   )
        # The regular expression r"^[^\s_]*$" will match any string that does not contain whitespace (\s) or underscores (_).
        # Prevent the user from entering whitepace or an underscore
        regex = QRegularExpression(r'^[^\s_\-"\']*$')
        validator = QRegularExpressionValidator(regex, self.newPoseName)
        self.newPoseName.setValidator(validator)
        self.newPoseName.textEdited.connect(self.updateNewPoseNameValue)
        self.newPoseName.returnPressed.connect(self.createNewPoseOnEnter)
        
        ######################################################
        # Set RawKee Bind Pose Buttons                       #
        self.iPoseButton = self.findChild(QtWidgets.QPushButton, 'iPoseButton')
        self.iPoseButton.clicked.connect(self.restoreRawKeeIPose)

        self.aPoseButton = self.findChild(QtWidgets.QPushButton, 'aPoseButton')
        self.aPoseButton.clicked.connect(self.restoreRawKeeAPose)

        self.tPoseButton = self.findChild(QtWidgets.QPushButton, 'tPoseButton')
        self.tPoseButton.clicked.connect(self.restoreRawKeeTPose)

        self.ePoseButton = self.findChild(QtWidgets.QPushButton, 'ePoseButton')
        self.ePoseButton.clicked.connect(self.restoreRawKeeEPose)
        
        #######################################################
        # Set RawKee Bind Pose Status CheckBoxes              #
        self.grabDefaultRKPoses()
        
        #IPose
        iVal = False
        if cmds.objExists(self.rkDefaultPoses[0]) == True:
            iVal = True
        self.iPoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'iPoseCheckBox')
        self.iPoseCheckBox.setChecked(iVal)
        self.iPoseCheckBox.stateChanged.connect(self.rawKeeIPoseStatusChange)
        
        #APose
        aVal = False
        if cmds.objExists(self.rkDefaultPoses[1]) == True:
            aVal = True
        self.aPoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'aPoseCheckBox')
        self.aPoseCheckBox.setChecked(aVal)
        self.aPoseCheckBox.stateChanged.connect(self.rawKeeAPoseStatusChange)
        
        #TPose
        tVal = False
        if cmds.objExists(self.rkDefaultPoses[2]) == True:
            tVal = True
        self.tPoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'tPoseCheckBox')
        self.tPoseCheckBox.setChecked(tVal)
        self.tPoseCheckBox.stateChanged.connect(self.rawKeeTPoseStatusChange)
        
        #EPose
        eVal = False
        if cmds.objExists(self.rkDefaultPoses[3]) == True:
            eVal = True
        self.ePoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'ePoseCheckBox')
        self.ePoseCheckBox.setChecked(eVal)
        self.ePoseCheckBox.stateChanged.connect(self.rawKeeEPoseStatusChange)
        

    def cleanUpOnEditorClose(self):
        print("Cleaned")


    def add_to_bindpose_editor_workspace_control(self):
        bindpose_editor_workspace_control = omui.MQtUtil.findControl(self.bindpose_editor_control_name())
        if bindpose_editor_workspace_control:
            bindpose_editor_workspace_control_ptr = int(bindpose_editor_workspace_control)
            bindpose_editor_widget_ptr = int(getCppPointer(self)[0])
            
            omui.MQtUtil.addWidgetToMayaLayout(bindpose_editor_widget_ptr, bindpose_editor_workspace_control_ptr)

            
    ############################################################
    def setCurrentSelection(self, text):
        self.bpToLoad = text
        
        
    def restoreSelectedBindPose(self):
        if self.bpToLoad != "List of RawKee Bind Poses":
            searchName = "rk_" + self.bpToLoad + "_"
            actualBPName = ""
            
            self.bpComboBox = self.findChild(RKDagPoseComboBox, 'poseComboBox')
            for pose in self.bpComboBox.otPoses:
                if searchName in pose:
                    actualBPName = pose
            
            if cmds.objExists(actualBPName) == True:
                cmds.dagPose(actualBPName, restore=True )

        
    def deleteSelectedBindPose(self):
        if self.bpToLoad != "List of Bind Poses":
            searchName = "rk_" + self.bpToLoad + "_"
            actualBPName = ""
            
            self.bpComboBox = self.findChild(RKDagPoseComboBox, 'poseComboBox')
            for pose in self.bpComboBox.otPoses:
                if searchName in pose:
                    actualBPName = pose
            
            if cmds.objExists(actualBPName) == True:
                cmds.delete(actualBPName)

        
    def restoreRawKeeIPose(self):
        if cmds.objExists(self.rkDefaultPoses[0]) == True:
            cmds.dagPose( self.rkDefaultPoses[0], restore=True )

        
    def restoreRawKeeAPose(self):
        if cmds.objExists(self.rkDefaultPoses[1]) == True:
            cmds.dagPose( self.rkDefaultPoses[1], restore=True )
        
        
    def restoreRawKeeTPose(self):
        if cmds.objExists(self.rkDefaultPoses[2]) == True:
            cmds.dagPose( self.rkDefaultPoses[2], restore=True )
        
        
    def restoreRawKeeEPose(self):
        if cmds.objExists(self.rkDefaultPoses[3]) == True:
            cmds.dagPose( self.rkDefaultPoses[3], restore=True )


    ################################################
    def rawKeeIPoseStatusChange(self, state):
        if cmds.objExists(self.rkDefaultPoses[0]) == True:
            cmds.delete(  self.rkDefaultPoses[0])
            self.rkDefaultPoses[0] = ""
            
        if state == Qt.CheckState.Checked.value:
            self.createNodeRKDagPose(0, "iPoseCheckBox")
            

    def rawKeeAPoseStatusChange(self, state):
        if cmds.objExists(self.rkDefaultPoses[1]) == True:
            cmds.delete(  self.rkDefaultPoses[1])
            self.rkDefaultPoses[1] = ""
            
        if state == Qt.CheckState.Checked.value:
            self.createNodeRKDagPose(1, "aPoseCheckBox")
            

    def rawKeeTPoseStatusChange(self, state):
        if cmds.objExists(self.rkDefaultPoses[2]) == True:
            cmds.delete(  self.rkDefaultPoses[2])
            self.rkDefaultPoses[2] = ""
            
        if state == Qt.CheckState.Checked.value:
            self.createNodeRKDagPose(2, "tPoseCheckBox")
            

    def rawKeeEPoseStatusChange(self, state):
        if cmds.objExists(self.rkDefaultPoses[3]) == True:
            cmds.delete(  self.rkDefaultPoses[3])
            self.rkDefaultPoses[3] = ""
            
        if state == Qt.CheckState.Checked.value:
            self.createNodeRKDagPose(3, "ePoseCheckBox")
            
    def createNewPoseOnEnter(self):
        if self.newPoseNameValue != "" and self.rootJoint != "":
            pName = "rk_" + self.newPoseNameValue + "_ASFalse_num"
            cmds.dagPose( self.rootJoint, save=True, selection=False, name=pName )
            self.newPoseNameValue = ""
            self.newPoseName = self.findChild(QtWidgets.QLineEdit, 'newPoseName')
            self.newPoseName.setText(self.newPoseNameValue)
        
    
    def updateNewPoseNameValue(self, text):
        self.newPoseNameValue = text
    

    def createNodeRKDagPose(self, poseIdx, poseCB):
        print("Pose: " + self.rkDefaultPoses[poseIdx])
        if self.rkDefaultPoses[poseIdx] != "":
            cmds.delete(self.rkDefaultPoses[poseIdx])

        poseName = "rk_"
        if   poseIdx == 0:
            poseName = poseName + "IPose_ASFalse_num"
        elif poseIdx == 1:
            poseName = poseName + "APose_ASFalse_num"
        elif poseIdx == 2:
            poseName = poseName + "TPose_ASFalse_num"
        elif poseIdx == 3:
            poseName = poseName + "EPose_ASFalse_num"

        print("Pose Name: " + poseName)
        print("Joint Root: [" + self.rootJoint + "]")
        
        try:
            result = cmds.dagPose( self.rootJoint, save=True, selection=False, name=poseName )
            self.rkDefaultPoses[poseIdx] = result
            print(self.rkDefaultPoses[poseIdx])
        except:
            if   poseIdx == 0:
                self.iPoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'iPoseCheckBox')
                self.iPoseCheckBox.setChecked(False)
            elif poseIdx == 1:
                self.aPoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'aPoseCheckBox')
                self.aPoseCheckBox.setChekced(False)
            elif poseIdx == 2:
                self.tPoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'tPoseCheckBox')
                self.tPoseCheckBox.setChecked(False)
            elif poseIdx == 3:
                self.ePoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'ePoseCheckBox')
                self.ePoseCheckBox.setChecked(False)
            print("Unable to create dagPose: " + poseName)
            #pcb = self.findChild(QtWidgets.QPushButton, poseCB)
            #pcb.setChecked(False)

                
    def grabDefaultRKPoses(self):
        selNodes = cmds.ls(sl=True)
        if len(selNodes) > 0:
            
            if   cmds.nodeType(selNodes[0]) == "transform":
                try:
                    x3dType = cmds.getAttr(selNodes[0] + ".x3dGroupType")
                    if x3dType == "HAnimHumanoid":
                        hRels = cmds.listRelatives(c=True, type="joint")
                        if hRels is not None:
                            self.rootJoint = hRels[0]
                except:
                    pass
            elif cmds.nodeType(selNodes[0]) == "joint":
                self.rootJoint = self.getRoot(selNodes[0])

            if self.rootJoint != "":
                connectedPoses = cmds.listConnections(self.rootJoint, p=False, t='dagPose')
                if connectedPoses is not None:
                    for cPose in connectedPoses:
                        pSplit = cPose.split('_')
                        if pSplit[0] == "rk":
                            if   pSplit[1] == "IPose":
                                if self.rkDefaultPoses[0] != "":
                                    cmds.delete(cPose)
                                else:
                                    self.rkDefaultPoses[0] = cPose
                                
                            elif pSplit[1] == "APose":
                                if self.rkDefaultPoses[1] != "":
                                    cmds.delete(cPose)
                                else:
                                    self.rkDefaultPoses[1] = cPose
                                
                            elif pSplit[1] == "TPose":
                                if self.rkDefaultPoses[2] != "":
                                    cmds.delete(cPose)
                                else:
                                    self.rkDefaultPoses[2] = cPose
                                
                            elif pSplit[1] != "EPose":
                                if self.rkDefaultPoses[3] != "":
                                    cmds.delete(cPose)
                                else:
                                    self.rkDefaultPoses[3] = cPose

                cmds.select(self.rootJoint)


    def getRoot(self, joint):
        currentCharNode = joint
        isSearchingForRoot = True
        
        while isSearchingForRoot == True:
            rels = cmds.listRelatives(currentCharNode, p=True)
            
            if rels is not None:
                rType = cmds.nodeType(rels[0])
                if rType == "joint":
                    currentCharNode = rels[0]
                else:
                    isSearchingForRoot = False
            else:
                isSearchingForRoot = False
                
        return currentCharNode