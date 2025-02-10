import sys
import maya.api.OpenMaya as aom
import maya.OpenMayaUI   as omui
import maya.cmds         as cmds
import maya.mel          as mel
import os

###########################################################
# Used for killing external applications started by RawKee,
# but methods implented don't work as expected. May remove.
###########################################################
import signal                                           ###
###########################################################

##########################################
# Used for launching external applications
##########################################
import subprocess        as sp         ###
##########################################

from rawkee import RKOrganizer
from rawkee import RKSceneEditor
from rawkee.RKFOptsDialog import RKFOptsDialog

#from rawkee.RKUtils import *

import x3d              as rkx3d

try:
    from PySide2           import QtCore
    from PySide2           import QtWidgets
    from PySide2           import QtGui
    from PySide2.QtWidgets import QAction
    from PySide2.QtWidgets import QActionGroup
    from PySide2.QtWidgets import QIcon
    from PySide2.QtWidgets import QMenu
    from PySide2.QtWidgets import QWidgetAction
    from PySide2.QtWidgets import QButtonGroup
    from PySide2.QtWidgets import QPushButton
    from shiboken2         import wrapInstance

except:
    from PySide6           import QtCore
    from PySide6           import QtWidgets
    from PySide6           import QtGui
    from PySide6.QtGui     import QAction
    from PySide6.QtGui     import QActionGroup
    from PySide6.QtGui     import QIcon
    from PySide6.QtWidgets import QMenu
    from PySide6.QtWidgets import QWidgetAction
    from PySide6.QtWidgets import QButtonGroup
    from PySide6.QtWidgets import QPushButton
    from shiboken6         import wrapInstance

class RKWeb3D():

    def __init__(self):
        # Grab Main Window
        self.mayaWin = self.mayaMainWindow()
        
        self.pVersion = ""
        
        self.rko = None
        
        self.server = None 
        
        self.curDir   = ""
        self.fileName = ""
        self.dirPath  = ""
        self.fullPath = ""
        self.selectedFilter = ""
        #                       self.x3dfilters = "X3D XML (*.x3d);;X3D Classic (*.x3dv);;X3D Binary (*.x3db);;X3D Enhanced Binary (*.x3de);;X3D JSON (*.x3dj);;X3D JSON (*.json);;VRML97 (*.wrl);;Web3D Files (*.x3d *.x3db *.x3de *.x3dj *.x3dv *.json *.wrl)"
        self.x3dfilters = "X3D XML (*.x3d);;X3D Classic (*.x3dv);;VRML 97 (*.wrl);;X3D JSON (*.x3dj);;X3D JSON (*.json);;Web3D Files (*.x3d *.x3dv *.wrl *.x3dj *.json)"
        
        # Setup the main 'RawKee X3D' plugin menu
        self.rkMenuName ="rawkee_menu"

        #Populate the RawKee X3D Menu
        self.addRawKeeMenu()
        
        self.x3dDocs = []
        
    def __del__(self):
        self.removeRawKeeMenu()
        #self.termServer()
        
#        if self.rko != None:
#            del self.rko
    
    def launchServer(self):
        public_path = RKOrganizer.__file__.replace("\\", "/").rsplit("/", 1)[0]
        public_path = public_path+"/public"
        print("Launching Server")
#        myCmd = "mayapy -m nodejs.npx http-server" + public_path
#        self.server = sp.Popen(myCmd)        
        self.server = sp.Popen(["mayapy", "-m", "nodejs.npx", "http-server", public_path], creationflags=sp.CREATE_NEW_CONSOLE)        
#        self.server = sp.Popen(["mayapy -m nodejs.npx", "http-server", public_path])
        
    def termServer(self):
        print("OS name: " + os.name)
