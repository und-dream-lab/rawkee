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
import os

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

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class RKHAnimHumanoidSetupEditor(MayaQWidgetDockableMixin, QWidget):
    
    OBJECT_NAME = "RKHAnimHumanoidSetupEditor"
    
    @classmethod
    def hanim_humanoid_setup_editor_control_name(cls):
        return "{0}WorkspaceControl".format(cls.OBJECT_NAME)
        
    @classmethod
    def workspace_ui_script(cls):
        return "from rawkee.RKHAnimHumanoidSetupEditor import RKHAnimHumanoidSetupEditor\nrkHHSEWidget = RKHAnimHumanoidSetupEditor()"
        
    @classmethod
    def workplace_close_command(cls):
        return "self.cleanUpOnEditorClose()"

    
    def __init__(self):
        super().__init__()
        
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("RawKee HAnimHumanoid Setup")
        self.setMinimumSize(300,140)

        self.add_to_hanim_humanoid_setup_editor_workspace_control()

        self.uiPaths = os.path.abspath(__file__)
        self.uiPaths = os.path.dirname(self.uiPaths)
        self.uiPaths += "/auxilary/RKHAnimHumanoidSetupPanel.ui"

        loader = QtUiTools.QUiLoader()
        #loader.registerCustomWidget(RKDagPoseComboBox)
        
        hhseGUIFile = QtCore.QFile(self.uiPaths)
        hhseGUIFile.open(QtCore.QFile.ReadOnly)
        self.hhsePanel = loader.load(hhseGUIFile)

        ######################################################
        # Top Level Layout                                   #
        main_layout = QtWidgets.QHBoxLayout(self)  
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.hhsePanel)
        

    def cleanUpOnEditorClose(self):
        print("Cleaned")


    def add_to_hanim_humanoid_setup_editor_workspace_control(self):
        hanim_humanoid_setup_editor_control_name = omui.MQtUtil.findControl(self.hanim_humanoid_setup_editor_control_name())
        if hanim_humanoid_setup_editor_control_name:
            hanim_humanoid_setup_editor_control_name_ptr = int(hanim_humanoid_setup_editor_control_name)
            hanim_humanoid_setup_editor_widget_ptr = int(getCppPointer(self)[0])
            
            omui.MQtUtil.addWidgetToMayaLayout(hanim_humanoid_setup_editor_widget_ptr, hanim_humanoid_setup_editor_workspace_control_ptr)
