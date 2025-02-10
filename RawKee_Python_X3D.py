import sys
import os
from rawkee import RKWeb3D
from rawkee.RKWeb3D import RKAddSwitch, RKAddGroup, RKAddCollision, RKSetAsBillboard, RKAddX3DSound, RKTestIt
from rawkee.RKSceneEditor import *
#### from rawkee.nodes.x3dSound import X3DSound, X3DSoundDrawOverride
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

# Maya API 2.0 function required for Plugins
def maya_useNewAPI():
    """
	The presence of this function tells Maya that the plugin produces, and
	expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


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
            rkWeb3D.activateExportFunctions()
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
            rkWeb3D.activateSelExportFunctions()
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
class RKX3DCastleProject(aom.MPxCommand):
    kPluginCmdName = "rkCASSetProject"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DCastleProject()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.setCastleProjectDirectory()
        else:
            print("rkWeb3D was None")


class RKX3DCastleExportOp(aom.MPxCommand):
    kPluginCmdName = "rkCASExportOp"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DCastleExportOp()
        
    def doIt(self, args):
        global rkWeb3D
        
        if rkWeb3D is not None:
            rkWeb3D.activateCastleExportOptions()
        else:
            print("rkWeb3D was None")


class RKX3DCastleSelExportOp(aom.MPxCommand):
    kPluginCmdName = "rkCASSelExportOp"

    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKX3DCastleSelExportOp()
        
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
        else:
            print("RKWeb3D is not set!")
        


# Initialize the plug-in
def initializePlugin(plugin):
    print("Made possible by the: Alias Research Donation Program\n\n")
    pluginFn = aom.MFnPlugin(plugin, RAWKEE_VENDOR, RAWKEE_VERSION)
 
    # RawKee Utility Functions required to be in MEL format such as functions related to AE Templates.
    mel.eval('source "x3d.mel"')
    
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

        pluginFn.registerNode(X3DSound.TYPE_NAME,         # name of node
                              X3DSound.TYPE_ID,           # unique id that identifiesnode
                              X3DSound.creator,                 # function/method that returns new instance of class
                              X3DSound.initialize,              # function/method that will initialize all attributes of node
                              aom.MPxNode.kLocatorNode,         # type of node to be registered
                              X3DSound.DRAW_CLASSIFICATION)     # 
                              
#        pluginFn.registerNode(X3DViewpointCamera.kPluginNodeName, # name of node
#                              X3DViewpointCamera.kPluginNodeId,   # unique id that identifiesnode
#                              X3DViewpointCamera.creator,         # function/method that returns new instance of class
#                              X3DViewpointCamera.initialize,      # function/method that will initialize all attributes of node
#                              aom.MPxNode.kCameraSetNode)         # type of node to be registered
                              
    except:
        aom.MGlobal.displayError("Failed to register node: {0}".format(X3DSound.kPluginNodeName))
    '''
    
    ##################################
    '''
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
        
        #pluginFn.registerCommand(RKWeb3DExporter.kPluginCmdName, RKWeb3DExporter.cmdCreator)
        #pluginFn.registerCommand(        RKServer.kPluginCmdName,         RKServer.cmdCreator)
        #pluginFn.registerCommand(          RKAddX3DSound.kPluginCmdName,     RKAddX3DSound.cmdCreator)
        pluginFn.registerCommand(       RKSetAsBillboard.kPluginCmdName,        RKSetAsBillboard.cmdCreator)
        pluginFn.registerCommand(         RKAddCollision.kPluginCmdName,          RKAddCollision.cmdCreator)
        pluginFn.registerCommand(             RKAddGroup.kPluginCmdName,              RKAddGroup.cmdCreator)
        pluginFn.registerCommand(            RKAddSwitch.kPluginCmdName,             RKAddSwitch.cmdCreator)
        pluginFn.registerCommand(                 RKInfo.kPluginCmdName,                  RKInfo.cmdCreator)
        pluginFn.registerCommand(          RKX3DExportOp.kPluginCmdName,           RKX3DExportOp.cmdCreator)
        pluginFn.registerCommand(            RKX3DExport.kPluginCmdName,             RKX3DExport.cmdCreator)
        pluginFn.registerCommand(       RKX3DSelExportOp.kPluginCmdName,        RKX3DSelExportOp.cmdCreator)
        pluginFn.registerCommand(         RKX3DSelExport.kPluginCmdName,          RKX3DSelExport.cmdCreator)
        pluginFn.registerCommand(          RKX3DImportOp.kPluginCmdName,           RKX3DImportOp.cmdCreator)
        pluginFn.registerCommand(            RKX3DImport.kPluginCmdName,             RKX3DImport.cmdCreator)
        #pluginFn.registerCommand(        RKPrimeX3DScene.kPluginCmdName,        RKPrimeX3DScene.cmdCreator)
        pluginFn.registerCommand(               RKTestIt.kPluginCmdName,                RKTestIt.cmdCreator)
        pluginFn.registerCommand(      RKShowSceneEditor.kPluginCmdName,       RKShowSceneEditor.cmdCreator)
        pluginFn.registerCommand(     RKX3DCastleProject.kPluginCmdName,      RKX3DCastleProject.cmdCreator)
        pluginFn.registerCommand(    RKX3DCastleExportOp.kPluginCmdName,     RKX3DCastleExportOp.cmdCreator)
        pluginFn.registerCommand( RKX3DCastleSelExportOp.kPluginCmdName,  RKX3DCastleSelExportOp.cmdCreator)
        
    except:
        sys.stderr.write("Failed to register a plugin command.\n")

    # Function that sets the Maya global varaibles required by RawKee - Found in 'rawkee.RKUtils'
    mel.eval('setDefRKOptVars()')

    # Create Menu System for RawKee 'rawkee.RKMenus'
    global rkWeb3D
    rkWeb3D = RKWeb3D.RKWeb3D()
    rkWeb3D.pVersion = RAWKEE_TITLE


    

# Uninitialize the plug-in
def uninitializePlugin(plugin):
    pluginFn = aom.MFnPlugin(plugin)
    
    
    ##################################
    '''
    DEREGISTERING Custom RawKee Commands
    '''
    ##################################
    try:
        pluginFn.deregisterCommand(RKX3DCastleSelExportOp.kPluginCmdName)
        pluginFn.deregisterCommand(   RKX3DCastleExportOp.kPluginCmdName)
        pluginFn.deregisterCommand(    RKX3DCastleProject.kPluginCmdName)
        pluginFn.deregisterCommand(     RKShowSceneEditor.kPluginCmdName)
        pluginFn.deregisterCommand(              RKTestIt.kPluginCmdName)
        #pluginFn.deregisterCommand(      RKPrimeX3DScene.kPluginCmdName)
        pluginFn.deregisterCommand(           RKX3DImport.kPluginCmdName)
        pluginFn.deregisterCommand(         RKX3DImportOp.kPluginCmdName)
        pluginFn.deregisterCommand(        RKX3DSelExport.kPluginCmdName)
        pluginFn.deregisterCommand(      RKX3DSelExportOp.kPluginCmdName)
        pluginFn.deregisterCommand(           RKX3DExport.kPluginCmdName)
        pluginFn.deregisterCommand(         RKX3DExportOp.kPluginCmdName)
        pluginFn.deregisterCommand(                RKInfo.kPluginCmdName)
        pluginFn.deregisterCommand(           RKAddSwitch.kPluginCmdName)
        pluginFn.deregisterCommand(            RKAddGroup.kPluginCmdName)
        pluginFn.deregisterCommand(        RKAddCollision.kPluginCmdName)
        pluginFn.deregisterCommand(      RKSetAsBillboard.kPluginCmdName)
        #pluginFn.deregisterCommand(    RKAddX3DSound.kPluginCmdName)
        #pluginFn.deregisterCommand(         RKServer.kPluginCmdName)
        
    except:
        sys.stderr.write("Failed to unregister a plugin command.\n")


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
    '''
    try:
#        pluginFn.deregisterNode(X3DViewpointCamera.kPluginNodeId)
        pluginFn.deregisterNode(           X3DSound.TYPE_ID)
        pluginFn.deregisterNode(      X3D_Transform.TYPE_ID)
        pluginFn.deregisterNode(          X3D_Group.TYPE_ID)
        pluginFn.deregisterNode(          X3D_Scene.TYPE_ID)
    except:
        aom.MGlobal.displayError("Failed to deregister a node.")#{0}".format(X3DSound.TYPE_NAME))
    '''
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
    
    # Delete the RKWeb3D object that is the menu system and 
    # export function system for the MayaMainWindow
    global rkWeb3D
    del rkWeb3D




#Only for code development
if __name__ == "__main__":
    cmds.file(new=True, force=True)
    plugin_name = "RawKee_Python_X3D.py"
    cmds.evalDeferred('if cmds.pluginInfo("{0}", q=True, loaded=True): cmds.unloadPlugin("{0}")'.format(plugin_name))
    cmds.evalDeferred('if not cmds.pluginInfo("{0}", q=True, loaded=True): cmds.loadPlugin("{0}")'.format(plugin_name))
    cmds.evalDeferred('cmds.createNode("x3dSound")')



'''
		aom.MGlobal.executeCommandStringResult("source x3d.mel")
		aom.MGlobal.executeCommandStringResult("source x3dUtilCommands.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_scenegraph_ui_tree.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_exporter_procedures.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_routing_scripts.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_ie_menus.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_switch_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_lod_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_collision_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_navigationinfo_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_worldinfo_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_transform_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_proximitysensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_touchsensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_timesensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_viewpoint_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_orientationinterpolator_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_positioninterpolator_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_script_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_node_creation_procs.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_appearance_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_box_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_color_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_colorrgba_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_cone_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_coordinate_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_cylinder_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_directionallight_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_group_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_imagetexture_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_movietexture_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_indexedfaceset_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_material_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_metadatadouble_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_metadatafloat_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_metadatainteger_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_metadataset_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_metadatastring_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_normal_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_pointlight_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_shape_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_spotlight_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_texturetransform_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_texturecoordinate_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_sphere_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_anchor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_billboard_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_inline_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_colorinterpolator_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_scalarinterpolator_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_coordinateinterpolator_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_normalinterpolator_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_booleansequencer_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_integersequencer_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_booleantrigger_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_booleantoggle_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_integertrigger_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_timetrigger_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_cylindersensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_keysensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_loadsensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_planesensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_spheresensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_stringsensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_visibilitysensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_pixeltexture_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_multitexturecoordinate_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_multitexturetransform_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_multitexture_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_audioclip_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_sound_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_booleanfilter_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_collidableshape_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_hanimhumanoid_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_hanimjoint_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_hanimsite_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_gamepadsensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_rigidbodycollection_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_rigidbody_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_collisioncollection_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_collisionspace_tables.mel")
		aom.MGlobal.executeCommandStringResult("source x3d_collisionsensor_tables.mel")
		aom.MGlobal.executeCommandStringResult("setUpX3DMenus")
'''
