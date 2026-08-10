import sys
import os

from rawkee4maya.maya import RKWeb3D
from rawkee4maya.maya.RKWeb3D import RKAddSwitch, RKAddGroup, RKAddCollision, RKSetAsBillboard, RKAddX3DSound, RKTestIt
from rawkee4maya.maya.RKWeb3D import RKASBackupClipBoard, RKASRestoreClipBoard
from rawkee4maya.maya.RKWeb3D import RKSetAsHAnimHumanoid
from rawkee4maya.maya.RKWeb3D import RKTransferSkinASGS,     RKLoadDefPoseForHAnim,  RKAdvancedSkeleton
from rawkee4maya.maya.RKWeb3D import RKEstimateIPoseForASGS, RKEstimateAPoseForASGS, RKEstimateTPoseForASGS, RKSetASPoseForASGS, RKDefPoseForASGS
from rawkee4maya.maya.RKWeb3D import RKLoadIPoseForASGS,     RKLoadAPoseForASGS,     RKLoadTPoseForASGS
from rawkee4maya.maya.RKWeb3D import RKSaveIPoseForASGS,     RKSaveAPoseForASGS,     RKSaveTPoseForASGS
from rawkee4maya.maya.RKWeb3D import RKX3DAuxLoader
from rawkee.editor.RKSceneEditor import *
from rawkee4maya.maya.RKSceneEditorMaya import RKSceneEditorMaya
from rawkee4maya.maya.RKCharacterEditor import *
from rawkee4maya.maya.RKBindPoseEditor import *
from rawkee4maya.maya.RKCharacterAnimationClipEditor import *
from rawkee4maya.maya.RKHAnimHumanoidSetupEditor import *
from rawkee4maya.maya.RKmGearSetupEditor import *
from rawkee4maya.maya.RKMaterialXEditor import *

# From Early 2000s C++ Registered Node IDs
from rawkee4maya.maya.nodes.x3dSound import X3DSound, X3DSoundDrawOverride

# From 2024 RawKee PE Registered Node IDSs
from rawkee4maya.maya.nodes.rkAnimPack import RKAnimPack

import rawkee4maya.maya.nodes.sticker    as stk


#### from rawkee4maya.nodes.X3D_Scene import X3D_Scene, RKPrimeX3DScene
#### from rawkee4maya.nodes.X3D_Transform import X3D_Transform
#### from rawkee4maya.nodes.X3D_Group import X3D_Group
#from rawkee4maya.nodes.x3dViewpointCamera import X3DViewpointCamera
#from rawkee4maya.RKUtils import *#setDefRKOptVars


from maya import cmds as cmds
from maya import mel  as mel

# Import the package required for Maya Plugin functions
import maya.api.OpenMaya as aom
import maya.api.OpenMayaRender as omr
import maya.api.OpenMayaUI as omui

from maya.app.general import nodeEditorMenus

import webbrowser


##########################################
# For http Service, Not directly supported Any longer
##########################################
# from nodejs import npx
##########################################

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
RAWKEE_MINOR   = "1"
RAWKEE_MICRO   = "0"
RAWKEE_VERSION = RAWKEE_MAJOR + "." + RAWKEE_MINOR + "." + RAWKEE_MICRO
RAWKEE_TITLE   = "RawKee X3D Exporter for Maya - Python Version: " + RAWKEE_VERSION

RAWKEE_BASE    = ""
RAWKEE_ICONS   = ""

RKCallBackIDs  = []
global RKMarkingMenus

