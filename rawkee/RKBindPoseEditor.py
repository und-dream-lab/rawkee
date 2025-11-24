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

    def showPopup(self):
        
        self.clear()
        
        poses = cmds.ls(type='dagPose')
        
        if poses is not None:
            rkPoses = []
            otPoses = []
            
            for pose in poses:
                if pose == "rkIPose" or pose == "rkAPose" or pose == "rkTPose" or pose == "rkEPose":
                    rkPoses.append(pose)
                else:
                    otPoses.append(pose)
            
            poses = rkPoses
            for pose in otPoses:
                poses.append(pose)
        
            self.addItems(poses)        
        
        # 3. Call the original implementation to finally display the list to the user
        super().showPopup()


class RKBindPoseEditor(MayaQWidgetDockableMixin, QWidget):
    
    OBJECT_NAME = "RKBindPoseEditor"
    
    @classmethod
    def bindpose_editor_control_name(cls):
        return "{0}WorkspaceControl".format(cls.OBJECT_NAME)
        
    @classmethod
    def workspace_ui_script(cls):
        return "from rawkee.RKBindPoseEditor import RKBindPoseEditor\nrkSEWidget = RKBindPoseEditor()"
        
    @classmethod
    def workplace_close_command(cls):
        return "self.cleanUpOnEditorClose()"

    
    def __init__(self):
        super().__init__()
        
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("RawKee BindPose Editor")
        self.setMinimumSize(300,300)

        self.add_to_bindpose_editor_workspace_control()

        self.uiPaths = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
        self.uiPaths += "/auxilary/"
        self.bpePath = self.uiPaths + "RKBindPoseEditorPanel.ui"
        
        loader = QtUiTools.QUiLoader()
        loader.registerCustomWidget(RKDagPoseComboBox)
        
        bpeGUIFile = QtCore.QFile(self.bpePath)
        bpeGUIFile.open(QtCore.QFile.ReadOnly)
        self.bpePanel = loader.load(bpeGUIFile)
        
        ######################################################
        # Top Level Layout                                   #
        main_layout = QtWidgets.QHBoxLayout(self)            #
        main_layout.addWidget(self.bpePanel)
        
        ######################################################
        # Set ComboBox and Load Button for a Bind Poses      #
        self.bpToLoad = "List of Bind Poses"
        self.bpComboBox = self.findChild(RKDagPoseComboBox, 'poseComboBox')
        self.bpComboBox.currentTextChanged.connect(self.setCurrentSelection)

        self.loadPoseButton = self.findChild(QtWidgets.QPushButton, 'loadPoseButton')
        self.loadPoseButton.clicked.connect(self.restoreSelectedBindPose)
        
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
        iVal = False
        if cmds.objExists("rkIPose") == True:
            iVal = True
        self.iPoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'iPoseCheckBox')
        self.iPoseCheckBox.setChecked(iVal)
        self.iPoseCheckBox.stateChanged.connect(self.rawKeeIPoseStatusChange)
        
        aVal = False
        if cmds.objExists("rkAPose") == True:
            aVal = True
        self.aPoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'aPoseCheckBox')
        self.aPoseCheckBox.setChecked(aVal)
        self.aPoseCheckBox.stateChanged.connect(self.rawKeeAPoseStatusChange)
        
        tVal = False
        if cmds.objExists("rkTPose") == True:
            tVal = True
        self.tPoseCheckBox = self.findChild(QtWidgets.QCheckBox, 'tPoseCheckBox')
        self.tPoseCheckBox.setChecked(tVal)
        self.tPoseCheckBox.stateChanged.connect(self.rawKeeTPoseStatusChange)
        
        eVal = False
        if cmds.objExists("rkEPose") == True:
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
        if self.bpToLoad != "List of Bind Poses":
            if cmds.objExists(self.bpToLoad) == True:
                cmds.dagPose(self.bpToLoad, restore=True )

        
    def restoreRawKeeIPose(self):
        if cmds.objExists("rkIPose") == True:
            cmds.dagPose( "rkIPose", restore=True )

        
    def restoreRawKeeAPose(self):
        if cmds.objExists("rkAPose") == True:
            cmds.dagPose( "rkAPose", restore=True )
        
        
    def restoreRawKeeTPose(self):
        if cmds.objExists("rkTPose") == True:
            cmds.dagPose( "rkTPose", restore=True )
        
        
    def restoreRawKeeEPose(self):
        if cmds.objExists("rkEPose") == True:
            cmds.dagPose( "rkEPose", restore=True )


    ################################################
    def rawKeeIPoseStatusChange(self, state):
        if cmds.objExists("rkIPose") == True:
            cmds.delete("rkIPose")
            
        if state == Qt.CheckState.Checked.value:
            self.createNodeRKDagPose("rkIPose", "iPoseCheckBox")
            

    def rawKeeAPoseStatusChange(self, state):
        if cmds.objExists("rkAPose") == True:
            cmds.delete("rkAPose")
            
        if state == Qt.CheckState.Checked.value:
            self.createNodeRKDagPose("rkAPose", "aPoseCheckBox")
            

    def rawKeeTPoseStatusChange(self, state):
        if cmds.objExists("rkTPose") == True:
            cmds.delete("rkTPose")
            
        if state == Qt.CheckState.Checked.value:
            self.createNodeRKDagPose("rkTPose", "tPoseCheckBox")
            

    def rawKeeEPoseStatusChange(self, state):
        if cmds.objExists("rkEPose") == True:
            cmds.delete("rkEPose")
            
        if state == Qt.CheckState.Checked.value:
            self.createNodeRKDagPose("rkEPose", "ePoseCheckBox")
            

    def createNodeRKDagPose(self, poseName, poseCB):
        selNodes = cmds.ls(selection=True, dag=True)
        if selNodes is not None:
            try:
                cmds.dagPose( selNodes[0], save=True, selection=False, name=poseName )
            except:
                print("Unable to create dagPose: " + poseName)
                pcb = self.findChild(QtWidgets.QPushButton, poseCB)
                pcb.setChecked(False)