#        os.kill(self.server.pid, signal.CTRL_C_EVENT)
        if os.name  == 'nt':
            self.server
        else:
            self.server.send_signal(signal_SIGTERM)
    
    # Function to get Maya Main Window Widget
    def mayaMainWindow(self):
        '''
        Using Qt and Shiboken to grab a pointer to the main Maya window and 
        return it as a QWidget
        '''
        mainWindowPtr = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mainWindowPtr), QtWidgets.QMainWindow)
        
    # If called grabs the Maya Main Window from this class in the form of a QMainWindow object.
    def getMayaWindow(self):
        return self.mayaWin

    # Generate "RawKee (X3D)" - main plugin menu
    def addRawKeeMenu(self):
        '''
        Construct RawKee's Primary Menu for the Main Window, and then
        add the menu to the main menu.
        '''
        print("Add Menu Ran")
    
        
        #TODO: Implement Connections to function calls ##############
        #cmds.window(query=True, mainMenuBar=True)
        self.rawKeeMenu = cmds.menu(self.rkMenuName, label = 'RawKee (X3D)', tearOff=True, p='MayaWindow')#QMenu("RawKee (X3D)", self.mayaWin)

        '''
        cmds.menuItem(label='RawKee Tutorials')#self.rawKeeMenu.addAction("RawKee Tutorials")# -command "showX3DTutorials";
        cmds.menuItem(label='RawKee Documentation')#self.rawKeeMenu.addAction("RawKee Documentation")# -command "showX3DTutorials";
        '''
        cmds.menuItem(divider=True, dividerLabel='File - Import/Export' )                                                           #self.rawKeeMenu.addSection("File - Import/Export")
        self.x3dExport       = cmds.menuItem(label='Export All - X3D',      command='maya.cmds.rkX3DExport()')
        self.x3dExportOpt    = cmds.menuItem(image=':menu_options.png',     command='maya.cmds.rkX3DExportOp()',    optionBox=True) #self.rawKeeMenu.addAction(self.x3dExportOpt)
        self.x3dSelExport    = cmds.menuItem(label='Export Selected - X3D', command='maya.cmds.rkX3DSelExport()')
        self.x3dSelExportOpt = cmds.menuItem(image=':menu_options.png',     command='maya.cmds.rkX3DSelExportOp()', optionBox=True) #self.rawKeeMenu.addAction(self.x3dExportOpt)
        self.x3dImport       = cmds.menuItem(label='Import X3D Files',      command='maya.cmds.rkX3DImport()')                      #self.rawKeeMenu.addAction(self.x3dImport)
        self.x3dImportOpt    = cmds.menuItem(image=':menu_options.png',     command='maya.cmds.rkX3DImportOp()',    optionBox=True) #self.rawKeeMenu.addAction(self.x3dImportOpt)
