import sys
import os
from rawkee import RKWeb3D
from rawkee.RKWeb3D import RKAddSwitch, RKAddGroup, RKAddCollision, RKSetAsBillboard, RKAddX3DSound, RKTestIt
from rawkee.RKWeb3D import RKASBackupClipBoard, RKASRestoreClipBoard
from rawkee.RKWeb3D import RKSetAsHAnimHumanoid
from rawkee.RKWeb3D import RKTransferSkinASGS,     RKLoadDefPoseForHAnim,  RKAdvancedSkeleton
from rawkee.RKWeb3D import RKEstimateIPoseForASGS, RKEstimateAPoseForASGS, RKEstimateTPoseForASGS, RKSetASPoseForASGS, RKDefPoseForASGS
from rawkee.RKWeb3D import RKLoadIPoseForASGS,     RKLoadAPoseForASGS,     RKLoadTPoseForASGS
from rawkee.RKWeb3D import RKSaveIPoseForASGS,     RKSaveAPoseForASGS,     RKSaveTPoseForASGS
from rawkee.RKWeb3D import RKX3DAuxLoader
from rawkee.RKSceneEditor import *
from rawkee.RKCharacterEditor import *

# From Early 2000s C++ Registered Node IDs
from rawkee.nodes.x3dTimeSensor import X3DTimeSensor
from rawkee.nodes.x3dSound import X3DSound, X3DSoundDrawOverride

# From 2024 RawKee PE Registered Node IDSs
from rawkee.nodes.x3dHAnimMotion import X3DHAnimMotion
from rawkee.nodes.rkAnimPack import RKAnimPack

import rawkee.nodes.sticker    as stk


#### from rawkee.nodes.X3D_Scene import X3D_Scene, RKPrimeX3DScene
#### from rawkee.nodes.X3D_Transform import X3D_Transform
#### from rawkee.nodes.X3D_Group import X3D_Group
#from rawkee.nodes.x3dViewpointCamera import X3DViewpointCamera
#from rawkee.RKUtils import *#setDefRKOptVars

from maya import cmds as cmds
from maya import mel  as mel

# Import the package required for Maya Plugin functions
import maya.api.OpenMaya as aom
import maya.api.OpenMayaRender as omr
import maya.api.OpenMayaUI as omui

import webbrowser

#http Service
from nodejs import npx

# RawKee Information
global RAWKEE_VENDOR
global RAWKEE_AUTHOR
global RAWKEE_MAJOR
global RAWKEE_MINOR
global RAWKEE_MICRO
global RAWKEE_VERSION
global RAWKEE_TITLE

RAWKEE_VENDOR  = "UND DREAM Lab - https://github.com/und-dream-lab/rawkee/"
RAWKEE_AUTHOR  = "Aaron Bergstrom"
RAWKEE_MAJOR   = "2"
RAWKEE_MINOR   = "0"
RAWKEE_MICRO   = "0"
RAWKEE_VERSION = RAWKEE_MAJOR + "." + RAWKEE_MINOR + "." + RAWKEE_MICRO
RAWKEE_TITLE   = "RawKee X3D Exporter for Maya - Python Version: " + RAWKEE_VERSION

RAWKEE_BASE    = ""
RAWKEE_ICONS   = ""

RKCallBackIDs    = []