# Maya API 2.0 function required for Plugins
def maya_useNewAPI():
    """
	The presence of this function tells Maya that the plugin produces, and
	expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass

def rkUpdateStickers(client_data):
    stk.reveal()


##################################################
# Initialize all required MaterialX functionality.
##################################################
def initialize_mtlx_paths():
    maya_root = os.environ.get('MAYA_LOCATION')
    # Path to the bundled MaterialX Python modules in Maya 2026
    mtlx_site_packages = os.path.join(maya_root, 'bin', 'python', 'site-packages')
    
    if mtlx_site_packages not in sys.path:
        sys.path.append(mtlx_site_packages)
        

##########################################
# Not directly supported Any longer
##########################################
# def startX_ITE(args):
#    public_path = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
#    public_path = public_path+"/public"
#
#    npx.call(['http-server', public_path])
############################################

# Global RawKee menu systems Object used to add Menus to Maya Main Window
# Cosntructing the RawKee menu system using "maya.cmds" is a more pleasant 
# experience than using MEL 
rkWeb3D = None
_rkSceneEditorWin = None

'''
Outliner Right Click Character Functions for mGear
'''
class RKMGearSkelToCGESkin(aom.MPxCommand):
    kPluginCmdName = "rkMGearSkelToCGESkin"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKMGearSkelToCGESkin()
        
    def doIt(self, argList):
        print("buildCGESkinFromSkeleton")

        selectNames = cmds.ls(sl=True, long=False)
        selectPaths = cmds.ls(sl=True, long=True)
        if not selectNames:
            print("buildCGESkinFromSkeleton: nothing selected.")
            return

        self.sourceRoot = selectPaths[0]

        # --- 1. Save mGear pose and reset to bind pose so the duplicate
        #        captures bind-pose joint positions. ---
        mgearRoot = self._findMGearRoot(self.sourceRoot)
        #charName = cmds.getAttr(f"{mgearRoot}.rig_name")
        cmds.select(mgearRoot)
        self.addCustomMGearCtlValues()

        # --- 2. Create CGESkin container ---
        #actualName = cmds.createNode('transform', ss=True, name=f'CGESkin_{charName}')
        #cmds.addAttr(actualName, longName="rkPoseCount", at="long", defaultValue=0)
        #cmds.addAttr(actualName, longName='x3dGroupType', dataType='string', keyable=False)
        #cmds.setAttr(actualName + '.x3dGroupType', "CGESkin", type='string', lock=True)
        
        cmds.addAttr(mgearRoot, longName="rkPoseCount", at="long", defaultValue=0)
        cmds.addAttr(mgearRoot, longName='x3dGroupType', dataType='string', keyable=False)
        cmds.setAttr(mgearRoot + '.x3dGroupType', "CGESkin", type='string', lock=True)
        try:
            stk.put(mgearRoot, "x3dCGESkin.png")
        except Exception as e:
            print(f"buildCGESkinFromSkeleton: sticker failed: {e}")

        #cmds.parent(self.sourceRoot, actualName)
        #cmds.parent(mgearRoot, actualName)
        cmds.parent( self.sourceRoot, mgearRoot)
        cmds.reorder(self.sourceRoot.split("|")[-1], front=True)


    ##################################
    # Bind Pose Functions
    ##################################
    def addCustomMGearCtlValues(self):
        selected = cmds.ls(sl=True, type="transform")
        if not selected:
            print("addCustomMGearCtlValues: no transform selected.")
            return
        root        = selected[0]
        descendants = cmds.listRelatives(root, allDescendents=True, type="transform", fullPath=True) or []
        controls    = [n for n in descendants
                       if cmds.attributeQuery("isCtl", node=n, exists=True)]

        for ctl in controls:
            #if not cmds.attributeQuery("rkPoseCount", node=ctl, exists=True):
            #    cmds.addAttr(ctl, longName="rkPoseCount", at="long", defaultValue=0)
            #rkPCount = cmds.getAttr(f"{ctl}.rkPoseCount")
            #rkPCount += 1
            #cmds.setAttr(f"{ctl}.rkPoseCount", rkPCount)

            for attr in (cmds.listAttr(ctl, keyable=True) or []):
                try:
                    attrValue = cmds.getAttr(f"{ctl}.{attr}")
                    if not isinstance(attrValue, (int, float)):
                        continue
                    if cmds.attributeQuery(f"rkPose_{attr}_0", node=ctl, exists=True):
                        cmds.setAttr(f"{ctl}.rkPose_{attr}_0", attrValue)
                    else:
                        #cmds.addAttr(ctl, longName=f"rkPose_{attr}_{rkPCount}", defaultValue=attrValue, hidden=True)
                        cmds.addAttr(ctl, longName=f"rkPose_{attr}_0", at="double",
                                     defaultValue=attrValue, hidden=True)
                except Exception as e:
                    print(f"addCustomMGearCtlValues: skipped '{ctl}.{attr}': {e}")


    #################################################
    # Find mGear Rig Root via Dependency Graph
    #################################################
    def _findMGearRoot(self, jointFullPath):
        """Find the mGear rig root transform.

        Traverses the dependency graph upstream from *jointFullPath*, filtering
        for transform nodes.  The first transform found that carries the mGear
        'isCtl' attribute is an mGear control; walking up its DAG chain to the
        world level yields the rig root.  Falls back to the joint's own topmost
        DAG ancestor if no controls are reachable."""
        sel = om.MSelectionList()
        sel.add(jointFullPath)
        jointObj = sel.getDependNode(0)

        dgIter = om.MItDependencyGraph(
            jointObj,
            om.MFn.kTransform,
            om.MItDependencyGraph.kUpstream,
            om.MItDependencyGraph.kBreadthFirst,
            om.MItDependencyGraph.kNodeLevel
        )
        while not dgIter.isDone():
            node     = dgIter.currentNode()
            nodeName = om.MFnDependencyNode(node).name()
            if cmds.attributeQuery('isCtl', node=nodeName, exists=True):
                # Found a control — walk up its DAG chain looking for the mGear
                # rig root, identified by the presence of 'is_rig' or 'gear_version'.
                current = om.MFnDagNode(node).fullPathName()
                while True:
                    if (cmds.attributeQuery('is_rig',      node=current, exists=True) or
                            cmds.attributeQuery('gear_version', node=current, exists=True)):
                        return current
                    parents = cmds.listRelatives(current, parent=True, fullPath=True)
                    if not parents:
                        break
                    current = parents[0]
            dgIter.next()

        # Fallback: no mGear root found upstream; use the joint's top DAG ancestor.
        print("_findMGearRoot: no mGear rig root reachable from skeleton DG; using joint's top ancestor.")
        current = jointFullPath
        while True:
            parents = cmds.listRelatives(current, parent=True, fullPath=True)
            if not parents:
                return current
            current = parents[0]


class RKMGearSkelToHAnim(aom.MPxCommand):
    kPluginCmdName = "rkMGearSkelToHAnim"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKMGearSkelToHAnim()
        
    def doIt(self, argList):
        print("buildHAnimHumanoidFromSkeleton")

        selectNames = cmds.ls(sl=True, long=False)
        selectPaths = cmds.ls(sl=True, long=True)
        if not selectNames:
            print("buildHAnimHumanoidFromSkeleton: nothing selected.")
            return

        self.sourceRoot = selectPaths[0]

        # --- 1. Save mGear pose and reset to bind pose so the duplicate
        #        captures bind-pose joint positions. ---
        mgearRoot = self._findMGearRoot(self.sourceRoot)
        charName = cmds.getAttr(f"{mgearRoot}.rig_name")
        cmds.select(mgearRoot)
        self.addCustomMGearCtlValues()

        # --- 2. Create HAnimHumanoid container ---
        actualName = cmds.createNode('transform', ss=True, name=f'HAnim_{charName}')
        cmds.addAttr(actualName, longName="rkPoseCount", at="long", defaultValue=0)
        cmds.addAttr(actualName, longName='x3dGroupType', dataType='string', keyable=False)
        cmds.setAttr(actualName + '.x3dGroupType', "HAnimHumanoid", type='string', lock=True)
        cmds.addAttr(actualName, longName='levelOfArticulation', shortName='LOA', attributeType='long', keyable=False, defaultValue=0, minValue=-1, maxValue=4)
        cmds.addAttr(actualName, longName="skeletalConfiguration", dataType="string")
        cmds.setAttr(actualName + '.skeletalConfiguration', "BASIC", type="string")
        try:
            stk.put(actualName, "x3dHAnimHumanoid.png")
        except Exception as e:
            print(f"buildHAnimHumanoidFromSkeleton: sticker failed: {e}")

        # --- 3. Create a clean duplicate skeleton under HAnimHumanoid.
        #        _createJointHierarchyUnderParent copies all TRS values but no
        #        connections, so makeIdentity runs without fighting live rig values. ---
        srcToDupShortMap = {}
        self._createJointHierarchyUnderParent(self.sourceRoot, actualName, srcToDupShortMap)

        dupRootList = cmds.listRelatives(actualName, children=True, type='joint', fullPath=True) or []
        if not dupRootList:
            print("buildHAnimHumanoidFromSkeleton: failed to create duplicate root joint.")
            return
        dupRoot = dupRootList[0]

        # Full-path source → duplicate map used throughout the rest of the function.
        srcToFullDupMap = {}
        self._buildJointMap(self.sourceRoot, dupRoot, srcToFullDupMap)

        # --- 4. Freeze duplicate and push translations into offsetParentMatrix ---
        cmds.makeIdentity(dupRoot, apply=True, t=True, r=True, s=True, n=False, pn=True, jo=True)

        dupJoints = [dupRoot]
        dupDescs  = cmds.listRelatives(dupRoot, ad=True, type='joint', fullPath=True) or []
        dupDescs.sort(key=lambda j: j.count('|'))
        dupJoints.extend(dupDescs)

        for dj in dupJoints:
            x = cmds.getAttr(dj + '.translateX')
            y = cmds.getAttr(dj + '.translateY')
            z = cmds.getAttr(dj + '.translateZ')
            cmds.setAttr(dj + '.offsetParentMatrix',
                         [1,0,0,0, 0,1,0,0, 0,0,1,0, x,y,z,1],
                         type='matrix')
            cmds.setAttr(dj + '.translate',   0.0, 0.0, 0.0, type='double3')
            cmds.setAttr(dj + '.rotateOrder', 0)

        # --- 5. Add a parentConstraint from each source joint to its corresponding
        #        duplicate joint so the duplicate skeleton follows the source rig. ---
        for srcJoint, dupJoint in srcToFullDupMap.items():
            try:
                cmds.parentConstraint(srcJoint, dupJoint, mo=True, w=1)
            except Exception as e:
                print(f"buildHAnimHumanoidFromSkeleton: parentConstraint {srcJoint} \u2192 {dupJoint}: {e}")
        self.resetMGear(mgearRoot)

        # --- 6. Parent mGear root under HAnimHumanoid ---
        if cmds.objExists(mgearRoot):
            result    = cmds.parent(mgearRoot, actualName)
            mgearRoot = cmds.ls(result[0], long=True)[0]
            cmds.reorder(mgearRoot, front=True)

        # --- 7. Collect bound meshes and save skin weights from source skeleton ---
        skelSel = om.MSelectionList()
        skelSel.add(self.sourceRoot)
        srDag   = om.MFnDagNode(skelSel.getDagPath(0))
        skins   = []
        self.collectBoundSkins(srDag, skins)

        skinClusters = []
        for skin in skins:
            self.collectSkinClusterFromSkin(skin, skinClusters)

        # Map each source influencer to its duplicate counterpart.
        infDagPaths = []
        for sc in skinClusters:
            dupPaths = []
            for inf in (cmds.skinCluster(sc.name(), q=True, inf=True) or []):
                try:
                    iSel = om.MSelectionList()
                    iSel.add(inf)
                    srcPath = iSel.getDagPath(0).fullPathName()
                    dupPath = srcToFullDupMap.get(srcPath)
                    if dupPath:
                        dSel = om.MSelectionList()
                        dSel.add(dupPath)
                        dupPaths.append(dSel.getDagPath(0))
                    else:
                        print(f"buildHAnimHumanoidFromSkeleton: no dup for influencer '{srcPath}'")
                except Exception as e:
                    print(f"buildHAnimHumanoidFromSkeleton: influencer '{inf}': {e}")
            infDagPaths.append(dupPaths)

        meshWeights = []
        infLengths  = []
        for i in range(len(skins)):
            self.getWeightsFromSkin(skins[i], skinClusters[i], meshWeights, infLengths)

        # --- 8. Unbind meshes from source skeleton ---
        for skin in skins:
            cmds.skinCluster(skin.name(), edit=True, unbind=True, ubk=True)

        # --- 9. Rebind meshes to the duplicate skeleton ---
        boundSkins    = []
        boundWeights  = []
        boundInfPaths = []
        for i in range(len(skins)):
            if not infDagPaths[i]:
                print(f"buildHAnimHumanoidFromSkeleton: no dup joints for '{skins[i].name()}' — skipping")
                continue
            try:
                cmds.delete(skins[i].fullPathName(), ch=True)
                jStrings = [dp.fullPathName() for dp in infDagPaths[i]]
                cmds.skinCluster(jStrings + [skins[i].fullPathName()], tsb=True)
                boundSkins.append(skins[i])
                boundWeights.append(meshWeights[i])
                boundInfPaths.append(infDagPaths[i])
            except Exception as e:
                print(f"buildHAnimHumanoidFromSkeleton: rebind '{skins[i].name()}': {e}")

        self.overWriteWeights(boundSkins, boundWeights, boundInfPaths)

        # --- 10. Remove the parentConstraints that were added to the duplicate
        #         joints in step 6 before the mGear connections are redirected. ---
        for dupJoint in srcToFullDupMap.values():
            try:
                cons = cmds.listRelatives(dupJoint, children=True,
                                          type='parentConstraint', fullPath=True) or []
                if cons:
                    cmds.delete(cons)
            except Exception as e:
                print(f"buildHAnimHumanoidFromSkeleton: delete parentConstraint on {dupJoint}: {e}")

        # --- 11. Redirect mGear rig connections from source to duplicate joints.
        #        Direct connections are rewired; constraint-based connections are
        #        deleted from source and recreated on the duplicate with mo=True
        #        so the offset is recalculated for the new (OPM-based) joint pose. ---
        CONSTRAINT_TYPES = ('parentConstraint', 'orientConstraint',
                            'pointConstraint',  'scaleConstraint')
        TRS_ATTRS = [
            'translate',   'translateX',   'translateY',   'translateZ',
            'rotate',      'rotateX',      'rotateY',      'rotateZ',
            'scale',       'scaleX',       'scaleY',       'scaleZ',
            'jointOrient', 'jointOrientX', 'jointOrientY', 'jointOrientZ',
            'rotateAxis',  'rotateAxisX',  'rotateAxisY',  'rotateAxisZ',
        ]

        for srcJoint, dupJoint in srcToFullDupMap.items():
            # Rewire direct (non-constraint) incoming TRS connections.
            try:
                iSel    = om.MSelectionList()
                iSel.add(srcJoint)
                mobj    = iSel.getDependNode(0)
                srcFull = iSel.getDagPath(0).fullPathName()
                depFn   = om.MFnDependencyNode(mobj)
                for attrName in TRS_ATTRS:
                    try:
                        attr = depFn.attribute(attrName)
                        plug = om.MPlug(mobj, attr)
                        if plug.isDestination:
                            driverNode = plug.source().name().split('.')[0]
                            if cmds.nodeType(driverNode) not in CONSTRAINT_TYPES:
                                srcPlugName = plug.source().name()
                                dstAttr = plug.partialName(includeNodeName=False, useLongNames=True)
                                cmds.disconnectAttr(srcPlugName, srcFull + '.' + dstAttr)
                                cmds.connectAttr(srcPlugName, dupJoint + '.' + dstAttr, force=True)
                    except Exception as e:
                        print(f"buildHAnimHumanoidFromSkeleton: redirect '{attrName}' on {srcJoint}: {e}")
            except Exception as e:
                print(f"buildHAnimHumanoidFromSkeleton: redirect API setup {srcJoint}: {e}")

            # Recreate constraint-based connections on the duplicate joint.
            try:
                cons = cmds.listRelatives(srcJoint, children=True,
                                          type=list(CONSTRAINT_TYPES), fullPath=True) or []
                for con in cons:
                    conType = cmds.nodeType(con)
                    try:
                        if conType == 'parentConstraint':
                            targets = cmds.parentConstraint(con, q=True, targetList=True) or []
                            if targets:
                                cmds.parentConstraint(targets, dupJoint, mo=True, w=1)
                        elif conType == 'orientConstraint':
                            targets = cmds.orientConstraint(con, q=True, targetList=True) or []
                            if targets:
                                cmds.orientConstraint(targets, dupJoint, mo=True, w=1)
                        elif conType == 'pointConstraint':
                            targets = cmds.pointConstraint(con, q=True, targetList=True) or []
                            if targets:
                                cmds.pointConstraint(targets, dupJoint, mo=True, w=1)
                        elif conType == 'scaleConstraint':
                            targets = cmds.scaleConstraint(con, q=True, targetList=True) or []
                            if targets:
                                cmds.scaleConstraint(targets, dupJoint, mo=True, w=1)
                    except Exception as e:
                        print(f"buildHAnimHumanoidFromSkeleton: recreate {conType} on {dupJoint}: {e}")
            except Exception as e:
                print(f"buildHAnimHumanoidFromSkeleton: constraint redirect {srcJoint}: {e}")

        # --- 12. Delete source skeleton ---
        if cmds.objExists(self.sourceRoot):
            cmds.delete(self.sourceRoot)

        # --- 13. Rename duplicate joints to the original source short names.
        #         Sort deepest-first so parent renames don't invalidate child paths. ---
        renameItems = sorted(srcToFullDupMap.items(),
                             key=lambda p: p[0].count('|'), reverse=True)
        for srcPath, dupPath in renameItems:
            srcShortName = srcPath.split('|')[-1]
            try:
                if cmds.objExists(dupPath):
                    cmds.rename(dupPath, srcShortName)
            except Exception as e:
                print(f"buildHAnimHumanoidFromSkeleton: rename {dupPath} → {srcShortName}: {e}")

        # Refresh duplicateRoot and sourceRoot to the renamed dup root.
        dupRootFinal = (cmds.listRelatives(actualName, children=True, type='joint',
                                           fullPath=True) or [None])[0]
        self.duplicateRoot = dupRootFinal or dupRoot
        self.sourceRoot    = self.duplicateRoot

        # --- 14. Save bind pose ---
        #finalJoints = [self.duplicateRoot]
        #finalJoints.extend(
        #    cmds.listRelatives(self.duplicateRoot, ad=True, type='joint', fullPath=True) or []
        #)
        #cmds.select(finalJoints)
        #poseName = cmds.dagPose(save=True, selection=True, name="iPose")
        #cmds.addAttr(poseName, longName='x3dHAnimPose', dataType="string")
        #cmds.setAttr(poseName + ".x3dHAnimPose", "iPose", type="string")

        # --- 15. Restore mGear pose ---
        self.setMGearPose(0, root=actualName)
        cmds.reorder(self.sourceRoot.split("|")[-1], front=True)

        print("buildHAnimHumanoidFromSkeleton: complete.")


    #################################################
    # Find mGear Rig Root via Dependency Graph
    #################################################
    def _findMGearRoot(self, jointFullPath):
        """Find the mGear rig root transform.

        Traverses the dependency graph upstream from *jointFullPath*, filtering
        for transform nodes.  The first transform found that carries the mGear
        'isCtl' attribute is an mGear control; walking up its DAG chain to the
        world level yields the rig root.  Falls back to the joint's own topmost
        DAG ancestor if no controls are reachable."""
        sel = om.MSelectionList()
        sel.add(jointFullPath)
        jointObj = sel.getDependNode(0)

        dgIter = om.MItDependencyGraph(
            jointObj,
            om.MFn.kTransform,
            om.MItDependencyGraph.kUpstream,
            om.MItDependencyGraph.kBreadthFirst,
            om.MItDependencyGraph.kNodeLevel
        )
        while not dgIter.isDone():
            node     = dgIter.currentNode()
            nodeName = om.MFnDependencyNode(node).name()
            if cmds.attributeQuery('isCtl', node=nodeName, exists=True):
                # Found a control — walk up its DAG chain looking for the mGear
                # rig root, identified by the presence of 'is_rig' or 'gear_version'.
                current = om.MFnDagNode(node).fullPathName()
                while True:
                    if (cmds.attributeQuery('is_rig',      node=current, exists=True) or
                            cmds.attributeQuery('gear_version', node=current, exists=True)):
                        return current
                    parents = cmds.listRelatives(current, parent=True, fullPath=True)
                    if not parents:
                        break
                    current = parents[0]
            dgIter.next()

        # Fallback: no mGear root found upstream; use the joint's top DAG ancestor.
        print("_findMGearRoot: no mGear rig root reachable from skeleton DG; using joint's top ancestor.")
        current = jointFullPath
        while True:
            parents = cmds.listRelatives(current, parent=True, fullPath=True)
            if not parents:
                return current
            current = parents[0]


    ##################################
    # Bind Pose Functions
    ##################################
    def addCustomMGearCtlValues(self):
        selected = cmds.ls(sl=True, type="transform")
        if not selected:
            print("addCustomMGearCtlValues: no transform selected.")
            return
        root        = selected[0]
        descendants = cmds.listRelatives(root, allDescendents=True, type="transform", fullPath=True) or []
        controls    = [n for n in descendants
                       if cmds.attributeQuery("isCtl", node=n, exists=True)]

        for ctl in controls:
            #if not cmds.attributeQuery("rkPoseCount", node=ctl, exists=True):
            #    cmds.addAttr(ctl, longName="rkPoseCount", at="long", defaultValue=0)
            #rkPCount = cmds.getAttr(f"{ctl}.rkPoseCount")
            #rkPCount += 1
            #cmds.setAttr(f"{ctl}.rkPoseCount", rkPCount)

            for attr in (cmds.listAttr(ctl, keyable=True) or []):
                try:
                    attrValue = cmds.getAttr(f"{ctl}.{attr}")
                    if not isinstance(attrValue, (int, float)):
                        continue
                    if cmds.attributeQuery(f"rkPose_{attr}_0", node=ctl, exists=True):
                        cmds.setAttr(f"{ctl}.rkPose_{attr}_0", attrValue)
                    else:
                        #cmds.addAttr(ctl, longName=f"rkPose_{attr}_{rkPCount}", defaultValue=attrValue, hidden=True)
                        cmds.addAttr(ctl, longName=f"rkPose_{attr}_0", at="double",
                                     defaultValue=attrValue, hidden=True)
                except Exception as e:
                    print(f"addCustomMGearCtlValues: skipped '{ctl}.{attr}': {e}")


    #################################################
    # Recursive Joint Hierarchy Builder
    #################################################
    def _createJointHierarchyUnderParent(self, srcJoint, parentNode, srcToDupMap):
        """Create one new joint under *parentNode* whose local transform
        exactly mirrors *srcJoint*, then recurse into each joint child.

        The new joint's short name is the source short name with a ``_ha``
        suffix; ``_uniqueJointName`` ensures there are no collisions.

        *srcToDupMap* accumulates {srcFullPath: newJointShortName} entries
        for every joint created during the recursion."""
        srcShortName = srcJoint.split('|')[-1]
        newName      = self._uniqueJointName(srcShortName + '_ha')

        # Read every local transform component from the source so that the
        # new joint occupies the identical world position.
        t   = cmds.getAttr(srcJoint + '.translate')[0]
        r   = cmds.getAttr(srcJoint + '.rotate')[0]
        jo  = cmds.getAttr(srcJoint + '.jointOrient')[0]
        ra  = cmds.getAttr(srcJoint + '.rotateAxis')[0]
        s   = cmds.getAttr(srcJoint + '.scale')[0]
        ro  = cmds.getAttr(srcJoint + '.rotateOrder')
        rad = cmds.getAttr(srcJoint + '.radius')
        opm = cmds.getAttr(srcJoint + '.offsetParentMatrix')

        newJoint = cmds.createNode('joint', name=newName, parent=parentNode)

        cmds.setAttr(newJoint + '.translate',    t[0],  t[1],  t[2])
        cmds.setAttr(newJoint + '.rotate',       r[0],  r[1],  r[2])
        cmds.setAttr(newJoint + '.jointOrient', jo[0], jo[1], jo[2])
        cmds.setAttr(newJoint + '.rotateAxis',  ra[0], ra[1], ra[2])
        cmds.setAttr(newJoint + '.scale',        s[0],  s[1],  s[2])
        cmds.setAttr(newJoint + '.rotateOrder', ro)
        cmds.setAttr(newJoint + '.radius', rad)
        cmds.setAttr(newJoint + '.offsetParentMatrix', opm, type='matrix')

        srcToDupMap[srcJoint] = newJoint

        children = cmds.listRelatives(srcJoint, children=True, type='joint', fullPath=True) or []
        for child in children:
            self._createJointHierarchyUnderParent(child, newJoint, srcToDupMap)

        return newJoint


    #################################################
    # Build Source-to-Duplicate Joint Mapping
    ##################################################
    def _buildJointMap(self, srcRootPath, dupRootPath, mapping):
        """Walk the source and duplicate joint hierarchies in parallel and
        populate *mapping* with entries of the form:
            source_joint_full_path -> duplicate_joint_full_path

        The duplicate skeleton must have been created by duplicating the source
        skeleton (via buildHAnimHumanoidFromSkeleton), so both hierarchies are structurally
        identical even though joint names may differ due to Maya auto-numbering
        collisions at duplication time (e.g. ``root`` -> ``root1``)."""
        srcSel = om.MSelectionList()
        dupSel = om.MSelectionList()
        srcSel.add(srcRootPath)
        dupSel.add(dupRootPath)
        mapping[srcSel.getDagPath(0).fullPathName()] = dupSel.getDagPath(0).fullPathName()

        srcChildren = cmds.listRelatives(srcRootPath, children=True, type='joint', fullPath=True) or []
        dupChildren = cmds.listRelatives(dupRootPath, children=True, type='joint', fullPath=True) or []

        for i in range(min(len(srcChildren), len(dupChildren))):
            self._buildJointMap(srcChildren[i], dupChildren[i], mapping)


    def resetMGear(self, mgearRoot):
        root = mgearRoot
        if root is None:
            print("resetMGear: no mgearRoot was provided.")
            return
        descendants = cmds.listRelatives(root, allDescendents=True, type="transform", fullPath=True) or []
        controls    = [n for n in descendants
                       if cmds.attributeQuery("isCtl", node=n, exists=True)]
        for ctl in controls:
            for attr in (cmds.listAttr(ctl, keyable=True) or []):
                try:
                    default = cmds.attributeQuery(attr, node=ctl, listDefault=True)
                    if default is not None:
                        cmds.setAttr(f"{ctl}.{attr}", default[0])
                except:
                    pass


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
        
            
    def collectSkinClusterFromSkin(self, mNode, skinClusters):
        #smlist = om.MSelectionList()
        #smlist.add(mNode.name())
        #mpath = smlist.getDagPath(0)
        
        skClusters = []
        scIter = om.MItDependencyGraph(mNode.object(), rkfn.kSkinClusterFilter, om.MItDependencyGraph.kUpstream, om.MItDependencyGraph.kBreadthFirst, om.MItDependencyGraph.kNodeLevel)
        while not scIter.isDone():
            skClusters.append(omAnim.MFnSkinCluster(scIter.currentNode()))
            scIter.next()
        
        #if len(skClusters) > 0:
        #    skinClusters.append(skClusters[0])
        for skc in skClusters:
            print("Name: " + skc.name())
            skinClusters.append(skc)

        
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
            print("After\n")


    #################################################
    # Unique Joint Name Generator
    #################################################
    def _uniqueJointName(self, baseName):
        """Return *baseName* unchanged if no scene node with that name exists,
        otherwise append incrementing integers (baseName1, baseName2, …) until
        a free name is found."""
        if not cmds.objExists(baseName):
            return baseName
        i = 1
        candidate = f"{baseName}{i}"
        while cmds.objExists(candidate):
            i += 1
            candidate = f"{baseName}{i}"
        return candidate


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
        

    def setMGearPose(self, poseIndex, root=None):
        if root is None:
            selected = cmds.ls(sl=True, type="transform")
            if not selected:
                print("setMGearPose: no transform selected.")
                return
            root = selected[0]
        descendants = cmds.listRelatives(root, allDescendents=True, type="transform", fullPath=True) or []
        controls    = [n for n in descendants
                       if cmds.attributeQuery("isCtl", node=n, exists=True)]
        for ctl in controls:
            for attr in (cmds.listAttr(ctl, keyable=True) or []):
                try:
                    poseAttr = f"rkPose_{attr}_{poseIndex}"
                    if cmds.attributeQuery(poseAttr, node=ctl, exists=True):
                        poseValue = cmds.getAttr(f"{ctl}.{poseAttr}")
                        if isinstance(poseValue, (int, float)):
                            cmds.setAttr(f"{ctl}.{attr}", poseValue)
                except Exception as e:
                    print(f"setMGearPose: skipped '{ctl}.{attr}': {e}")
###################################################################################


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


# Creating the MEL Command for showing the Sunrize Editor Website
class RKShowSunrize(aom.MPxCommand):
    kPluginCmdName = "rkShowSunrize"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowSunrize()
        
    def doIt(self, args):
        webbrowser.open_new("https://create3000.github.io/sunrize/")


# Creating the MEL Command for showing the RawKee Help Wiki
class RKShowX_ITE(aom.MPxCommand):
    kPluginCmdName = "rkShowX_ITE"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowX_ITE()
        
    def doIt(self, args):
        webbrowser.open_new("https://create3000.github.io/x_ite/")


# Creating the MEL Command for showing the RawKee Help Wiki
class RKShowCGE(aom.MPxCommand):
    kPluginCmdName = "rkShowCGE"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowCGE()
        
    def doIt(self, args):
        webbrowser.open_new("https://castle-engine.io/")


class RKShowX3DOM(aom.MPxCommand):
    kPluginCmdName = "rkShowX3DOM"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowX3DOM()
        
    def doIt(self, args):
        webbrowser.open_new("https://www.x3dom.org/")


class RKShowART(aom.MPxCommand):
    kPluginCmdName = "rkShowART"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowART()
        
    def doIt(self, args):
        webbrowser.open_new("https://www.antcgi.com/store/p/art-modular-rigging-tool")


class RKShowAdvSkel(aom.MPxCommand):
    kPluginCmdName = "rkShowAdvSkel"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowAdvSkel()
        
    def doIt(self, args):
        webbrowser.open_new("https://animationstudios.com.au/")


class RKShowmGear(aom.MPxCommand):
    kPluginCmdName = "rkShowmGear"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowmGear()
        
    def doIt(self, args):
        webbrowser.open_new("https://mgear-framework.com/")


# Creating the MEL Command for showing the RawKee Help Wiki
class RKShowHelpWiki(aom.MPxCommand):
    kPluginCmdName = "rkShowHelpWiki"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowHelpWiki()
        
    def doIt(self, args):
        webbrowser.open_new("https://github.com/und-dream-lab/rawkee/wiki")


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

class RKSetBindPose(aom.MPxCommand):
    kPluginCmdName = "rkSetBindPose"
    
    def __int__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKSetBindPose()

    def doIt(self, args):
        self.nodeName = ""
        
        if len(args) > 0:
            tArg = args.asString(0)
            if cmds.objExists(tArg):
                self.nodeName = tArg
        
        if cmds.objExists(self.nodeName + "_defpose"):
            cmds.delete(  self.nodeName + "_defpose")
        cmds.select(      self.nodeName)
        cmds.dagPose( save=True, selection=False, name=self.nodeName + "_defpose" )
        
        
        
class RKAssignLabelAsName(aom.MPxCommand):
    kPluginCmdName = "rkAssignLabelAsName"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
    
    @staticmethod
    def cmdCreator():
        return RKAssignLabelAsName()
        
    def doIt(self, args):
        objs  = cmds.ls(selection=True)
        mList = aom.MSelectionList()
        for obj in objs:
            mList.add(obj)
        
        oLen = mList.length()
        for i in range(oLen):
            dagNode = aom.MFnDagNode(mList.getDependNode(i))
            if dagNode.typeName == "joint":
                cls.setJointNameToJointName(dagNode)
                break

    @classmethod
    def setJointNameToJointName(cls, jNode):
        jLabel = cls.getCGEJointLabel(jNode)
        jNode.setName(jLabel)
        
        dnCount = jNode.childcount()
        
        # First Pass - Interate children with a priority of Joint nodes
        for i in range(dnCount):
            dagChild = aom.MFnDagNode(jNode.child(i))
            if   dagChild.typeName == "joint":
                cls.setJointNameToJointName(dagChild)


    @classmethod    
    def getCGEJointLabel(cls, jNode):
        jointName = ""
        hasMeat = True

        sideVal = cmds.getAttr(jNode.name() + ".side")
        if sideVal == 0:
            jointName = "Center_"
        elif sideVal == 1:
            jointName = "Left_"
        elif sideVal == 2:
            jointName = "Right_"

        nType = cmds.getAttr(jNode.name() + ".type")
        
        typeText = self.getJointType(str(nType))
        
        if typeText == "Other":
            typeText = cmds.getAttr(jNode.name() + ".otherType")
            
        if typeText == "":
            hasMeat = False

        if hasMeat == True:
            jointName += typeText
        else:
            jointName = jNode.name()
        
            #if jointName == "":
            #    jointName = "Random_" + str(random.randint(1000001, 2000000))
            #   print("CGE WARNING: Printed random joint name because it was not defined in the Maya joint's (Side), (Type), and (OtherType) attributes - CGE Joint Name: " + jointName)
        
        return jointName


class RKShowSceneEditor(aom.MPxCommand):
    kPluginCmdName = "rkShowSceneEditor"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowSceneEditor()
        
    def doIt(self, args):
        sceneEditorControlName = RKSceneEditorMaya.scene_editor_control_name()
        if cmds.workspaceControl(sceneEditorControlName, exists=True):
            cmds.workspaceControl(sceneEditorControlName, e=True, close=True,
                                  closeCommand=RKSceneEditorMaya.workplace_close_command())
            cmds.deleteUI(sceneEditorControlName)
        rkSEEditor = RKSceneEditorMaya()
        rkSEEditor.show(dockable=True, uiScript=RKSceneEditorMaya.workspace_ui_script())


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
            rkCEditor.CBIDs = RKCallBackIDs
            #rkCEditor.setRKWeb3D(rkWeb3D)
            rkCEditor.show(dockable=True, uiScript=RKCharacterEditor.workspace_ui_script())
        else:
            print("RKWeb3D is not set!")
        


class RKShowBindPoseEditor(aom.MPxCommand):
    kPluginCmdName = "rkShowBindPoseEditor"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowBindPoseEditor()
        
    def doIt(self, args):
        print("RawKee X3D - Bind Pose Editor")
        #cmds.rkPrimeX3DScene()
        
        global rkWeb3D
        if rkWeb3D is not None:
            bindposeEditorControlName = RKBindPoseEditor.bindpose_editor_control_name()
        
            if cmds.workspaceControl(bindposeEditorControlName, exists=True):
                #Must Close before Delete
                cmds.workspaceControl(bindposeEditorControlName, e=True, close=True, closeCommand=RKBindPoseEditor.workplace_close_command())
                cmds.deleteUI(bindposeEditorControlName)
            
            rkBPEditor = RKBindPoseEditor()
            rkBPEditor.CBIDs = RKCallBackIDs
            #rkCEditor.setRKWeb3D(rkWeb3D)
            rkBPEditor.show(dockable=True, uiScript=RKBindPoseEditor.workspace_ui_script())
        else:
            print("RKWeb3D is not set!")


class RKShowCharacterAnimationClipEditor(aom.MPxCommand):
    kPluginCmdName = "rkShowCharacterAnimationClipEditor"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowCharacterAnimationClipEditor()
        
    def doIt(self, args):
        print("RawKee X3D - Character Animation Clip Editor")
        
        global rkWeb3D
        if rkWeb3D is not None:
            characterAnimationClipEditorControlName = RKCharacterAnimationClipEditor.character_animation_clip_editor_control_name()
        
            if cmds.workspaceControl(characterAnimationClipEditorControlName, exists=True):
                #Must Close before Delete
                cmds.workspaceControl(characterAnimationClipEditorControlName, e=True, close=True, closeCommand=RKCharacterAnimationClipEditor.workplace_close_command())
                cmds.deleteUI(characterAnimationClipEditorControlName)
            
            rkCACEditor = RKCharacterAnimationClipEditor()
            rkCACEditor.CBIDs = RKCallBackIDs
            rkCACEditor.show(dockable=True, uiScript=RKCharacterAnimationClipEditor.workspace_ui_script())
        else:
            print("RKWeb3D is not set!")


class RKShowMaterialXEditor(aom.MPxCommand):
    kPluginCmdName = "rkShowMaterialXEditor"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowMaterialXEditor()
        
    def doIt(self, args):
        print("RawKee X3D - MaterialX Editor")
        
        global rkWeb3D
        if rkWeb3D is not None:
            materialXEditorControlName = RKMaterialXEditor.materialx_editor_control_name()
        
            if cmds.workspaceControl(materialXEditorControlName, exists=True):
                #Must Close before Delete
                cmds.workspaceControl(materialXEditorControlName, e=True, close=True, closeCommand=RKMaterialXEditor.workplace_close_command())
                cmds.deleteUI(materialXEditorControlName)
            
            rkMTXEditor = RKMaterialXEditor()
            rkMTXEditor.CBIDs = RKCallBackIDs
            rkMTXEditor.show(dockable=True, uiScript=RKMaterialXEditor.workspace_ui_script())
        else:
            print("RKWeb3D is not set!")


class RKShowHAnimHumanoidSetupEditor(aom.MPxCommand):
    kPluginCmdName = "rkShowHAnimHumanoidSetupEditor"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowHAnimHumanoidSetupEditor()
        
    def doIt(self, args):
        print("RawKee X3D - HAnimHumanoid Setup Editor")
        #cmds.rkPrimeX3DScene()
        
        global rkWeb3D
        if rkWeb3D is not None:
            hanimHumanoidSetupEditorControlName = RKHAnimHumanoidSetupEditor.hanim_humanoid_setup_editor_control_name()
        
            if cmds.workspaceControl(hanimHumanoidSetupEditorControlName, exists=True):
                #Must Close before Delete
                cmds.workspaceControl(hanimHumanoidSetupEditorControlName, e=True, close=True, closeCommand=RKHAnimHumanoidSetupEditor.workplace_close_command())
                cmds.deleteUI(hanimHumanoidSetupEditorControlName)
            
            rkHHSEditor = RKHAnimHumanoidSetupEditor()
            rkHHSEditor.CBIDs = RKCallBackIDs
            #rkCEditor.setRKWeb3D(rkWeb3D)
            rkHHSEditor.show(dockable=True, uiScript=RKHAnimHumanoidSetupEditor.workspace_ui_script())
        else:
            print("RKWeb3D is not set!")


class RKShowMGearSetupEditor(aom.MPxCommand):
    kPluginCmdName = "rkShowMGearSetupEditor"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKShowMGearSetupEditor()
        
    def doIt(self, args):
        print("RawKee X3D - mGear Setup Editor")
        #cmds.rkPrimeX3DScene()
        
        global rkWeb3D
        if rkWeb3D is not None:
            mgearSetupEditorControlName = RKmGearSetupEditor.mgear_setup_editor_control_name()
        
            if cmds.workspaceControl(mgearSetupEditorControlName, exists=True):
                #Must Close before Delete
                cmds.workspaceControl(mgearSetupEditorControlName, e=True, close=True, closeCommand=RKmGearSetupEditor.workplace_close_command())
                cmds.deleteUI(mgearSetupEditorControlName)
            
            rkMGSEditor = RKmGearSetupEditor()
            rkMGSEditor.CBIDs = RKCallBackIDs
            #rkCEditor.setRKWeb3D(rkWeb3D)
            rkMGSEditor.show(dockable=True, uiScript=RKmGearSetupEditor.workspace_ui_script())
        else:
            print("RKWeb3D is not set!")


def runRawKeeInitializer(plugin):
    print("Made possible by the: Alias Research Donation Program\n\n")
    pluginFn = aom.MFnPlugin(plugin, RAWKEE_VENDOR, RAWKEE_VERSION)
 
    # RawKee Utility Functions required to be in MEL format such as functions related to AE Templates.
    RAWKEE_BASE = RKWeb3D.__file__.replace("\\", "/").rsplit("/", 1)[0]
    mel.eval('source "' + RAWKEE_BASE + '/mel/x3d.mel"')
    
    # Check to see if the Advanced Skelton Scripts are installed, and if they are, 
    # source the main AS script.
    adString = "AdvancedSkeleton"
    envString = mel.eval('getenv MAYA_SCRIPT_PATH')
    if adString in envString:
        mel.eval('source "AdvancedSkeletonFiles/../AdvancedSkeleton.mel"')
        print("Sourced mel scripts for Advanced Skeleton toolset. Adding Advanced Skeleton functionality to RawKee HAnim Character Export")
    else:
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
        # mGear Character Functions
        pluginFn.registerCommand(RKMGearSkelToHAnim.kPluginCmdName, RKMGearSkelToHAnim.cmdCreator)
        pluginFn.registerCommand(RKMGearSkelToCGESkin.kPluginCmdName, RKMGearSkelToCGESkin.cmdCreator)
        
        #pluginFn.registerCommand(        RKServer.kPluginCmdName,         RKServer.cmdCreator)
        #pluginFn.registerCommand(          RKAddX3DSound.kPluginCmdName,     RKAddX3DSound.cmdCreator)
        pluginFn.registerCommand(RKASBackupClipBoard.kPluginCmdName,   RKASBackupClipBoard.cmdCreator)
        pluginFn.registerCommand(RKASRestoreClipBoard.kPluginCmdName, RKASRestoreClipBoard.cmdCreator)
        
        pluginFn.registerCommand(    RKShowAdvSkel.kPluginCmdName,      RKShowAdvSkel.cmdCreator)
        pluginFn.registerCommand(      RKShowmGear.kPluginCmdName,        RKShowmGear.cmdCreator)
        pluginFn.registerCommand(        RKShowART.kPluginCmdName,          RKShowART.cmdCreator)
        pluginFn.registerCommand(      RKShowX3DOM.kPluginCmdName,        RKShowX3DOM.cmdCreator)
        pluginFn.registerCommand(        RKShowCGE.kPluginCmdName,          RKShowCGE.cmdCreator)
        pluginFn.registerCommand(      RKShowX_ITE.kPluginCmdName,        RKShowX_ITE.cmdCreator)
        pluginFn.registerCommand(    RKShowSunrize.kPluginCmdName,      RKShowSunrize.cmdCreator)
        pluginFn.registerCommand(   RKShowHelpWiki.kPluginCmdName,     RKShowHelpWiki.cmdCreator)
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

        try:
            pluginFn.registerCommand(RKShowMGearSetupEditor.kPluginCmdName, RKShowMGearSetupEditor.cmdCreator)
        except Exception as e:
            sys.stderr.write("RKShowMGearSetupEditor - Failed to unregister a plugin command.\n")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {e}")

        try:
            pluginFn.registerCommand(RKShowHAnimHumanoidSetupEditor.kPluginCmdName, RKShowHAnimHumanoidSetupEditor.cmdCreator)
        except Exception as e:
            sys.stderr.write("RKShowHAnimHumanoidSetupEditor - Failed to unregister a plugin command.\n")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {e}")

        try:
            pluginFn.registerCommand(RKShowCharacterAnimationClipEditor.kPluginCmdName, RKShowCharacterAnimationClipEditor.cmdCreator)
        except Exception as e:
            sys.stderr.write("RKShowCharacterAnimationClipEditor - Failed to unregister a plugin command.\n")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {e}")
            
        try:
            pluginFn.registerCommand(RKShowMaterialXEditor.kPluginCmdName, RKShowMaterialXEditor.cmdCreator)
        except Exception as e:
            sys.stderr.write("RKShowMaterialXEditor - Failed to unregister a plugin command.\n")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {e}")

        pluginFn.registerCommand( RKShowBindPoseEditor.kPluginCmdName,  RKShowBindPoseEditor.cmdCreator)
        pluginFn.registerCommand(RKShowCharacterEditor.kPluginCmdName, RKShowCharacterEditor.cmdCreator)
        pluginFn.registerCommand(    RKShowSceneEditor.kPluginCmdName,     RKShowSceneEditor.cmdCreator)
        
        pluginFn.registerCommand(  RKX3DSetProject.kPluginCmdName,   RKX3DSetProject.cmdCreator)
        pluginFn.registerCommand(  RKCASSetProject.kPluginCmdName,   RKCASSetProject.cmdCreator)
        pluginFn.registerCommand(    RKCASExportOp.kPluginCmdName,     RKCASExportOp.cmdCreator)
        pluginFn.registerCommand( RKCASSelExportOp.kPluginCmdName,  RKCASSelExportOp.cmdCreator)
        pluginFn.registerCommand(      RKCASExport.kPluginCmdName,       RKCASExport.cmdCreator)
        pluginFn.registerCommand(   RKCASSelExport.kPluginCmdName,    RKCASSelExport.cmdCreator)
        
        pluginFn.registerCommand(   RKX3DAuxLoader.kPluginCmdName,    RKX3DAuxLoader.cmdCreator)
        
        pluginFn.registerCommand( RKAssignLabelAsName.kPluginCmdName, RKAssignLabelAsName.cmdCreator)
        
        pluginFn.registerCommand( RKSetBindPose.kPluginCmdName, RKSetBindPose.cmdCreator)
    except:
        sys.stderr.write("Failed to register a plugin command.\n")

    # Function that sets the Maya global varaibles required by RawKee - Found in 'rawkee4maya.maya.RKUtils'
    mel.eval('setDefRKOptVars()')

    # Create Menu System for RawKee 'rawkee4maya.RKMenus'
    global rkWeb3D
    rkWeb3D = RKWeb3D.RKWeb3D()
    rkWeb3D.pVersion = RAWKEE_TITLE
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

    #addRKAnimPackNodeDeleteCallback()
    
    
# Initialize the plug-in
def initializePlugin(plugin):
    initialize_mtlx_paths()
    
    # Now it is safe to import the specific Gen modules
    try:
        import MaterialX.PyMaterialXGenShader as mx_gen_shader
        import MaterialX.PyMaterialXGenGlsl as mx_gen_glsl
        
        runRawKeeInitializer(plugin)
        # Proceed with registering nodes/commands
    except ImportError as e:
        om.MGlobal.displayError(f"Failed to load MaterialX Gen modules: {e}")



# Uninitialize the plug-in
def uninitializePlugin(plugin):
    pluginFn = aom.MFnPlugin(plugin)
    
    
    ##################################
    '''
    DEREGISTERING Custom RawKee Commands
    '''
    ##################################
    try:
        pluginFn.deregisterCommand(RKSetBindPose.kPluginCmdName)
    except:
        sys.stderr.write("RKSetBindPose failed to deregister")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")
        
    try:
        pluginFn.deregisterCommand(RKAssignLabelAsName.kPluginCmdName)
    except:
        sys.stderr.write("RKAssignLabelAsName failed to deregister")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")
    
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
        pluginFn.deregisterCommand(RKShowBindPoseEditor.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowBindPoseEditor - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(RKShowMaterialXEditor.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowMaterialXEditor - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(RKShowCharacterAnimationClipEditor.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowCharacterAnimationClipEditor - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(RKShowHAnimHumanoidSetupEditor.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowHAnimHumanoidSetupEditor - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(RKShowMGearSetupEditor.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowMGearSetupEditor - Failed to unregister a plugin command.\n")
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
        pluginFn.deregisterCommand(   RKShowHelpWiki.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowHelpWiki - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(    RKShowSunrize.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowSunrize - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKShowX_ITE.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowX_ITE - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(        RKShowCGE.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowCGE - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKShowX3DOM.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowX3DOM - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKShowART.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowART - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKShowmGear.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowmGear - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand(      RKShowAdvSkel.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKShowAdvSkel - Failed to unregister a plugin command.\n")
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
        
    try:
        pluginFn.deregisterCommand( RKMGearSkelToCGESkin.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKMGearSkelToCGESkin - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

    try:
        pluginFn.deregisterCommand( RKMGearSkelToHAnim.kPluginCmdName)
    except Exception as e:
        sys.stderr.write("RKMGearSkelToHAnim - Failed to unregister a plugin command.\n")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

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
    except:
        aom.MGlobal.displayError("Failed to deregister a node.")#{0}".format(X3DSound.TYPE_NAME))

    ##################################################################
    # Removal of Remote Menu Sysem for RawKee from Maya Main Window
    ##################################################################
    
    # First we must remove the refernce to RKWeb3D object in the editor panels
    # otherwise the object's __del__ function won't by code below of...
    # 'del rkWeb3D'
    
    ########### Scene Editor ##################
    sceneEditorControlName = RKSceneEditorMaya.scene_editor_control_name()
    if cmds.workspaceControl(sceneEditorControlName, exists=True):
        cmds.workspaceControl(sceneEditorControlName, e=True, close=True,
                              closeCommand=RKSceneEditorMaya.workplace_close_command())
        cmds.deleteUI(sceneEditorControlName)
    
    ########### Deprecated Character Editor ####################
    characterEditorControlName = RKCharacterEditor.character_editor_control_name()

    if cmds.workspaceControl(characterEditorControlName, exists=True):
        #Must Close before Delete
        cmds.workspaceControl(characterEditorControlName, e=True, close=True, closeCommand=RKCharacterEditor.workplace_close_command())
        cmds.deleteUI(characterEditorControlName)
    
    ########## mGear Setup Editor ##################
    mgearSetupEditorControlName = RKmGearSetupEditor.mgear_setup_editor_control_name()

    if cmds.workspaceControl(mgearSetupEditorControlName, exists=True):
        #Must Close before Delete
        cmds.workspaceControl(mgearSetupEditorControlName, e=True, close=True, closeCommand=RKmGearSetupEditor.workplace_close_command())
        cmds.deleteUI(mgearSetupEditorControlName)
    
    
    ########## MaterialX Editor ##################
    materialXEditorControlName = RKMaterialXEditor.materialx_editor_control_name()

    if cmds.workspaceControl(materialXEditorControlName, exists=True):
        #Must Close before Delete
        cmds.workspaceControl(materialXEditorControlName, e=True, close=True, closeCommand=RKMaterialXEditor.workplace_close_command())
        cmds.deleteUI(materialXEditorControlName)
    
    
    ########## Character Animation Clip Editor ##################
    characterAnimationClipEditorControlName = RKCharacterAnimationClipEditor.character_animation_clip_editor_control_name()

    if cmds.workspaceControl(characterAnimationClipEditorControlName, exists=True):
        #Must Close before Delete
        cmds.workspaceControl(characterAnimationClipEditorControlName, e=True, close=True, closeCommand=RKCharacterAnimationClipEditor.workplace_close_command())
        cmds.deleteUI(characterAnimationClipEditorControlName)
    
    
    ########## HAnimHumanoid Setup Editor ##################
    hanimHumanoidSetupEditorControlName = RKHAnimHumanoidSetupEditor.hanim_humanoid_setup_editor_control_name()

    if cmds.workspaceControl(hanimHumanoidSetupEditorControlName, exists=True):
        #Must Close before Delete
        cmds.workspaceControl(hanimHumanoidSetupEditorControlName, e=True, close=True, closeCommand=RKHAnimHumanoidSetupEditor.workplace_close_command())
        cmds.deleteUI(hanimHumanoidSetupEditorControlName)
    
    
    ########### Bind Pose / HAnimPose node Editor #############
    bindposeEditorControlName = RKBindPoseEditor.bindpose_editor_control_name()

    if cmds.workspaceControl(bindposeEditorControlName, exists=True):
        #Must Close before Delete
        cmds.workspaceControl(bindposeEditorControlName, e=True, close=True, closeCommand=RKBindPoseEditor.workplace_close_command())
        cmds.deleteUI(bindposeEditorControlName)
    
    # Delete the RKWeb3D object that is the menu system and 
    # export function system for the MayaMainWindow
    global rkWeb3D
    rkWeb3D.removeRawKeeMenu()
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
