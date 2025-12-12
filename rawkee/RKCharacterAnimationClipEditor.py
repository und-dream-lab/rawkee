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


class RKCharacterAnimationClipEditor(MayaQWidgetDockableMixin, QWidget):
    
    OBJECT_NAME = "RKCharacterAnimationClipEditor"
    
    @classmethod
    def character_animation_clip_editor_control_name(cls):
        return "{0}WorkspaceControl".format(cls.OBJECT_NAME)
        
    @classmethod
    def workspace_ui_script(cls):
        return "from rawkee.RKCharacterAnimationClipEditor import RKCharacterAnimationClipEditor\nrkCACEWidget = RKCharacterAnimationClipEditor()"
        
    @classmethod
    def workplace_close_command(cls):
        return "self.cleanUpOnEditorClose()"

    
    def __init__(self):
        super().__init__()
        
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("RawKee Character Animation Clip Editor")
        self.setMinimumSize(400,600)

        self.add_to_character_animation_clip_editor_workspace_control()

        self.uiPaths = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
        self.uiPaths += "/auxilary/"
        self.cacePath = self.uiPaths + "RKCharacterAnimationClipEditorFrame.ui"

        loader = QtUiTools.QUiLoader()
        #loader.registerCustomWidget(RKDagPoseComboBox)
        
        caceGUIFile = QtCore.QFile(self.cacePath)
        caceGUIFile.open(QtCore.QFile.ReadOnly)
        self.cacePanel = loader.load(caceGUIFile)

        ######################################################
        # Top Level Layout                                   #
        main_layout = QtWidgets.QHBoxLayout(self)  
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.cacePanel)
        

    def cleanUpOnEditorClose(self):
        print("Cleaned")


    def add_to_character_animation_clip_editor_workspace_control(self):
        character_animation_clip_editor_control_name = omui.MQtUtil.findControl(self.character_animation_clip_editor_control_name())
        if character_animation_clip_editor_control_name:
            character_animation_clip_editor_control_name_ptr = int(character_animation_clip_editor_control_name)
            character_animation_clip_editor_widget_ptr = int(getCppPointer(self)[0])
            
            omui.MQtUtil.addWidgetToMayaLayout(character_animation_clip_editor_widget_ptr, character_animation_clip_editor_workspace_control_ptr)