#        self.x3dExport.addAction("Export Scene Prep")# -c "x3dPrepareSceneForExport";

        #--------------------------------------------------------------------
        # Finishing off the  X3D Plug-in menu
        #--------------------------------------------------------------------
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(divider=True, dividerLabel='RawKee Editors')
        cmds.menuItem(label='X3D Interaction Editor', command='maya.cmds.rkShowSceneEditor()')                # -command "showX3DIEditor";
        #cmds.menuItem(label='X3D Character Editor')                  # -command "x3dCharacterEditor";
        #cmds.menuItem(label='X3D Animation Editor')                  # -command "x3dAnimationEditor";

        '''
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(divider=True, dividerLabel='Texture Utility Commands')
        cmds.menuItem(label='Set All MultiTexture Modes: Default')   # -c ("x3dSetAllSingleTextureModes 0");
        cmds.menuItem(label='Set All MultiTexture Modes: Replace')   # -c ("x3dSetAllSingleTextureModes 1");
        cmds.menuItem(label='Set All MultiTexture Modes: Modulate')  # -c ("x3dSetAllSingleTextureModes 2");
        cmds.menuItem(label='Set All MultiTexture Modes: Add')       # -c ("x3dSetAllSingleTextureModes 3");
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Make All Textures PixelTextures')       # -c ("x3dSetAllTexturesPixel");
        cmds.menuItem(label='Make All Textures ImageTextures')       # -c ("x3dSetAllTexturesFile");
        '''

        cmds.menuItem(divider=True, dividerLabel='Code Repositories')
        cmds.menuItem(label='RawKee GitHub Python Repo')
        cmds.menuItem(divider=True, dividerLabel='Websites')
        cmds.menuItem(label='Univ. of North Dakota - DREAM Lab')
        cmds.menuItem(label='Web3D Consortium')
        cmds.menuItem(label='Metaverse Standards Forum')
        cmds.menuItem(label='Test Function', command='maya.cmds.rkTestIt()')
        ###################################################
    
        mel.eval('addRawKeeMenuItemsToFileMenu()')
    
    
    # Destroy "RawKee (X3D)" - main plugin menu
    def removeRawKeeMenu(self):
        '''
        Remove and destroy the RawKee Primary Menu
        '''
        
        try:
            cmds.deleteUI(self.rkMenuName)     
            cmds.refresh()
            mel.eval('removeRawKeeMenuItemsFromFileMenu()')
        except:
            print("An error occured when attempting to remove the RawKee menubar menu, and rawkee items from the 'File' menu.")

        print("Removing Menus")
    
    def printTheGlobal(self):
        print("The Global")
    
    # Export Function
    def activateExportFunctions(self):
        print("RawKee X3D Export")
        
        #############################################
        # Prepare New X3D Document with Scene
        profileType = "Full"
        x3dVersion  = "4.0"
        x3dDoc = rkx3d.X3D(profile=profileType, version=x3dVersion)
        x3dDoc.Scene = rkx3d.Scene()

        #############################################
        # Get File Path From QFileDialog File Chooser
        # Placing this activity here because users
        # expect the file chooser to appear 
        # immediately when attempting a file 
        # save/export.
        if self.curDir == "":
            self.curDir = cmds.internalVar(userAppDir=True)

        self.dirPath = self.curDir
        self.fullPath = self.dirPath
        self.fullPath, self.selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self.mayaWin, QtCore.QObject.tr("RawKee - Export File As..."), self.fullPath, QtCore.QObject.tr(self.x3dfilters))
        print(self.selectedFilter)

        #############################################
        # Making certain there is a valid file path 
        # before proceeding.
        if self.fullPath != None and self.fullPath != "":
        
            # TODO Move this to the actual export call - From RKUtils.py 
            #processNonFileTextures()
        
            #########################################
            # Create the Object that organizes the 
            # data in the maya scen to be 
            # copied into the X3D Document object
            rko = RKOrganizer.RKOrganizer()
        
            #########################################
            # Rethink if we want this code here
            # Commenting it out for now.
            '''
            # Setup Basic File Path Info
            self.rko.fileName = self.fullPath
            idx = self.rko.fileName.rfind("/")
            self.rko.localPath = self.rko.fileName[:idx+1]
            print(self.rko.localPath)
            
            
            ###############################################
            #x3dEO.setFileSax3dWriter(tempFile);
            self.rko.rkio.fullPath = self.rko.fileName
            
            #x3dEO.setExportStyle(filter());
            self.rko.setExportStyle(self.selectedFilter)
            '''

            ###############################################
            # Commenting this out for now. But will 
            # probably will still use it at some point,
            # though it may be called from another lcoation
            # in the code.
            #############################
            rko.organizeExport() # TODO - Required to keep the scene traversal from crashing, becauese the 'ignore' methods are called here.
            #############################

            # Grab Transforms parented to the real root.
            parentDagPaths, topDagNodes = rko.getAllTopDagNodes()
            
            # Traverse DAG and map node data to X3D
            rko.maya2x3d(x3dDoc.Scene, parentDagPaths, topDagNodes, self.pVersion)
            
            # Write the X3D data to a file.
            exEncoding     = "x3d"
            if   self.selectedFilter == "X3D Classic (*.x3dv)":
                exEncoding = "x3dv"
            elif self.selectedFilter == "X3D JSON (*.x3dj)"     or self.selectedFilter == "X3D JSON (*.json)":
                exEncoding = "x3dj"

            rko.rkio.x3d2disk(x3dDoc, self.fullPath, exEncoding)
            
            # Delete the RKOrganizer object.
            del rko
            
        else:
            print("User Cancelled file selection.")
        
        # Delete the X3D Document object now that it is no longer being used.
        del x3dDoc
        
        
    # Export Function
    def activateSelExportFunctions(self):
        print("RawKee X3D Selected Export")


    # Export Options Function
    def activateExportOptions(self):
        dTitle = "X3D Export Options"
        try:
            self.openIODialog.close()
            self.openIODialog.deleteLater()
        except:
            pass
            
        self.openIODialog = RKFOptsDialog(dialogTitle=dTitle)
        self.openIODialog.show()
        
        print("TODO: Implement Export Options Window")
        
    
    # Export Options Function
    def activateSelExportOptions(self):
        dTitle = "X3D Export Selected Options"
        try:
            self.openIODialog.close()
            self.openIODialog.deleteLater()
        except:
            pass
            
        self.openIODialog = RKFOptsDialog(dialogTitle=dTitle)
        self.openIODialog.show()
        
        print("TODO: Implement Select Export Options Window")
        
    
    # Import Function
    def activateImportFunctions(self):
        print("RawKee X3D Import")
        
        if self.curDir == "":
            self.curDir = cmds.internalVar(userAppDir=True)

        self.dirPath = self.curDir
        self.fullPath = self.dirPath
        
        
        self.fullPath, self.selectedFilter = QtWidgets.QFileDialog.getOpenFileName(self.mayaWin, QtCore.QObject.tr("RawKee - Select File to Import"), self.fullPath, QtCore.QObject.tr(self.x3dfilters))
    
        #self.rko.processImportFile(self.fullPath, self.selectedFilter)
    
    # Import Options Function
    def activateImportOptions(self):
        dTitle = "X3D Import Options"
        try:
            self.openIODialog.close()
            self.openIODialog.deleteLater()
        except:
            pass
            
        self.openIODialog = RKFOptsDialog(dialogTitle=dTitle)
        self.openIODialog.show()

        print("TODO: Implement Import Options Window")
        
    # Options for Castle Game Engine Export All - Send
    def activateCastleExportOptions(self):
        dTitle = "Castle Export All - Options"
        try:
            self.openIODialog.close()
            self.openIODialog.deleteLater()
        except:
            pass
            
        self.openIODialog = RKFOptsDialog(dialogTitle=dTitle)
        self.openIODialog.show()
        
    
    # Options for Castle Game Engine Export Selected Items - Send
    def activateCastleSelExportOptions(self):
        dTitle = "Castle Export Selected - Options"
        try:
            self.openIODialog.close()
            self.openIODialog.deleteLater()
        except:
            pass
            
        self.openIODialog = RKFOptsDialog(dialogTitle=dTitle)
        self.openIODialog.show()
        
    
    # File Import/Export Options Window
    def activateFOptsDialog(self):
        pass
        
    
    def setCastleProjectDirectory(self):
        prjVal = cmds.optionVar( query = 'rkCastlePrjDir')
        
        directoryResult = QtWidgets.QFileDialog.getExistingDirectory(self.mayaWin,  QtCore.QObject.tr("Set Castle Game Engine Project"), prjVal)
        
        if directoryResult:
            cmds.optionVar(sv=('rkCastlePrjDir', directoryResult))
        else:
            print("Directory Selection Cancelled.")
            
        #getOpenFileName(self.mayaWin, QtCore.QObject.tr("RawKee - Select File to Import"), self.fullPath, QtCore.QObject.tr(self.x3dfilters))