# Maya API 2.0 function required for Plugins
def maya_useNewAPI():
    """
	The presence of this function tells Maya that the plugin produces, and
	expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass

def rkUpdateStickers(client_data):
    stk.reveal()
    

def startX_ITE(args):
    public_path = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
    public_path = public_path+"/public"

    npx.call(['http-server', public_path])


# Global RawKee menu systems Object used to add Menus to Maya Main Window
# Cosntructing the RawKee menu system using "maya.cmds" is a more pleasant 
# experience than using MEL 
global rkWeb3D


class RKServer(aom.MPxCommand):
    kPluginCmdName = "rkServer"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKServer()
        
    def doIt(self, args):
        public_path = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
        public_path = public_path+"/public"
        
        tServer = "npx http-server " + public_path

        os.system(tServer)
#        npx.call(['http-server', public_path])


# Creating the MEL Command for the RawKee's Information Command
class RKInfo(aom.MPxCommand):
    kPluginCmdName = "rkInfo"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKInfo()
        
    def doIt(self, args):
        print(RAWKEE_TITLE)


# Creating the MEL Command for showing the Node Sticker Website
class RKShowNodeSticker(aom.MPxCommand):
    kPluginCmdName = "rkShowNodeSticker"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowNodeSticker()
        
    def doIt(self, args):
        webbrowser.open_new("https://github.com/davidlatwe/NodeSticker")


# Creating the MEL Command for showing the RawKee GitHub Website
class RKShowRawKee(aom.MPxCommand):
    kPluginCmdName = "rkShowRawKee"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowRawKee()
        
    def doIt(self, args):
        webbrowser.open_new("https://github.com/und-dream-lab/rawkee/")


# Creating the MEL Command for showing the DREAM Lab Website
class RKShowDreamLab(aom.MPxCommand):
    kPluginCmdName = "rkShowDreamLab"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowDreamLab()
        
    def doIt(self, args):
        webbrowser.open_new("https://dream.crc.und.edu/")


# Creating the MEL Command for showing the Web3D Website
class RKShowWeb3D(aom.MPxCommand):
    kPluginCmdName = "rkShowWeb3D"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowWeb3D()
        
    def doIt(self, args):
        webbrowser.open_new("https://www.web3d.org/")


# Creating the MEL Command for showing the Metaverse Standards Forum Website
class RKShowMSF(aom.MPxCommand):
    kPluginCmdName = "rkShowMSF"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowMSF()
        
    def doIt(self, args):
        webbrowser.open_new("https://metaverse-standards.org/")


# Creating the MEL Command for the RawKee's function to activate import function
class RKX3DImport(aom.MPxCommand):
    kPluginCmdName = "rkX3DImport"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DImport()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateImportFunctions()
        else:
            print("rkWeb3D was None")



# Creating the MEL Command for the RawKee's function to activate export function
class RKX3DExport(aom.MPxCommand):
    kPluginCmdName = "rkX3DExport"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DExport()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateExportFunctions(0)
        else:
            print("rkWeb3D was None")



# Creating the MEL Command for the RawKee's function to activate export function
class RKCASExport(aom.MPxCommand):
    kPluginCmdName = "rkCASExport"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKCASExport()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateExportFunctions(1)
        else:
            print("rkWeb3D was None")



# Creating the MEL Command for the RawKee's function to activate export function
class RKX3DSelExport(aom.MPxCommand):
    kPluginCmdName = "rkX3DSelExport"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DSelExport()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateSelExportFunctions(0)
        else:
            print("rkWeb3D was None")



# Creating the MEL Command for the RawKee's function to activate export function
class RKCASSelExport(aom.MPxCommand):
    kPluginCmdName = "rkCASSelExport"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKCASSelExport()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateSelExportFunctions(1)
        else:
            print("rkWeb3D was None")



# Creating the MEL Command for the RawKee's function to activate import function
class RKX3DImportOp(aom.MPxCommand):
    kPluginCmdName = "rkX3DImportOp"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DImportOp()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateImportOptions()
        else:
            print("rkWeb3D was None")



# Creating the MEL Command for the RawKee's function to activate export function
class RKX3DExportOp(aom.MPxCommand):
    kPluginCmdName = "rkX3DExportOp"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DExportOp()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateExportOptions()
        else:
            print("rkWeb3D was None")



# Creating the MEL Command for the RawKee's function to activate export function
class RKX3DSelExportOp(aom.MPxCommand):
    kPluginCmdName = "rkX3DSelExportOp"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DSelExportOp()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateSelExportOptions()
        else:
            print("rkWeb3D was None")


# Creating the MEL Command for the RawKee's function to activate export function
class RKX3DSetProject(aom.MPxCommand):
    kPluginCmdName = "rkX3DSetProject"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DSetProject()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.setRawKeeProjectDirectory()
        else:
            print("rkWeb3D was None")


# Creating the MEL Command for the RawKee's function to activate export function
class RKCASSetProject(aom.MPxCommand):
    kPluginCmdName = "rkCASSetProject"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKCASSetProject()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.setCastleProjectDirectory()
        else:
            print("rkWeb3D was None")


class RKCASExportOp(aom.MPxCommand):
    kPluginCmdName = "rkCASExportOp"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKCASExportOp()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateCastleExportOptions()
        else:
            print("rkWeb3D was None")


class RKCASSelExportOp(aom.MPxCommand):
    kPluginCmdName = "rkCASSelExportOp"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKCASSelExportOp()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateCastleSelExportOptions()
        else:
            print("rkWeb3D was None")


class RKShowSceneEditor(aom.MPxCommand):
    kPluginCmdName = "rkShowSceneEditor"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowSceneEditor()
        
    def doIt(self, args):
        print("RawKee Scene Editor")
        #cmds.rkPrimeX3DScene()
        
        global rkWeb3D
        if rkWeb3D is not None:
            sceneEditorControlName = RKSceneEditor.scene_editor_control_name()
        
            if cmds.workspaceControl(sceneEditorControlName, exists=True):
                #Must Close before Delete
                cmds.workspaceControl(sceneEditorControlName, e=True, close=True, closeCommand=RKSceneEditor.workplace_close_command())
                cmds.deleteUI(sceneEditorControlName)
            
            rkSEditor = RKSceneEditor()
            rkSEditor.setRKWeb3D(rkWeb3D)
            rkSEditor.show(dockable=True, uiScript=RKSceneEditor.workspace_ui_script())
            rkSEditor.centerNodeEditor()
        else:
            print("RKWeb3D is not set!")
        


class RKShowCharacterEditor(aom.MPxCommand):
    kPluginCmdName = "rkShowCharacterEditor"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowCharacterEditor()
        
    def doIt(self, args):
        print("RawKee X3D - Character Editor")
        #cmds.rkPrimeX3DScene()
        
        global rkWeb3D
        if rkWeb3D is not None:
            characterEditorControlName = RKCharacterEditor.character_editor_control_name()
        
            if cmds.workspaceControl(characterEditorControlName, exists=True):
                #Must Close before Delete
                cmds.workspaceControl(characterEditorControlName, e=True, close=True, closeCommand=RKCharacterEditor.workplace_close_command())
                cmds.deleteUI(characterEditorControlName)
            
            rkCEditor = RKCharacterEditor()
            #rkCEditor.setRKWeb3D(rkWeb3D)
            rkCEditor.show(dockable=True, uiScript=RKCharacterEditor.workspace_ui_script())
        else:
            print("RKWeb3D is not set!")
        


# Initialize the plug-in
def initializePlugin(plugin):

    print("Made possible by the: Alias Research Donation Program\n\n")
    pluginFn = aom.MFnPlugin(plugin, RAWKEE_VENDOR, RAWKEE_VERSION)
 
    # RawKee Utility Functions required to be in MEL format such as functions related to AE Templates.
    mel.eval('source "x3d.mel"')
    try:
        mel.eval('source "AdvancedSkeletonFiles/../AdvancedSkeleton.mel"')
        print("Sourced mel scripts for Advanced Skeleton toolset. Adding Advanced Skeleton functionality to RawKee HAnim Character Export")
    except:
        print("Advanced Skeleton Not Found\nDownload and install Advanced Skeleton to add additional HAnim Character functionality to RawKee.\nhttps://animationstudios.com.au/")
    
    # Source all the X3D Field names for use in Import/Export and the Interaction Editor
    #mel.eval('source "x3d_source_field_tables.mel"')
    
    ##################################
    '''
    REGISTERING Custom X3D Nodes
    '''
    ##################################
    '''
    try:
        
        pluginFn.registerNode(X3D_Scene.TYPE_NAME,         # name of node
                              X3D_Scene.TYPE_ID,           # unique id that identifiesnode
                              X3D_Scene.creator,                 # function/method that returns new instance of class
                              X3D_Scene.initialize)              # function/method that will initialize all attributes of node
        
        pluginFn.registerNode(X3D_Group.TYPE_NAME,           # name of node
                              X3D_Group.TYPE_ID,             # unique id that identifiesnode
                              X3D_Group.creator,             # function/method that returns new instance of class
                              X3D_Group.initialize)          # function/method that will initialize all attributes of node

        pluginFn.registerNode(X3D_Transform.TYPE_NAME,           # name of node
                              X3D_Transform.TYPE_ID,             # unique id that identifiesnode
                              X3D_Transform.creator,             # function/method that returns new instance of class
                              X3D_Transform.initialize)          # function/method that will initialize all attributes of node
    '''
    try:
        pluginFn.registerNode(X3DSound.TYPE_NAME,         # name of node
                              X3DSound.TYPE_ID,           # unique id that identifiesnode
                              X3DSound.creator,                 # function/method that returns new instance of class
                              X3DSound.initialize,              # function/method that will initialize all attributes of node
                              aom.MPxNode.kLocatorNode,         # type of node to be registered
                              X3DSound.DRAW_CLASSIFICATION)     # 
    except:
        aom.MGlobal.displayError("Failed to register node: {0}".format(X3DSound.kPluginNodeName))
                              
    try:
        pluginFn.registerNode(X3DHAnimMotion.TYPE_NAME,         # name of node
                              X3DHAnimMotion.TYPE_ID,           # unique id that identifiesnode
                              X3DHAnimMotion.creator,                 # function/method that returns new instance of class
                              X3DHAnimMotion.initialize,              # function/method that will initialize all attributes of node
                              aom.MPxNode.kLocatorNode)         # type of node to be registered
    except:
        aom.MGlobal.displayError("Failed to register node: {0}".format(X3DHAnimMotion.kPluginNodeName))
                              
    try:
        pluginFn.registerNode(X3DTimeSensor.TYPE_NAME,         # name of node
                              X3DTimeSensor.TYPE_ID,           # unique id that identifiesnode
                              X3DTimeSensor.creator,                 # function/method that returns new instance of class
                              X3DTimeSensor.initialize,              # function/method that will initialize all attributes of node
                              aom.MPxNode.kLocatorNode)         # type of node to be registered
    except:
        aom.MGlobal.displayError("Failed to register node: {0}".format(X3DTimeSensor.kPluginNodeName))
                              
    try:
        pluginFn.registerNode(RKAnimPack.TYPE_NAME,         # name of node
                              RKAnimPack.TYPE_ID,           # unique id that identifiesnode
                              RKAnimPack.creator,                 # function/method that returns new instance of class
                              RKAnimPack.initialize,              # function/method that will initialize all attributes of node
                              aom.MPxNode.kLocatorNode)         # type of node to be registered
    except:
        aom.MGlobal.displayError("Failed to register node: {0}".format(RKAnimPack.kPluginNodeName))
                              
#        pluginFn.registerNode(X3DViewpointCamera.kPluginNodeName, # name of node
#                              X3DViewpointCamera.kPluginNodeId,   # unique id that identifiesnode
#                              X3DViewpointCamera.creator,         # function/method that returns new instance of class
#                              X3DViewpointCamera.initialize,      # function/method that will initialize all attributes of node
#                              aom.MPxNode.kCameraSetNode)         # type of node to be registered
                              
        

    '''
    ##################################
    REGISTERING Custom X3D Node Draw Overrides
    '''
    ##################################
    '''
    try:
        omr.MDrawRegistry.registerDrawOverrideCreator(X3DSound.DRAW_CLASSIFICATION,
                                                      X3DSound.DRAW_REGISTRANT_ID,
                                                      X3DSoundDrawOverride.creator)
    except:
        aom.MGlobal.displayError("Failed to register draw override: {0}".format(X3DSoundDrawOverride.NAME))
    '''    
        
    ##################################
    '''
    REGISTERING Custom RawKee Commands
    '''
    ##################################
    try:
        
        #pluginFn.registerCommand(        RKServer.kPluginCmdName,         RKServer.cmdCreator)
        #pluginFn.registerCommand(          RKAddX3DSound.kPluginCmdName,     RKAddX3DSound.cmdCreator)
        pluginFn.registerCommand(RKASBackupClipBoard.kPluginCmdName,   RKASBackupClipBoard.cmdCreator)
        pluginFn.registerCommand(RKASRestoreClipBoard.kPluginCmdName, RKASRestoreClipBoard.cmdCreator)
        
        pluginFn.registerCommand(RKShowNodeSticker.kPluginCmdName,  RKShowNodeSticker.cmdCreator)
        pluginFn.registerCommand(     RKShowRawKee.kPluginCmdName,       RKShowRawKee.cmdCreator)
        pluginFn.registerCommand(   RKShowDreamLab.kPluginCmdName,     RKShowDreamLab.cmdCreator)
        pluginFn.registerCommand(      RKShowWeb3D.kPluginCmdName,        RKShowWeb3D.cmdCreator)
        pluginFn.registerCommand(        RKShowMSF.kPluginCmdName,        RKShowMSF.cmdCreator)
        
        pluginFn.registerCommand( RKSetAsHAnimHumanoid.kPluginCmdName,  RKSetAsHAnimHumanoid.cmdCreator)

        pluginFn.registerCommand( RKSetAsBillboard.kPluginCmdName,  RKSetAsBillboard.cmdCreator)
        pluginFn.registerCommand(   RKAddCollision.kPluginCmdName,    RKAddCollision.cmdCreator)
        pluginFn.registerCommand(       RKAddGroup.kPluginCmdName,        RKAddGroup.cmdCreator)
        pluginFn.registerCommand(      RKAddSwitch.kPluginCmdName,       RKAddSwitch.cmdCreator)
        pluginFn.registerCommand(           RKInfo.kPluginCmdName,            RKInfo.cmdCreator)
        pluginFn.registerCommand(    RKX3DExportOp.kPluginCmdName,     RKX3DExportOp.cmdCreator)
        pluginFn.registerCommand(      RKX3DExport.kPluginCmdName,       RKX3DExport.cmdCreator)
        pluginFn.registerCommand( RKX3DSelExportOp.kPluginCmdName,  RKX3DSelExportOp.cmdCreator)
        pluginFn.registerCommand(   RKX3DSelExport.kPluginCmdName,    RKX3DSelExport.cmdCreator)
        pluginFn.registerCommand(    RKX3DImportOp.kPluginCmdName,     RKX3DImportOp.cmdCreator)
        pluginFn.registerCommand(      RKX3DImport.kPluginCmdName,       RKX3DImport.cmdCreator)
        pluginFn.registerCommand(         RKTestIt.kPluginCmdName,          RKTestIt.cmdCreator)
        
        pluginFn.registerCommand(    RKAdvancedSkeleton.kPluginCmdName,     RKAdvancedSkeleton.cmdCreator)
        pluginFn.registerCommand(RKEstimateIPoseForASGS.kPluginCmdName, RKEstimateIPoseForASGS.cmdCreator)
        pluginFn.registerCommand(RKEstimateAPoseForASGS.kPluginCmdName, RKEstimateAPoseForASGS.cmdCreator)
        pluginFn.registerCommand(RKEstimateTPoseForASGS.kPluginCmdName, RKEstimateTPoseForASGS.cmdCreator)
        pluginFn.registerCommand(    RKSetASPoseForASGS.kPluginCmdName,     RKSetASPoseForASGS.cmdCreator)
        pluginFn.registerCommand(      RKDefPoseForASGS.kPluginCmdName,       RKDefPoseForASGS.cmdCreator)
        pluginFn.registerCommand(    RKTransferSkinASGS.kPluginCmdName,     RKTransferSkinASGS.cmdCreator)
        pluginFn.registerCommand( RKLoadDefPoseForHAnim.kPluginCmdName,  RKLoadDefPoseForHAnim.cmdCreator)
        pluginFn.registerCommand(    RKLoadIPoseForASGS.kPluginCmdName,     RKLoadIPoseForASGS.cmdCreator)
        pluginFn.registerCommand(    RKLoadAPoseForASGS.kPluginCmdName,     RKLoadAPoseForASGS.cmdCreator)
        pluginFn.registerCommand(    RKLoadTPoseForASGS.kPluginCmdName,     RKLoadTPoseForASGS.cmdCreator)
        pluginFn.registerCommand(    RKSaveIPoseForASGS.kPluginCmdName,     RKSaveIPoseForASGS.cmdCreator)
        pluginFn.registerCommand(    RKSaveAPoseForASGS.kPluginCmdName,     RKSaveAPoseForASGS.cmdCreator)
        pluginFn.registerCommand(    RKSaveTPoseForASGS.kPluginCmdName,     RKSaveTPoseForASGS.cmdCreator)
        
        pluginFn.registerCommand(RKShowCharacterEditor.kPluginCmdName, RKShowCharacterEditor.cmdCreator)
        pluginFn.registerCommand(    RKShowSceneEditor.kPluginCmdName,     RKShowSceneEditor.cmdCreator)
        
        pluginFn.registerCommand(  RKX3DSetProject.kPluginCmdName,   RKX3DSetProject.cmdCreator)
        pluginFn.registerCommand(  RKCASSetProject.kPluginCmdName,   RKCASSetProject.cmdCreator)
        pluginFn.registerCommand(    RKCASExportOp.kPluginCmdName,     RKCASExportOp.cmdCreator)
        pluginFn.registerCommand( RKCASSelExportOp.kPluginCmdName,  RKCASSelExportOp.cmdCreator)
        pluginFn.registerCommand(      RKCASExport.kPluginCmdName,       RKCASExport.cmdCreator)
        pluginFn.registerCommand(   RKCASSelExport.kPluginCmdName,    RKCASSelExport.cmdCreator)
        
        pluginFn.registerCommand(   RKX3DAuxLoader.kPluginCmdName,    RKX3DAuxLoader.cmdCreator)
    except:
        sys.stderr.write("Failed to register a plugin command.\n")

    # Function that sets the Maya global varaibles required by RawKee - Found in 'rawkee.RKUtils'
    mel.eval('setDefRKOptVars()')

    # Create Menu System for RawKee 'rawkee.RKMenus'
    global rkWeb3D
    rkWeb3D = RKWeb3D.RKWeb3D()
    rkWeb3D.pVersion = RAWKEE_TITLE
    
    RAWKEE_BASE = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
    rkWeb3D.setMyStyleSheet(RAWKEE_BASE)
    
    ################################################################################
    # Load RawKee Icon Library #####################################################
    osDiv = ":"
    if os.name == "nt":
        osDiv = ";"
    RAWKEE_ICONS = RAWKEE_BASE + "/nodes/icons" + osDiv
    
    iconpath = mel.eval('getenv XBMLANGPATH')
    
    ipIdx = iconpath.find(RAWKEE_ICONS)
    if ipIdx < 0:
        newpath = RAWKEE_ICONS
        newpath = newpath + iconpath
        cmdEval = 'putenv "XBMLANGPATH" '
        cmdEval = cmdEval + '"' + newpath + '"'
        mel.eval(cmdEval)
    
    ################################################################################
    # Set Callback Functions #######################################################
    ################################################################################
    
    ################################################################################
    # Function to re-apply stickers to nodes shown in the Outliner. rkUpdateStickers
    # is called every time the scene needs an update. This causes the nodes with
    # Node Stickers to be updated in the outliner.
    RKCallBackIDs.append(aom.MSceneMessage.addCallback(aom.MSceneMessage.kSceneUpdate, rkUpdateStickers))


    

# Uninitialize the plug-in
def uninitializePlugin(plugin):
    pluginFn = aom.MFnPlugin(plugin)
    
    
    ##################################
    '''
    DEREGISTERING Custom RawKee Commands
    '''
    ##################################
    try:
        pluginFn.deregisterCommand(   RKX3DAuxLoader.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKX3DAuxLoader failed to deregister")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(   RKCASSelExport.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKCASSelExport - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKCASExport.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKCASExport - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand( RKCASSelExportOp.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKCASSelExportOpt - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKCASExportOp.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKCASExportOp - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(  RKCASSetProject.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKCASSetProject - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(  RKX3DSetProject.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKX3DSetProject - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKShowSceneEditor.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowSceneEditor - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(RKShowCharacterEditor.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowCharacterEditor - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

       
    try:
        pluginFn.deregisterCommand(    RKSaveTPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKSaveTPoseForASGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKSaveAPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKSaveAPoseForASGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKSaveIPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKSaveIPoseForASGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKLoadTPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKLoadTPoseForASGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKLoadAPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKLoadAPoseForASGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKLoadIPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKLoadIPoseForASGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand( RKLoadDefPoseForHAnim.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKLoadDefPoseForHAnim - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKTransferSkinASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKTransferSkinASGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKDefPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKDefPoseForaSGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKSetASPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKSetASPoseForaSGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(RKEstimateTPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKEstimatetPoseForaSGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(RKEstimateAPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKEstimateaPoseForaSGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(RKEstimateIPoseForASGS.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKEstimateIPoseForaSGS - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKAdvancedSkeleton.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKAdvancedSkeleton - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(         RKTestIt.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKTestIt - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKX3DImport.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKX3DImport - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKX3DImportOp.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKX3DImportOp - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(   RKX3DSelExport.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKX3DSelExport - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand( RKX3DSelExportOp.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKX3DSelExportOp - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKX3DExport.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKX3DExport - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKX3DExportOp.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKX3DExportOp - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(           RKInfo.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKInfo - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKAddSwitch.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKAddSwitch - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(       RKAddGroup.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKAddGroup - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(   RKAddCollision.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKAddCollision - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand( RKSetAsBillboard.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKSetAsBillboard - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand( RKSetAsHAnimHumanoid.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKSetAsHAnimHumanoid - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(        RKShowMSF.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowMSF - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKShowWeb3D.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowWeb3D - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(   RKShowDreamLab.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowDreamLab - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(     RKShowRawKee.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowRawKee - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(RKShowNodeSticker.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowNodeSticker - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(RKASRestoreClipBoard.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKASRestoreClipBoard - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand( RKASBackupClipBoard.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKASBackupClipBoard - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

        #pluginFn.deregisterCommand(    RKAddX3DSound.kPluginCmdName)
        #pluginFn.deregisterCommand(         RKServer.kPluginCmdName)
        

    ##################################
    '''
    DEREGISTERING Custom X3D Node Draw Overrides
    '''
    ##################################
    '''
    try:
        omr.MDrawRegistry.deregisterDrawOverrideCreator(X3DSound.DRAW_CLASSIFICATION, X3DSound.DRAW_REGISTRANT_ID)
    except:
        aom.MGlobal.displayError("Failed to deregister draw override: {0}".format(X3DSoundDrawOverride.NAME))
    '''    
        
    ##################################
    '''
    DEREGISTERING Custom X3D Nodes
    '''
    ##################################

    try:
        pluginFn.deregisterNode(    RKAnimPack.TYPE_ID)
        pluginFn.deregisterNode(      X3DSound.TYPE_ID)
        pluginFn.deregisterNode(X3DHAnimMotion.TYPE_ID)
        pluginFn.deregisterNode( X3DTimeSensor.TYPE_ID)
    except:
        aom.MGlobal.displayError("Failed to deregister a node.")#{0}".format(X3DSound.TYPE_NAME))

    ##################################################################
    # Removal of Remote Menu Sysem for RawKee from Maya Main Window
    ##################################################################
    
    # First we must remove the refernce to RKWeb3D object in the RKSceneEditor panel
    # otherwise the object's __del__ function won't by code below of...
    # 'del rkWeb3D'
    sceneEditorControlName = RKSceneEditor.scene_editor_control_name()

    if cmds.workspaceControl(sceneEditorControlName, exists=True):
        #Must Close before Delete
        cmds.workspaceControl(sceneEditorControlName, e=True, close=True, closeCommand=RKSceneEditor.workplace_close_command())
        cmds.deleteUI(sceneEditorControlName)
    
    characterEditorControlName = RKCharacterEditor.character_editor_control_name()

    if cmds.workspaceControl(characterEditorControlName, exists=True):
        #Must Close before Delete
        cmds.workspaceControl(characterEditorControlName, e=True, close=True, closeCommand=RKCharacterEditor.workplace_close_command())
        cmds.deleteUI(characterEditorControlName)
    
    # Delete the RKWeb3D object that is the menu system and 
    # export function system for the MayaMainWindow
    global rkWeb3D
    del rkWeb3D

    #################################################################################
    # Unload RawKee Icon Library ####################################################
    iconpath = mel.eval('getenv XBMLANGPATH')
    RAWKEE_BASE = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
    
    osDiv = ":"
    if os.name == "nt":
        osDiv = ";"
    RAWKEE_ICONS = RAWKEE_BASE + "/nodes/icons" + osDiv

    ipIdx = iconpath.find(RAWKEE_ICONS)
    if ipIdx > -1:
        newpath = iconpath.replace(RAWKEE_ICONS, "")
        cmdEval = 'putenv "XBMLANGPATH" '
        cmdEval = cmdEval + '"' + newpath + '"'
        mel.eval(cmdEval)

    ################################################################################
    # Remove Callback Functions ####################################################
    ################################################################################
    for cbID in RKCallBackIDs:
        aom.MSceneMessage.removeCallback(cbID)


#Only for code development
if __name__ == "__main__":
    cmds.file(new=True, force=True)
    plugin_name = "RawKee_Python_X3D.py"
    cmds.evalDeferred('if cmds.pluginInfo("{0}", q=True, loaded=True): cmds.unloadPlugin("{0}")'.format(plugin_name))
    cmds.evalDeferred('if not cmds.pluginInfo("{0}", q=True, loaded=True): cmds.loadPlugin("{0}")'.format(plugin_name))
    cmds.evalDeferred('cmds.createNode("x3dSound")')
