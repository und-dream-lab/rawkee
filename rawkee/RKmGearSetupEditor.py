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

#To get local file path for html file
#from rawkee import RKWeb3D

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class RKmGearSetupEditor(MayaQWidgetDockableMixin, QWidget):
    
    OBJECT_NAME = "RKmGearSetupEditor"
    
    @classmethod
    def mgear_setup_editor_control_name(cls):
        return "{0}WorkspaceControl".format(cls.OBJECT_NAME)
        
    @classmethod
    def workspace_ui_script(cls):
        return "from rawkee.RKmGearSetupEditor import RKmGearSetupEditor\nrkMGSEWidget = RKmGearSetupEditor()"
        
    @classmethod
    def workplace_close_command(cls):
        return "self.cleanUpOnEditorClose()"

    
    def __init__(self):
        super().__init__()
        
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("RawKee mGear Setup Editor")
        self.setMinimumSize(400,600)

        self.add_to_mgear_setup_editor_workspace_control()
        
        self.rootJoint = ""
        self.rkRootJoint = ""

        #self.uiPaths = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
        
        self.uiPaths = os.path.abspath(__file__)
        self.uiPaths = os.path.dirname(self.uiPaths)
        self.uiPaths += "/auxilary/RKmGearSetupEditor.ui"

        loader = QtUiTools.QUiLoader()
        #loader.registerCustomWidget(RKDagPoseComboBox)
        
        mgseGUIFile = QtCore.QFile(self.uiPaths)
        mgseGUIFile.open(QtCore.QFile.ReadOnly)
        self.mgsePanel = loader.load(mgseGUIFile)

        ######################################################
        # Top Level Layout                                   #
        main_layout = QtWidgets.QHBoxLayout(self)  
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.mgsePanel)
        
        self.loadMGearSkelButton = self.findChild(QtWidgets.QPushButton, 'loadMGearSkelButton')
        self.loadMGearSkelButton.clicked.connect(self.loadMGearSkeleton)
        
        self.createRKSkelButton = self.findChild( QtWidgets.QPushButton, 'createRKSkelButton' )
        self.createRKSkelButton.clicked.connect(self.createRawKeeSkeleton)
        
        self.transferMeshButton = self.findChild( QtWidgets.QPushButton, 'transferMeshButton' )
        #self.transferMeshButton.clicked.connect(self.transferMGearMesh)
        self.transferMeshButton.clicked.connect(lambda: self.createRawKeeCharacterFromMGear(3))
        

    def cleanUpOnEditorClose(self):
        print("Cleaned")


    def add_to_mgear_setup_editor_workspace_control(self):
        mgear_setup_editor_control_name = omui.MQtUtil.findControl(self.mgear_setup_editor_control_name())
        if mgear_setup_editor_control_name:
            mgear_setup_editor_control_name_ptr = int(mgear_setup_editor_control_name)
            mgear_setup_editor_widget_ptr = int(getCppPointer(self)[0])
            
            omui.MQtUtil.addWidgetToMayaLayout(mgear_setup_editor_widget_ptr, mgear_setup_editor_workspace_control_ptr)


    def createRawKeeSkeleton(self):
        if self.rootJoint == "":
            print("Please load an mGear root joint")
            return
            
        self.cExportTypeComboBox = self.findChild(QtWidgets.QComboBox, 'cExportTypeComboBox')
        self.loaComboBox         = self.findChild(QtWidgets.QComboBox, 'loaComboBox'        )
        
        eType = self.cExportTypeComboBox.currentIndex()
        print("EType: " + str(eType))
        
        if   eType == 0:
            mayaNodeName = cmds.createNode('transform')
            cmds.addAttr(mayaNodeName, longName='x3dGroupType', dataType='string', keyable=False)
            cmds.setAttr(mayaNodeName + '.x3dGroupType', "HAnimHumanoid", type='string', lock=True)

            defLOA = self.loaComboBox.currentIndex()
            cmds.addAttr(mayaNodeName, longName='levelOfArticulation', shortName='LOA', attributeType='long', keyable=False, defaultValue=-1, minValue=-1, maxValue=4)
            cmds.setAttr(mayaNodeName + '.LOA', defLOA)

            cmds.addAttr(mayaNodeName, longName="skeletalConfiguration", dataType="string")
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
                
            newSkeleton = cmds.duplicate(self.rootJoint, rc=True)

            self.rkRootJoint = newSkeleton[0]
            cmds.makeIdentity(self.rkRootJoint, apply=True, t=True, r=True, s=True, jo=True)
            cmds.parent(self.rkRootJoint, mayaNodeName)
            self.linkRKandMGearSkeletonJoints(self.rootJoint, self.rkRootJoint)
            
        elif eType == 1:
            mayaNodeName = cmds.createNode('transform')
            cmds.addAttr(mayaNodeName, longName='x3dGroupType', dataType='string', keyable=False)
            cmds.setAttr(mayaNodeName + '.x3dGroupType', "HAnimHumanoid", type='string', lock=True)

            defLOA = self.loaComboBox.currentIndex()
            cmds.addAttr(mayaNodeName, longName='levelOfArticulation', shortName='LOA', attributeType='long', keyable=False, defaultValue=-1, minValue=-1, maxValue=4)
            cmds.setAttr(mayaNodeName + '.LOA', defLOA)

            cmds.addAttr(mayaNodeName, longName="skeletalConfiguration", dataType="string")
            cmds.setAttr(mayaNodeName + ".skeletalConfiguration", "RAWKEE", type="string")

            # This uses the 'sticker' script to update the Maya node's image in the Outliner. 
            # This just gives it a visual queue to the content author that this Maya 'transform'
            # node is not a typical transform node and will be exported as an HAnimNode.
            try:
                stk.put(mayaNodeName, "x3dHAnimHumanoid.png")
            except Exception as e:
                print(f"Exception Type: {type(e).__name__}")
                print(f"Exception Message: {e}")                            
                print("Oops... Node Sticker Didn't work.")
                
            newSkeleton = cmds.duplicate(self.rootJoint, rc=True)

            self.rkRootJoint = newSkeleton[0]
            cmds.makeIdentity(self.rkRootJoint, apply=True, t=True, r=True, s=True, jo=True)
            cmds.parent(self.rkRootJoint, mayaNodeName)
            self.linkRKandMGearSkeletonJoints(self.rootJoint, self.rkRootJoint)
            
        else:
            newSkeleton = cmds.duplicate(self.rootJoint, rc=True)
            self.rkRootJoint = newSkeleton[0]
            cmds.parent(self.rkRootJoint, world=True)
            self.linkRKandMGearSkeletonJoints(self.rootJoint, self.rkRootJoint)


    def linkRKandMGearSkeletonJoints(self, tJoint, cJoint, jMatches):
        cmds.parentConstraint(tJoint, cJoint, maintainOffset=True)
        jMatches[tJoint] = cJoint
        
        trJoints = cmds.listRelatives(tJoint, c=True, type="joint")
        crJoints = cmds.listRelatives(cJoint, c=True, type="joint")
        
        if trJoints:
            jLen = len(trJoints)
            
            for i in range(jLen):
                self.linkRKandMGearSkeletonJoints(trJoints[i], crJoints[i], jMatches)

    def loadMGearSkeleton(self):
        selected = cmds.ls(selection=True)
        rootJoint = ""
        
        if selected:
            if len(selected) > 0:
                nType = cmds.nodeType(selected[0])
                if nType == "joint":
                    rootJoint = selected[0]
                else:
                    print("Object Selected is Not a Joint")
                    return
        else:
            print("No Objects Selected")
            return

        self.mGearRootName = self.findChild(QtWidgets.QLineEdit, 'mGearRootName')
        self.rootJoint = rootJoint
        self.mGearRootName.setText(self.rootJoint)
        
    def transferMGearMesh(self):
        skinnedMeshes = {}
        usedMeshes    = []
        newMeshes     = []
        selected      = cmds.ls(sl=True)
        
        if selected:
            for item in selected:
                meshes = cmds.listRelatives(ad=True, type="mesh")
                if meshes:
                    for mNode in meshes:
                        hasFound = False
                        hNodes = cmds.listHistory(mNode)
                        if len(hNodes) > 0:
                            for hNode in hNodes:
                                if cmds.nodeType(hNode) == "skinCluster":
                                    hasFound = True
                        if hasFound == True:
                            skinnedMeshes[mNode] = True

        for key in skinnedMeshes:
            skClusters = cmds.ls(cmds.listHistory(key), type='skinCluster')
            
        #for key in skinnedMeshes:
        #    p = cmds.listRelatives(key, p=True)
        #    usedMeshes.append(p[0])
            
        #newMeshes = cmds.duplicate(usedMeshes)

    
    def createRawKeeCharacterFromMGear(self, cType: int = 3):
        selected    = cmds.ls(sl=True)
        rootJoint   = ""
        rkRootJoint = ""
        skinMeshes  = {}
        jMatches    = {}
        
        print(f"DEBUG: cType received as: {cType}")
        
        if selected:
            if len(selected) > 1:
                if cmds.nodeType(selected[0]) == "joint":
                    rootJoint = selected[0]
                    meshes = cmds.listRelatives(selected[1], ad=True, type="mesh")
                    if meshes:
                        for mNode in meshes:
                            hNodes = cmds.listHistory(mNode)
                            if hNodes:
                                for hNode in hNodes:
                                    if cmds.nodeType(hNode) == "skinCluster":
                                        skinMeshes[mNode] = hNode
                                        break
                else:
                    print("First object selected must be a joint")
                    return
            else:
                print("Two objects must be selected")
                return
        else:
            print("Please select a joint and a DAG object with at least one mesh descendant")
            return
            
        if len(skinMeshes) == 0:
            print("No skinned meshes were found")
            return
        else:
            if cType == 0:
                mayaNodeName = cmds.createNode('transform')
                cmds.addAttr(mayaNodeName, longName='x3dGroupType', dataType='string', keyable=False)
                cmds.setAttr(mayaNodeName + '.x3dGroupType', "HAnimHumanoid", type='string', lock=True)

                defLOA = -1
                cmds.addAttr(mayaNodeName, longName='levelOfArticulation', shortName='LOA', attributeType='long', keyable=False, defaultValue=-1, minValue=-1, maxValue=4)
                cmds.setAttr(mayaNodeName + '.LOA', defLOA)

                cmds.addAttr(mayaNodeName, longName="skeletalConfiguration", dataType="string")
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
                    
                newSkeleton = cmds.duplicate(rootJoint, rc=True)

                rkRootJoint = newSkeleton[0]
                cmds.makeIdentity(rkRootJoint, apply=True, t=True, r=True, s=True, jo=True)
                cmds.parent(rkRootJoint, mayaNodeName)
                print("Ran Type C 0:" + str(cType))
                self.linkRKandMGearSkeletonJoints(rootJoint, rkRootJoint, jMatches)
                
            elif cType == 1:
                mayaNodeName = cmds.createNode('transform')
                cmds.addAttr(mayaNodeName, longName='x3dGroupType', dataType='string', keyable=False)
                cmds.setAttr(mayaNodeName + '.x3dGroupType', "HAnimHumanoid", type='string', lock=True)

                defLOA = -1
                cmds.addAttr(mayaNodeName, longName='levelOfArticulation', shortName='LOA', attributeType='long', keyable=False, defaultValue=-1, minValue=-1, maxValue=4)
                cmds.setAttr(mayaNodeName + '.LOA', defLOA)

                cmds.addAttr(mayaNodeName, longName="skeletalConfiguration", dataType="string")
                cmds.setAttr(mayaNodeName + ".skeletalConfiguration", "RAWKEE", type="string")

                # This uses the 'sticker' script to update the Maya node's image in the Outliner. 
                # This just gives it a visual queue to the content author that this Maya 'transform'
                # node is not a typical transform node and will be exported as an HAnimNode.
                try:
                    stk.put(mayaNodeName, "x3dHAnimHumanoid.png")
                except Exception as e:
                    print(f"Exception Type: {type(e).__name__}")
                    print(f"Exception Message: {e}")                            
                    print("Oops... Node Sticker Didn't work.")
                    
                newSkeleton = cmds.duplicate(rootJoint, rc=True)

                rkRootJoint = newSkeleton[0]
                cmds.makeIdentity(rkRootJoint, apply=True, t=True, r=True, s=True, jo=True)
                cmds.parent(rkRootJoint, mayaNodeName)
                print("Ran Type C 1:" + str(cType))
                self.linkRKandMGearSkeletonJoints(rootJoint, rkRootJoint, jMatches)
                
            elif cType == 2:
                mayaNodeName = cmds.createNode('transform')
                newSkeleton = cmds.duplicate(rootJoint, rc=True)
                rkRootJoint = newSkeleton[0]
                cmds.parent(rkRootJoint, mayaNodeName)
                print("Ran Type C 2:" + str(cType))
                self.linkRKandMGearSkeletonJoints(rootJoint, rkRootJoint, jMatches)

            else:
                newSkeleton = cmds.duplicate(rootJoint, rc=True)
                rkRootJoint = newSkeleton[0]
                cmds.parent(rkRootJoint, world=True)
                print("Ran Type C 3:" + str(cType))
                self.linkRKandMGearSkeletonJoints(rootJoint, rkRootJoint, jMatches)

            if not cmds.objExists(rkRootJoint):
                print("Error: Target root joint not found: " + rkRootJoint)
                return

            export_dir = cmds.workspace(query=True, rootDirectory=True)
            export_dir = export_dir + "copy_weights/"

            # Create the export directory if it doesn't exist
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
                print("Created export directory: " + export_dir)
                
            # Get the complete list of joints from the target skeleton once
            tJoints = cmds.listRelatives(rkRootJoint, allDescendents=True, type='joint')
            if tJoints:
                tJoints.append(rkRootJoint) # Add the root itself
            else:
                tJoints = [rkRootJoint] # Only the root if no children
            
            # --- 2. LOOP THROUGH EACH MESH ---
            for key in skinMeshes:
                sourceMesh = key
                skCluster  = skinMeshes[key]
                oldInfluences = cmds.skinCluster(skCluster, query=True, influence=True)
                newInfluences = []
                for inf in oldInfluences:
                    newInfluences.append(jMatches[inf])

                
                ############################################################
                # --- A. EXPORT WEIGHTS (Maps) ---
                ############################################################
                # The JSON file path is unique for each mesh
                WEIGHT_FILE  = sourceMesh + "_weights.json"
                fullFilePath = os.path.join(export_dir, WEIGHT_FILE)
                
                try:
                    # Correct command: deformerWeights for export
                    cmds.deformerWeights(WEIGHT_FILE, path=export_dir, fm="JSON", ex=True, deformer=skCluster)
                    print("   Exported XML weights to: " + fullFilePath)
                except RuntimeError as e:
                    print(f"   ERROR during XML export for {sourceMesh}: {e}")
                    continue

                ############################################################
                # --- B. UNBIND AND CLEAN UP ---
                ############################################################
                print("2/4. Unbinding skin and deleting history from " + sourceMesh + "...")
                cmds.delete(sourceMesh, constructionHistory=True)

                ###########################################################
                # --- C. BIND TO NEW SKELETON ---
                ###########################################################
                print("3/4. Binding " + sourceMesh + " to the new skeleton (" + rkRootJoint + ")...")
                cmds.skinCluster(newInfluences, sourceMesh, 
                                 toSelectedBones=True, 
                                 bindMethod=0, 
                                 normalizeWeights=1, 
                                 dropoffRate=4.0)
                tSkinCluster = cmds.ls(cmds.listHistory(sourceMesh), type='skinCluster')[0]
                print("   New skinCluster created: " + tSkinCluster)

                ###########################################################
                # --- D. IMPORT SAVED WEIGHTS (XML/Binary) ---
                ###########################################################
                
                # --- D. IMPORT SAVED WEIGHTS (XML/Binary) ---
                cmds.deformerWeights(WEIGHT_FILE, path=export_dir, fm="JSON", im=True, deformer=tSkinCluster, m='index', ig=True)
        
            print("ALL SKIN MESHES PROCESSED SUCCESSFULLY using XML/Binary files.")