# Creating the MEL Command for the RawKee's Command to add a switch node
class RKAddCollision(aom.MPxCommand):
    kPluginCmdName = "rkAddCollision"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKAddCollision()
        
    def doIt(self, args):
        # Transform matrix is not locked. Instead, transforms translate, rotate, scale are frozen at
        # export time.
        node = cmds.createNode("transform", name='collision')
        cmds.addAttr(longName='proxy', attributeType='bool', defaultValue=False)
        cmds.addAttr(longName='x3dGroupType', dataType='string', keyable=False)
        cmds.setAttr(node + '.x3dGroupType', "x3dCollision", type='string', lock=True)
        
class RKAddX3DSound(aom.MPxCommand):
    kPluginCmdName = "rkAddX3DSound"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKAddX3DSound()
        
    def doIt(self, args):
        notFound = True
        istr = ""
        xStr = ""
        i = 0
        while notFound:
            xStr = "x3dSoundShape" + istr
            try:
                cmds.select(xStr)
                xList = cmds.ls( selection=True )
                if len(xList) > 0:
                    i = i + 1
                    istr = str(i)
            except:
                notFound = False
        pNode = cmds.createNode("transform", name="x3dSound")
        cmds.createNode("x3dSound", name=xStr, parent=pNode)
        
        

# Creating the MEL Command for the RawKee's Command to add a group node
class RKAddGroup(aom.MPxCommand):
    kPluginCmdName = "rkAddGroup"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKAddGroup()
        
    def doIt(self, args):
        # Transform matrix is not locked. Instead, transforms translate, rotate, scale are frozen at
        # export time.
        node = cmds.createNode("transform", name='group')
        cmds.addAttr(longName='x3dGroupType', dataType='string', keyable=False)
        cmds.setAttr(node + '.x3dGroupType', "x3dGroup", type='string', lock=True)


# Creating the MEL Command for the RawKee's Command to add a switch node
class RKAddSwitch(aom.MPxCommand):
    kPluginCmdName = "rkAddSwitch"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKAddSwitch()
        
    def doIt(self, args):
        # Transform matrix is not locked. Instead, transforms translate, rotate, scale are frozen at
        # export time.
        node = cmds.createNode("transform", name='switch')
        cmds.addAttr(longName='whichChoice', attributeType='long', defaultValue=-1, min=-1, keyable=False)
        cmds.addAttr(longName='x3dGroupType', dataType='string', keyable=False)
        cmds.setAttr(node + '.x3dGroupType', "x3dSwitch", type='string', lock=True)
        

# Creating the MEL Command for the RawKee's Command to add a switch node
class RKSetAsBillboard(aom.MPxCommand):
    kPluginCmdName = "rkSetAsBillboard"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKSetAsBillboard()
        
    def doIt(self, args):
        # Transform matrix is not locked. Instead, transforms translate, rotate, scale are frozen at
        # export time.
        
        rkSelections = cmds.ls(selection=True)
        rkNewSel = []
        
        for sel in rkSelections:
            x3dGTAttr = cmds.listAttr(sel, st=['x3dGroupType'])
            if not x3dGTAttr:
                if cmds.nodeType(sel) == 'transform':
                    rkChildren = cmds.listRelatives(sel, children=True)
                    isReady = True
                    print("Relatives")
                    for rkChild in rkChildren:
                        if cmds.nodeType(rkChild) == 'locator':
                            print("Found locator")
                            isReady = False
                        elif cmds.nodeType(rkChild) == 'aimConstraint':
                            print('Found aim constraint')
                            isReady = False
                    if isReady == True:
                        print('appending selection')
                        rkNewSel.append(sel)
        
        i = len(rkNewSel)
        print("RKNewSel: " + str(i))
        if i == 0:
            print('No eligible transform selected.')
        else:
            x3dBLoc = None
            cmds.select(cl=True)
        
            try:
                x3dBLoc = cmds.select('x3dBBLocator')
            except:
                x3dBLoc = cmds.spaceLocator(p=(0.0,0.0,0.0), name='x3dBLocator')
                cmds.select(cl=True)
                cmds.select('persp')
                cmds.select(x3dBLoc, add=True)
                mel.eval('doCreatePointConstraintArgList 1 { "0","0","0","0","0","1","0","1","","1" }')
                conNode = cmds.pointConstraint(offset=(0.0,0.0,0.0), skip='y', weight=1)
                cmds.reorder(conNode, front=True)
            
            if x3dBLoc != None:
                for node in rkNewSel:
                    cmds.select(cl=True)
                    cmds.select(x3dBLoc)
                    cmds.select(node, add=True)
                    mel.eval('doCreateAimConstraintArgList 1 { "0","0","0","0","1","0","0","0","1","0","0","1","0","1","vector","","0","0","0","","1" }')
                    conNode = cmds.aimConstraint( offset=(0.0,0.0,0.0), weight=1, aimVector=(0.0,0.0,1.0), upVector=(0.0,1.0,0.0), worldUpType='vector', worldUpVector=((0.0,1.0,0.0)))
                    cmds.reorder(conNode, front=True)
                    cmds.addAttr(longName='x3dGroupType', dataType='string', keyable=False)
                    cmds.setAttr(node + '.x3dGroupType', "x3dBillboard", type='string', lock=True)

# Creating the MEL Command for the RawKee's Command to add a group node
class RKTestIt(aom.MPxCommand):
    kPluginCmdName = "rkTestIt"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKTestIt()
        
    def doIt(self, args):
        print("Temporary Test Function")
        
        # Transform matrix is not locked. Instead, transforms translate, rotate, scale are frozen at
        # export time.
        '''
        node0 = cmds.createNode("X3D_Scene", name='xTestScene')
        node1 = cmds.createNode("X3D_Transform", name='xTestTrans')
        node2 = cmds.createNode("X3D_Group", name='xTestGroup')
        node3 = cmds.createNode("X3D_Group", name='xTestGroup1')
        
        mlist = aom.MSelectionList()
        mlist.add("xTestScene")
        mlist.add("xTestTrans")
        mlist.add("xTestGroup")
        mlist.add("xTestGroup1")

        pNode0 = aom.MFnDependencyNode(mlist.getDependNode(0)).userNode()
        pNode1 = aom.MFnDependencyNode(mlist.getDependNode(1)).userNode()
        pNode2 = aom.MFnDependencyNode(mlist.getDependNode(2)).userNode()
        pNode3 = aom.MFnDependencyNode(mlist.getDependNode(3)).userNode()
        
        mScene = pNode0.getScene()
        mTrans = pNode1.getX3DNode()
        mGroup = pNode2.getX3DNode()
        mGroup1 = pNode3.getX3DNode()
        
        mTrans.children.append(mGroup)
        mScene.children.append(mTrans)
        mScene.children.append(mGroup1)
        pNode1.self = None
        cmds.delete("xTestTrans")
        
        print("Length of Scene Children: " + str(len(mScene.children)))
        for n in mScene.children:
            print("Object Type: " + str(type(n)))
        ''' 
        
        
        
        #print(dir(x3d.Scene))
        #print(x3d.Transform().FIELD_DECLARATIONS())
        
        #nodeField = getattr(x3dParentNode, x3dFieldName)
        #if isinstance(nodeField, list):
                
        #methods_list = [method for method in dir(x3d.Scene) if callable(getattr(x3d.Scene, method)) and not method.startswith('__')]
        #print('Methods using dir():', methods_list)
        
        #methods_list = [method for method in dir(x3d.Group) if callable(getattr(x3d.Group, method)) and not method.startswith('__')]
        #print('Methods using dir():', methods_list)
        
        #methods_list = [method for method in dir(x3d.Transform) if callable(getattr(x3d.Transform, method)) and not method.startswith('__')]
        #print('Methods using dir():', methods_list)
        



