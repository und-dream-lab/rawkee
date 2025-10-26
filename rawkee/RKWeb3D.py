import sys
import maya.api.OpenMaya as aom
import maya.OpenMayaUI   as omui
import maya.cmds         as cmds
import maya.mel          as mel
import os
import copy

############################################################################
# Removing this feature.
############################################################################
    # Used for killing external applications started by RawKee,
    # but methods implented don't work as expected. May remove.
    ###########################################################
    # import signal                                         ###
    ###########################################################

    ##########################################
    # Used for launching external applications
    ##########################################
    # import subprocess        as sp       ###
    ##########################################

from rawkee import RKOrganizer
from rawkee import RKSceneEditor
from rawkee.RKFOptsDialog import RKFOptsDialog
from maya.api.OpenMaya    import MFn as rkfn


#from rawkee.RKUtils import *
import rawkee.nodes.sticker    as stk
import rawkee.x3d              as rkx3d

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

        #####################################################################################################################################
        # *.html export will remain temporarily unsupported because of the increasing complexity of the code necessary to support 
        # custom node and field features unique to X3DOM's shader, material, and texture implementation.
        #####################################################################################################################################
        # self.x3dfilters = "X3D XML (*.x3d);;X3D Classic (*.x3dv);;X3D JSON (*.x3dj);;X3D JSON (*.json);;X3D HTML5 (*.html);;Web3D Files (*.x3d *.x3dv *.x3dj *.json *.html)"
        self.x3dfilters = "X3D XML (*.x3d);;X3D Classic (*.x3dv);;X3D JSON (*.x3dj);;X3D JSON (*.json);;Web3D Files (*.x3d *.x3dv *.x3dj *.json)"
        
        # Setup the main 'RawKee X3D' plugin menu
        self.rkMenuName ="rawkee_menu"

        #Populate the RawKee X3D Menu
        self.addRawKeeMenu()
        
        self.x3dDocs = []
        
        self.RKCallBackIDs = []
        
        
    def __del__(self):
        self.removeRawKeeMenu()
        #self.termServer()
        
#        if self.rko != None:
#            del self.rko

    ############################################################################
    # Removing the X_ITE SERVER feature.
    ############################################################################
    # def launchServer(self):
    #    public_path = RKOrganizer.__file__.replace("\\", "/").rsplit("/", 1)[0]
    #    public_path = public_path+"/public"
    #    print("Launching Server")
    #    self.server = sp.Popen(["mayapy", "-m", "nodejs.npx", "http-server", public_path], creationflags=sp.CREATE_NEW_CONSOLE)        
    #
    #    
    # def termServer(self):
    #    print("OS name: " + os.name)
    #    if os.name  == 'nt':
    #        self.server
    #    else:
    #        self.server.send_signal(signal_SIGTERM)
    ############################################################################
    
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
    
        
        # Set the MainWindow MenuBar Menu for RawKee
        self.rawKeeMenu = cmds.menu(self.rkMenuName, label = 'RawKee PE (X3D)', tearOff=True, p='MayaWindow')#QMenu("RawKee (X3D)", self.mayaWin)

        '''
        cmds.menuItem(label='RawKee Tutorials')#self.rawKeeMenu.addAction("RawKee Tutorials")# -command "showX3DTutorials";
        cmds.menuItem(label='RawKee Documentation')#self.rawKeeMenu.addAction("RawKee Documentation")# -command "showX3DTutorials";
        '''
        cmds.menuItem(divider=True, dividerLabel='RawKee - Version 2.0.0 - Python Edition')
        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True)
        cmds.menuItem(label='RawKee Help Wiki',                             command='maya.cmds.rkShowHelpWiki()')

        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True, dividerLabel='File - Import/Export' )                                                           #self.rawKeeMenu.addSection("File - Import/Export")
        cmds.menuItem(divider=True)
        self.x3dExport       = cmds.menuItem(label='Export All - X3D',      command='maya.cmds.rkX3DExport()')
        self.x3dExportOpt    = cmds.menuItem(image=':menu_options.png',     command='maya.cmds.rkX3DExportOp()',    optionBox=True) #self.rawKeeMenu.addAction(self.x3dExportOpt)
        self.x3dSelExport    = cmds.menuItem(label='Export Selected - X3D', command='maya.cmds.rkX3DSelExport()')
        self.x3dSelExportOpt = cmds.menuItem(image=':menu_options.png',     command='maya.cmds.rkX3DSelExportOp()', optionBox=True) #self.rawKeeMenu.addAction(self.x3dExportOpt)
        #self.x3dImport       = cmds.menuItem(label='Import X3D Files',      command='maya.cmds.rkX3DImport()')                      #self.rawKeeMenu.addAction(self.x3dImport)
        #self.x3dImportOpt    = cmds.menuItem(image=':menu_options.png',     command='maya.cmds.rkX3DImportOp()',    optionBox=True) #self.rawKeeMenu.addAction(self.x3dImportOpt)
        self.x3dSetProject   = cmds.menuItem(label='Set RawKee Project',     command='maya.cmds.rkX3DSetProject()')

        #--------------------------------------------------------------------
        # Finishing off the  X3D Plug-in menu
        #--------------------------------------------------------------------
        cmds.setParent(self.rkMenuName, menu=True)

        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True, dividerLabel='RawKee Editors and Tools')
        cmds.menuItem(divider=True)
        ### --- will be part of future release --- ### cmds.menuItem(label='X3D Interaction Editor',             command='maya.cmds.rkShowSceneEditor()'    )                # -command "showX3DIEditor";
        cmds.menuItem(label='X3D Character and Animation Editor', command='maya.cmds.rkShowCharacterEditor()')                # -command "x3dCharacterEditor";
        ### --- will be part of next release --- ### cmds.menuItem(label='X3D General Animation Editor')                  # -command "x3dAnimationEditor";

        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True, dividerLabel='Get Compatible 3rd Party Character Tools')
        cmds.menuItem(divider=True)
        cmds.menuItem(label="Antony Ward's Modular Rigging Tool (aRT)", command='maya.cmds.rkShowART()')
        cmds.menuItem(label='Advanced Skeleton',                        command='maya.cmds.rkShowAdvSkel()')

        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True, dividerLabel='Learn About 3rd Party X3D Editors')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Sunrize - A Multi-Platform X3D Editor',    command='maya.cmds.rkShowSunrize()')

        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True, dividerLabel='Learn About 3rd Party X3D Viewers')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='X_ITE X3D Browser',                        command='maya.cmds.rkShowX_ITE()')
        cmds.menuItem(label='Castle Game Engine',                       command='maya.cmds.rkShowCGE()')
        cmds.menuItem(label='X3DOM - Instant 3D the HTML way!',         command='maya.cmds.rkShowX3DOM()')

        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True, dividerLabel='Visit Related Code Repositories')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='RawKee GitHub Python Repo',                command='maya.cmds.rkShowRawKee()')
        cmds.menuItem(label='Node Sticker - GitHub Repo / MIT License', command='maya.cmds.rkShowNodeSticker()')

        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True, dividerLabel='Websites')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Univ. of North Dakota - DREAM Lab',        command='maya.cmds.rkShowDreamLab()')
        cmds.menuItem(label='Web3D Consortium',                         command='maya.cmds.rkShowWeb3D()')
        cmds.menuItem(label='Metaverse Standards Forum',                command='maya.cmds.rkShowMSF()')
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
    def activateExportFunctions(self, expMode):
        print("RawKee X3D Export")
        
        # Set Export Mode
        cmds.optionVar(iv=('rkExportMode', expMode))

        #############################################
        # Prepare New X3D Document with Scene
        profileType = "Full"
        x3dVersion  = "4.0"
        x3dDoc = rkx3d.X3D(profile=profileType, version=x3dVersion)
        x3dDoc.Scene = rkx3d.Scene()
        eofScene = rkx3d.Scene()
        background = rkx3d.Background()
        background.DEF = "DefaultBackground"
        background.skyColor = (0.2, 0.2, 0.2)
        x3dDoc.Scene.children.append(background)

        #############################################
        # Get File Path From QFileDialog File Chooser
        # Placing this activity here because users
        # expect the file chooser to appear 
        # immediately when attempting a file 
        # save/export.
        if self.curDir == "":
            self.curDir = cmds.internalVar(userAppDir=True)

        if expMode == 0:
            self.dirPath = cmds.optionVar( q='rkPrjDir')
        elif expMode == 1:
            self.dirPath = cmds.optionVar( q='rkCastlePrjDir')
        else:
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
            rko.prepForSceneTraversal()

            # Grab Transforms parented to the real root.
            parentDagPaths, topDagNodes = rko.getAllTopDagNodes()
            
            # Write the X3D data to a file.
            exEncoding     = "x3d"
            fext = os.path.splitext(self.fullPath)[1]
            if   fext == ".x3dv":
                exEncoding = "x3dv"
            elif fext == ".x3dj":
                exEncoding = "x3dj"
            elif fext == ".json":
                exEncoding = "json"
            #####################################################################################################################################
            # *.html export will remain temporarily unsupported because of the increasing complexity of the code necessary to support 
            # custom node and field features unique to X3DOM's shader, material, and texture implementation.
            #####################################################################################################################################
            # elif fext == ".html":
            #    exEncoding = "html"

            # Traverse DAG and map node data to X3D
            rko.maya2x3d(x3dDoc.Scene, eofScene, parentDagPaths, topDagNodes, self.pVersion, self.fullPath, exEncoding)

            # Write X3D Scenegraph to Disk
            rko.rkio.x3d2disk(x3dDoc, self.fullPath, exEncoding)
            
            # Delete the RKOrganizer object.
            del eofScene
            del rko
            
        else:
            print("User Cancelled file selection.")
        
        # Delete the X3D Document object now that it is no longer being used.
        del x3dDoc
        
        
    # Export Function
    def activateSelExportFunctions(self, expMode):
        print("RawKee X3D Selected Export")

        # Set Export Mode
        cmds.optionVar(iv=('rkExportMode', expMode))

        #############################################
        # Prepare New X3D Document with Scene
        profileType = "Full"
        x3dVersion  = "4.0"
        x3dDoc = rkx3d.X3D(profile=profileType, version=x3dVersion)
        x3dDoc.Scene = rkx3d.Scene()
        background = rkx3d.Background()
        background.DEF = "DefaultBackground"
        background.skyColor = (0.2, 0.2, 0.2)
        x3dDoc.Scene.children.append(background)

        #############################################
        # Get File Path From QFileDialog File Chooser
        # Placing this activity here because users
        # expect the file chooser to appear 
        # immediately when attempting a file 
        # save/export.
        if self.curDir == "":
            self.curDir = cmds.internalVar(userAppDir=True)

        if expMode == 0:
            self.dirPath = cmds.optionVar( q='rkPrjDir')
        elif expMode == 1:
            self.dirPath = cmds.optionVar( q='rkCastlePrjDir')
        else:
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
            rko.prepForSceneTraversal()

            # Grab Transforms parented to the real root.
            parentDagPaths, topDagNodes = rko.getSelectedDagNodes()
            
            # Write the X3D data to a file.
            exEncoding     = "x3d"
            fext = os.path.splitext(self.fullPath)[1]
            if   fext == ".x3dv":
                exEncoding = "x3dv"
            elif fext == ".x3dj":
                exEncoding = "x3dj"
            elif fext == ".json":
                exEncoding = "json"
            #####################################################################################################################################
            # *.html export will remain temporarily unsupported because of the increasing complexity of the code necessary to support 
            # custom node and field features unique to X3DOM's shader, material, and texture implementation.
            #####################################################################################################################################
            # elif fext == ".html":
            #    exEncoding = "html"
                
            # Traverse DAG and map node data to X3D
            rko.maya2x3d(x3dDoc.Scene, parentDagPaths, topDagNodes, self.pVersion, self.fullPath, exEncoding)

            # Write X3D Scenegraph to disk.
            rko.rkio.x3d2disk(x3dDoc, self.fullPath, exEncoding)
            
            # Delete the RKOrganizer object.
            del rko
            
        else:
            print("User Cancelled file selection.")
        
        # Delete the X3D Document object now that it is no longer being used.
        del x3dDoc



    # Export Options Function
    def activateExportOptions(self):
        # Set Export Mode
        cmds.optionVar(iv=('rkExportMode', 0))
        
        dTitle = "X3D Export Options"
        try:
            self.openIODialog.close()
            self.openIODialog.deleteLater()
        except:
            pass
            
        self.openIODialog = RKFOptsDialog(dialogTitle=dTitle)
        self.openIODialog.show()
        
        
    
    # Export Options Function
    def activateSelExportOptions(self):
        # Set Export Mode
        cmds.optionVar(iv=('rkExportMode', 0))

        dTitle = "X3D Export Selected Options"
        try:
            self.openIODialog.close()
            self.openIODialog.deleteLater()
        except:
            pass
            
        self.openIODialog = RKFOptsDialog(dialogTitle=dTitle)
        self.openIODialog.show()
        
        
    
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

        
    # Options for Castle Game Engine Export All - Send
    def activateCastleExportOptions(self):
        # Set Export Mode
        cmds.optionVar(iv=('rkExportMode', 1))

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
        # Set Export Mode
        cmds.optionVar(iv=('rkExportMode', 1))

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
            

    def setRawKeeProjectDirectory(self):
        prjVal = cmds.optionVar( query = 'rkPrjDir')
        
        directoryResult = QtWidgets.QFileDialog.getExistingDirectory(self.mayaWin,  QtCore.QObject.tr("Set RawKee X3D Project"), prjVal)
        
        if directoryResult:
            cmds.optionVar(sv=('rkPrjDir', directoryResult))
        else:
            print("Directory Selection Cancelled.")
            


    def setMyStyleSheet(self, qssBasePath):
        print("Loading Qt Style Sheet and applying it to Maya UI. Please be patient, this applicaiton may take 2-3 seconds.", end="")
        stylesheet_filename = qssBasePath + "/auxilary/rkNodeStyle.qss"
        
        file = QtCore.QFile(stylesheet_filename)
        file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
        stylesheet = file.readAll()
        
        QtWidgets.QApplication.instance().setStyleSheet(str(stylesheet, encoding='utf-8'))
        print("")
        print("Qt Style Sheet Applied", end="")


# Backup Existing Advanced Skeleton ClipBoard0.ma file
class RKASBackupClipBoard(aom.MPxCommand):
    kPluginCmdName = "rkASBackupClipBoard"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKASBackupClipBoard()
        
    def doIt(self, args):
        cbTempfile = mel.eval('asGetTempDirectory()')
        cbTempfile += "AdvancedSkeleton/Selector/ClipBoard0"
        cbFile   = cbTempfile + ".ma"
        cbFileBk = cbTempfile + ".bk"
        
        fExists = mel.eval('filetest -e "' + cbFile + '"')
        
        if fExists == True:
            cmds.sysFile( cbFile, copy=cbFileBk )
        
        self.setResult((cbFile, str(fExists)))
        #print("fExists")
        #print(fExists)
        #print("cbFile")
        #print(cbFile)
        
        #return cbFile, fExists
        #return "C:/Users/aaron.bergstrom/AppData/Local/Temp/AdvancedSkeleton/Selector/ClipBoard0.ma", False


# Restore ClipBoard0.ma from backup file
class RKASRestoreClipBoard(aom.MPxCommand):
    kPluginCmdName = "rkASRestoreClipBoard"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKASRestoreClipBoard()
        
    def doIt(self, args):
        cbTempfile = mel.eval('asGetTempDirectory()')
        cbTempfile += "AdvancedSkeleton/Selector/ClipBoard0"
        cbFile   = cbTempfile + ".ma"
        cbFileBk = cbTempfile + ".bk"
        
        fExists = mel.eval('filetest -e "' + cbFileBk + '"')
        if fExists == True:
            cmds.sysFile(cbFileBk, copy=cbFile)


# Creating the MEL Command for Adding Advanced Skeleton compatibility to RawKee
class RKAdvancedSkeleton(aom.MPxCommand):
    kPluginCmdName = "rkAdvancedSkeleton"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)

    @staticmethod
    def cmdCreator():
        return RKAdvancedSkeleton()

    #mel.eval('asCreateGameEngineRootMotion()')
    #cmds.addAttr(haName, longName="loa", attributeType='long', defaultValue=-1, minValue=-1, maxValue=4)        
    #cmds.addAttr(haName, longName="skeletalConfiguration", dataType="string")
    #cmds.setAttr(haName + ".skeletalConfiguration", "CUSTOM", type="string")
    def doIt(self, args):
        mel.eval('AdvancedSkeleton')
        mel.eval('asGoToBuildPose bodySetup')
        mel.eval('asGoToBuildPose faceSetup')
        mel.eval('asCustomOrientJointsCreate()')
        haName = mel.eval('group -n HAnimHumanoid_01 GameSkeletonRoot_M')
        cmds.setAttr( "GameSkeletonRoot_M.visibility", 1 )
        cmds.optionVar( iv=('rkHAnimLoa', 0))
        cmds.optionVar( sv=('rkHAnimSkConfig', "BASIC"))
        cmds.setAttr("GameSkeletonRoot_M.side", 3)
        cmds.setAttr("GameSkeletonRoot_M.type", 18)
        cmds.setAttr("GameSkeletonRoot_M.otherType", "humanoid_root", type="string")
        mel.eval('asCustomOrientJointsConnect()')
        cmds.addAttr(longName="RKExportType", attributeType='long', defaultValue=1, minValue=0, maxValue=4)
        cmds.rkSetAsHAnimHumanoid()


# Ceating the MEL Command to set a transform node to HAnimHumanoid mode
class RKSetAsHAnimHumanoid(aom.MPxCommand):
    kPluginCmdName = "rkSetAsHAnimHumanoid"
    
    kTransNameFlag = "-rkTRN"
    kTransNameLongFlag = "-rkTransformName"
    
    kLOAValueFlag  = '-rkLOA'
    kLOAValueLongFlag  = "-rkLevelOfArticulation"
    
    def __int__(self):
        aom.MPxCommand.__init__(self)
        self.tName = ""
        self.loa = -1
        self.skConfig = "BASIC"
        
    @staticmethod
    def cmdCreator():
        return RKSetAsHAnimHumanoid()
        
    def doIt(self, args):
        self.tName = cmds.optionVar(q='rkHAnimDEF')
        
        if self.tName == "":
            try:
                rkSelections = cmds.ls(selection=True)
                self.tName = rkSelections[0]
            except:
                pass
        else:
            cmds.optionVar( sv=("rkHAnimDEF", ""))
            
        if self.tName != "":
            selList = aom.MSelectionList()
            selList.add(self.tName)

            depNode = aom.MFnDependencyNode(selList.getDependNode(0))
            if depNode.typeName == "transform":
                newAttrs = False
                x3dGT = ""
                try:
                    nameAndAttr = depNode.name() + ".x3dGroupType"
                    x3dGT = cmds.getAttr(nameAndAttr)
                    #if x3dGT == "x3dHAnimHumanoid":
                    #    hasJoints = True
                except:
                    print("x3dGroupType not found")
                
                if x3dGT == "":
                    dagNode = aom.MFnDagNode(selList.getDependNode(0))
                    for c in range(dagNode.childCount()):
                        cNode = aom.MFnDependencyNode(dagNode.child(c))
                        if cNode.typeName == "joint":
                            newAttrs = True

                if newAttrs == True:
                    cmds.addAttr(longName='x3dGroupType', dataType='string', keyable=False)
                    cmds.setAttr(depNode.name() + '.x3dGroupType', "HAnimHumanoid", type='string', lock=True)
                    cmds.addAttr(longName='levelOfArticulation', shortName='LOA', attributeType='long', keyable=False, defaultValue=-1, minValue=-1, maxValue=4)
                    cmds.addAttr(longName="skeletalConfiguration", dataType="string")
                    
                    self.loa      = cmds.optionVar(q='rkHAnimLoa')
                    self.skConfig = cmds.optionVar(q='rkHAnimSkConfig')
                    
                    if self.loa != -1:
                        cmds.setAttr(depNode.name() + '.LOA', int(self.loa))
                        cmds.optionVar( iv=('rkHAnimLoa', -1))
                    
                    cmds.setAttr(depNode.name() + ".skeletalConfiguration", self.skConfig, type="string")
                    cmds.optionVar( sv=('rkHAnimSkConfig', 'BASIC'))
                        
                    try:
                        stk.put(depNode.name(), "x3dHAnimHumanoid.png")
                    except Exception as e:
                        print(f"Exception Type: {type(e).__name__}")
                        print(f"Exception Message: {e}")                            
                        print("Oops... Node Sticker Didn't work.")


# Creating the MEL Command for setting the a-pose
class RKSetASPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkSetASPoseForASGS"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKSetASPoseForASGS()
        
    def doIt(self, args):
        mel.eval('asGoToBuildPose bodySetup')
        mel.eval('asGoToBuildPose faceSetup')
        

# Creating the MEL Command for setting the i-pose
# Check for Existing IPose, if exists, load that, if not, do the following
class RKEstimateIPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkEstimateIPoseForASGS"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKEstimateIPoseForASGS()
        
    def doIt(self, args):
        mel.eval('source "AdvancedSkeletonFiles/Selector/biped.mel"')
        mel.eval('asGoToTPose asSelectorbiped')
        angleValue = 90.0
        if cmds.currentUnit( query=True, angle=True ) == "radians":
            angleValue = 1.5708
        #cmds.setAttr("FKShoulder_R.rotate", 0, angleValue, 0)
        #cmds.setAttr("FKShoulder_L.rotate", 0, angleValue, 0)
        cmds.setAttr("FKShoulder_R.rotateY", angleValue)
        cmds.setAttr("FKShoulder_L.rotateY", angleValue)
        mel.eval('asGoToBuildPose faceSetup')
        

# Creating the MEL Command for setting the a-pose
class RKEstimateAPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkEstimateAPoseForASGS"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKEstimateAPoseForASGS()
        
    def doIt(self, args):
        mel.eval('asGoToBuildPose bodySetup')
        mel.eval('asGoToBuildPose faceSetup')
        angleValue = 45.0
        if cmds.currentUnit( query=True, angle=True ) == "radians":
            angleValue = 0.785398
        cmds.setAttr("FKShoulder_R.rotateY", angleValue)
        cmds.setAttr("FKShoulder_L.rotateY", angleValue)
        

# Creating the MEL Command for setting the t-pose
class RKEstimateTPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkEstimateTPoseForASGS"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKEstimateTPoseForASGS()
        
    def doIt(self, args):
        mel.eval('asGoToBuildPose faceSetup')
        mel.eval('source "AdvancedSkeletonFiles/Selector/biped.mel"')
        mel.eval('asGoToTPose asSelectorbiped')
        #cmds.setAttr("FKShoulder_R.rotate", 0, 0, 0)
        #cmds.setAttr("FKShoulder_L.rotate", 0, 0, 0)
        cmds.setAttr("FKShoulder_R.rotateY", 0)
        cmds.setAttr("FKShoulder_L.rotateY", 0)
        

# Creating the MEL Command that copies the skin mesh data and binds
# it to the HAnim compatible skeleton.
#
###########################
# Must have biped.mel open
######## asGetTempDirectory, asPasteFromClipBoard, asCopyToClipBoard
# string $animationFile,$animationFilePath;
# $animationFile="ClipBoard"+$anim;
# $animationFilePath=`asGetTempDirectory`+"AdvancedSkeleton/Selector/";
# asCopyToClipBoard asSelectorbiped 0;
# asPasteFromClipBoard asSelectorbiped 0;

class RKDefPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkDefPoseForASGS"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKDefPoseForASGS()
        
    def doIt(self, args):
        # Backup current clipboard if it exists.
        cbFile, itExists = cmds.rkASBackupClipBoard()

        # Get file name without current directory.
        cFileName = mel.eval('file -q -sn -shn')
        
        # Chop off file extentions
        if len(cFileName) > 0:
            cFileName = cFileName.split('.')[0]
        
        # Get Advanced Skeleton Temp Directory and create HAnim Default Post file name.
        defPoseFile = mel.eval('asGetTempDirectory()')
        defPoseFile += "AdvancedSkeleton/Selector/" + cFileName + "_HAnimDefaultPose.ma"
        
        # Save current pose to clip board
        mel.eval('asCopyToClipBoard asSelectorbiped 0')
        
        # Copy the current clipboard to HAnim Default Pose file for this scene.
        cmds.sysFile(cbFile, copy=defPoseFile)
        
        # This is done incase something weird happens to the values when saved to disk
        # so that we know the same values will get 'Frozen' when the pose is 
        # pasted from disk.
        mel.eval('asPasteFromClipBoard asSelectorbiped 0')
        
        # Disconnect HAnim Skeleton from Advanced Skeleton, Freeze Transform and all it's children,
        # then reconnect HAnim Skeleton to Advanced Skeleton
        mel.eval('asCustomOrientJointsDisconnect()')
        humanoid = cmds.listRelatives('GameSkeletonRoot_M', p=True)

        self.swapGameSkeletonForHAnim(humanoid[0])
        
        cmds.select(humanoid, r=True)
        mel.eval('makeIdentity -apply true -t 1 -r 1 -s 1 -n 0 -pn 1 -jointOrient')
        
        ##########################################################
        # Insert More Here
        
        hJoints = cmds.listRelatives(humanoid, ad=True, type='joint')
        nJoints = []
        for j in hJoints:
            jx = cmds.getAttr(j+".translateX")
            jy = cmds.getAttr(j+".translateY")
            jz = cmds.getAttr(j+".translateZ")
            
            cmds.setAttr(j+".translateX", 0.0)
            cmds.setAttr(j+".translateY", 0.0)
            cmds.setAttr(j+".translateZ", 0.0)

            # Assuming $node is the name of your object and $matrix is your 4x4 matrix
            cmds.setAttr(j+'.offsetParentMatrix', 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, jx, jy, jz, 1.0, type='matrix')
            
            # Change the name to the expected Advanced Skeleton GameSkeleton naming convention.
            nJoint = j.removesuffix("HAnim")
            cmds.rename(j, nJoint)
            nJoints.append(nJoint)
        
        #
        ##########################################################
        
        cmds.select(nJoints)
        jSel = aom.MSelectionList()
        jSel.add(nJoints[0])
        mIter = aom.MItDependencyGraph(jSel.getDependNode(0), rkfn.kDagPose, aom.MItDependencyGraph.kDownstream, aom.MItDependencyGraph.kBreadthFirst, aom.MItDependencyGraph.kNodeLevel)
        while not mIter.isDone():
            delThisNode = False
            bPoseNode = aom.MFnDependencyNode(mIter.currentNode())
            try:
                poseValue = cmds.getAttr(bPoseNode + ".x3dHAnimPose")
                if poseValue == "iPose":
                    delThisNode = True
            except:
                pass
                
            if delThisNode == True:
                cmds.delete(bPoseNode)

            mIter.next()

        iBindPose = cmds.dagPose(bindPose=True, save=True)
        cmds.addAttr(iBindPose, longName='x3dHAnimPose', dataType="string")
        cmds.setAttr(iBindPose + ".x3dHAnimPose", "iPose", type="string")
        
        mel.eval('asCustomOrientJointsConnect()')

        # Restore clipboard from backup if it exists.
        if itExists == "True":
            cmds.rkASRestoreClipBoard()
        else:
            mel.eval('sysFile -delete "' + cbFile +'"')
            
    def swapGameSkeletonForHAnim(self, humanoidName):
        slist = aom.MSelectionList()
        slist.add(humanoidName)
        hDag = aom.MFnDagNode(slist.getDependNode(0))
        
        ########################################################
        # Not needed
        ########################################################
        # getAttr ancestorName.worldMatrix[0]
        # cmdtext = "getAttr " + hDag.name() + ".worldMatrix[0]"
        # hwMatrix = mel.eval(cmdtext)

        #Get Child Numbers
        cNum = hDag.childCount()
            
        # Traverse the Skeleton
        for i in range(cNum):
            dagChild = aom.MFnDagNode(hDag.child(i))
            if   dagChild.typeName == "joint":
                self.copyJointAndParent(hDag, dagChild)
                
        cmds.delete('GameSkeletonRoot_M')

                
                
    def copyJointAndParent(self, skParent, origJoint):
        newJName = origJoint.name() + "HAnim"

        # xform -q -ws -rp myObject;
        cmdtext = 'xform -q -ws -rp ' + origJoint.name()
        rotLoc = mel.eval(cmdtext)
        
        # Assuming $objectWorldMatrix contains the world matrix of the object itself
        # float $objectWorldMatrix[] = `getAttr objectName.worldMatrix[0]`;
        # float $pivotWorldSpace[] = `pointMatrixMult -point $pivot[0] $pivot[1] $pivot[2] -matrix $objectWorldMatrix`;

        
        #createNode "transform" -name "myNewNode" -parent "existingParentNode"
        cmds.createNode("joint", name=newJName)
        jSide  = cmds.getAttr(origJoint.name()+".side")
        jType  = cmds.getAttr(origJoint.name()+".type")
        jOType = cmds.getAttr(origJoint.name()+".otherType")
        cmds.setAttr(newJName+".side", jSide)
        cmds.setAttr(newJName+".type", jType)
        cmds.setAttr(newJName+".otherType", jOType, type="string")
        
        cmds.setAttr(newJName+".translateX", rotLoc[0])
        cmds.setAttr(newJName+".translateY", rotLoc[1])
        cmds.setAttr(newJName+".translateZ", rotLoc[2])
        
        cmds.parent(newJName, skParent.name())
        
        slist = aom.MSelectionList()
        slist.add(newJName)
        jDag = aom.MFnDagNode(slist.getDependNode(0))
        

        #Get Child Numbers
        cNum = origJoint.childCount()
            
        # Traverse the Skeleton
        for i in range(cNum):
            dagChild = aom.MFnDagNode(origJoint.child(i))
            if   dagChild.typeName == "joint":
                self.copyJointAndParent(jDag, dagChild)


# Creating the MEL Command to transfer weights to HAnim compliant 
# skelton from advanced skeleton.
class RKTransferSkinASGS(aom.MPxCommand):
    kPluginCmdName = "rkTransferSkinASGS"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKTransferSkinASGS()
        
    def doIt(self, args):
        mel.eval('asGoToBuildPose bodySetup')
        mel.eval('asGoToBuildPose faceSetup')
        mel.eval('asCustomOrientTransferSkin()')
        
        
class RKLoadDefPoseForHAnim(aom.MPxCommand):
    kPluginCmdName = "rkLoadDefPoseForHAnim"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
            
    @staticmethod
    def cmdCreator():
        return RKLoadDefPoseForHAnim()
        
    def doIt(self, args):
        # Backup current clipboard if it exists.
        cbFile, itExists = cmds.rkASBackupClipBoard()

        # Get file name without current directory.
        cFileName = mel.eval('file -q -sn -shn')
        
        # Chop off file extentions
        if len(cFileName) > 0:
            cFileName = cFileName.split('.')[0]
        
        # Get Advanced Skeleton Temp Directory and create HAnim Default Post file name.
        defPoseFile = mel.eval('asGetTempDirectory()')
        defPoseFile += "AdvancedSkeleton/Selector/" + cFileName + "_HAnimDefaultPose.ma"
        
        # Copy the current clipboard to HAnim Default Pose file for this scene.
        cmds.sysFile(defPoseFile, copy=cbFile)
        
        # This is done incase something weird happens to the values when saved to disk
        # so that we know the same values will get 'Frozen' when the pose is 
        # pasted from disk.
        mel.eval('asPasteFromClipBoard asSelectorbiped 0')
        
        # Restore clipboard from backup if it exists.
        if itExists == "True":
            cmds.rkASRestoreClipBoard()
        else:
            mel.eval('sysFile -delete "' + cbFile +'"')
        
class RKLoadIPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkLoadIPoseForASGS"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKLoadIPoseForASGS()
        
    def doIt(self, args):
        # Backup current clipboard if it exists.
        cbFile, itExists = cmds.rkASBackupClipBoard()

        # Get file name without current directory.
        cFileName = mel.eval('file -q -sn -shn')
        
        # Chop off file extentions
        if len(cFileName) > 0:
            cFileName = cFileName.split('.')[0]
        
        # Get Advanced Skeleton Temp Directory and create HAnim Default Post file name.
        iPoseFile = mel.eval('asGetTempDirectory()')
        iPoseFile += "AdvancedSkeleton/Selector/" + cFileName + "_HAnimIPose.ma"
        
        # Copy the current clipboard to HAnim Default Pose file for this scene.
        cmds.sysFile(iPoseFile, copy=cbFile)
        
        # This is done incase something weird happens to the values when saved to disk
        # so that we know the same values will get 'Frozen' when the pose is 
        # pasted from disk.
        mel.eval('asPasteFromClipBoard asSelectorbiped 0')
        
        # Restore clipboard from backup if it exists.
        if itExists == "True":
            cmds.rkASRestoreClipBoard()
        else:
            mel.eval('sysFile -delete "' + cbFile +'"')
        

class RKLoadAPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkLoadAPoseForASGS"

    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKLoadAPoseForASGS()
        
    def doIt(self, args):
        # Backup current clipboard if it exists.
        cbFile, itExists = cmds.rkASBackupClipBoard()

        # Get file name without current directory.
        cFileName = mel.eval('file -q -sn -shn')
        
        # Chop off file extentions
        if len(cFileName) > 0:
            cFileName = cFileName.split('.')[0]
        
        # Get Advanced Skeleton Temp Directory and create HAnim Default Post file name.
        aPoseFile = mel.eval('asGetTempDirectory()')
        aPoseFile += "AdvancedSkeleton/Selector/" + cFileName + "_HAnimAPose.ma"
        
        # Copy the current clipboard to HAnim Default Pose file for this scene.
        cmds.sysFile(aPoseFile, copy=cbFile)
        
        # This is done incase something weird happens to the values when saved to disk
        # so that we know the same values will get 'Frozen' when the pose is 
        # pasted from disk.
        mel.eval('asPasteFromClipBoard asSelectorbiped 0')
        
        # Restore clipboard from backup if it exists.
        if itExists == "True":
            cmds.rkASRestoreClipBoard()
        else:
            mel.eval('sysFile -delete "' + cbFile +'"')
        

class RKLoadTPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkLoadTPoseForASGS"

    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKLoadTPoseForASGS()
        
    def doIt(self, args):
        # Backup current clipboard if it exists.
        cbFile, itExists = cmds.rkASBackupClipBoard()

        # Get file name without current directory.
        cFileName = mel.eval('file -q -sn -shn')
        
        # Chop off file extentions
        if len(cFileName) > 0:
            cFileName = cFileName.split('.')[0]
        
        # Get Advanced Skeleton Temp Directory and create HAnim Default Post file name.
        tPoseFile = mel.eval('asGetTempDirectory()')
        tPoseFile += "AdvancedSkeleton/Selector/" + cFileName + "_HAnimTPose.ma"
        
        # Copy the current clipboard to HAnim Default Pose file for this scene.
        cmds.sysFile(tPoseFile, copy=cbFile)
        
        # This is done incase something weird happens to the values when saved to disk
        # so that we know the same values will get 'Frozen' when the pose is 
        # pasted from disk.
        mel.eval('asPasteFromClipBoard asSelectorbiped 0')
        
        # Restore clipboard from backup if it exists.
        if itExists == "True":
            cmds.rkASRestoreClipBoard()
        else:
            mel.eval('sysFile -delete "' + cbFile +'"')
        

class RKSaveIPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkSaveIPoseForASGS"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKSaveIPoseForASGS()
        
    def doIt(self, args):
        # Backup current clipboard if it exists.
        cbFile, itExists = cmds.rkASBackupClipBoard()

        # Get file name without current directory.
        cFileName = mel.eval('file -q -sn -shn')
        
        # Chop off file extentions
        if len(cFileName) > 0:
            cFileName = cFileName.split('.')[0]
        
        # Get Advanced Skeleton Temp Directory and create HAnim Default Post file name.
        iPoseFile = mel.eval('asGetTempDirectory()')
        iPoseFile += "AdvancedSkeleton/Selector/" + cFileName + "_HAnimIPose.ma"
        
        # Save current pose to clip board
        mel.eval('asCopyToClipBoard asSelectorbiped 0')
        
        # Copy the current clipboard to HAnim Default Pose file for this scene.
        cmds.sysFile(cbFile, copy=iPoseFile)
        
        # This is done incase something weird happens to the values when saved to disk
        # so that we know the same values will get 'Frozen' when the pose is 
        # pasted from disk.
        mel.eval('asPasteFromClipBoard asSelectorbiped 0')
        
        # Restore clipboard from backup if it exists.
        if itExists == "True":
            cmds.rkASRestoreClipBoard()
        else:
            mel.eval('sysFile -delete "' + cbFile +'"')

        

class RKSaveAPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkSaveAPoseForASGS"

    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKSaveAPoseForASGS()
        
    def doIt(self, args):
        # Backup current clipboard if it exists.
        cbFile, itExists = cmds.rkASBackupClipBoard()

        # Get file name without current directory.
        cFileName = mel.eval('file -q -sn -shn')
        
        # Chop off file extentions
        if len(cFileName) > 0:
            cFileName = cFileName.split('.')[0]
        
        # Get Advanced Skeleton Temp Directory and create HAnim Default Post file name.
        aPoseFile = mel.eval('asGetTempDirectory()')
        aPoseFile += "AdvancedSkeleton/Selector/" + cFileName + "_HAnimAPose.ma"
        
        # Save current pose to clip board
        mel.eval('asCopyToClipBoard asSelectorbiped 0')
        
        # Copy the current clipboard to HAnim Default Pose file for this scene.
        cmds.sysFile(cbFile, copy=aPoseFile)
        
        # This is done incase something weird happens to the values when saved to disk
        # so that we know the same values will get 'Frozen' when the pose is 
        # pasted from disk.
        mel.eval('asPasteFromClipBoard asSelectorbiped 0')
        
        # Restore clipboard from backup if it exists.
        if itExists == "True":
            cmds.rkASRestoreClipBoard()
        else:
            mel.eval('sysFile -delete "' + cbFile +'"')

        

class RKSaveTPoseForASGS(aom.MPxCommand):
    kPluginCmdName = "rkSaveTPoseForASGS"

    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKSaveTPoseForASGS()
        
    def doIt(self, args):
        # Backup current clipboard if it exists.
        cbFile, itExists = cmds.rkASBackupClipBoard()

        # Get file name without current directory.
        cFileName = mel.eval('file -q -sn -shn')
        
        # Chop off file extentions
        if len(cFileName) > 0:
            cFileName = cFileName.split('.')[0]
        
        # Get Advanced Skeleton Temp Directory and create HAnim Default Post file name.
        tPoseFile = mel.eval('asGetTempDirectory()')
        tPoseFile += "AdvancedSkeleton/Selector/" + cFileName + "_HAnimTPose.ma"
        
        # Save current pose to clip board
        mel.eval('asCopyToClipBoard asSelectorbiped 0')
        
        # Copy the current clipboard to HAnim Default Pose file for this scene.
        cmds.sysFile(cbFile, copy=tPoseFile)
        
        # This is done incase something weird happens to the values when saved to disk
        # so that we know the same values will get 'Frozen' when the pose is 
        # pasted from disk.
        mel.eval('asPasteFromClipBoard asSelectorbiped 0')
        
        # Restore clipboard from backup if it exists.
        if itExists == "True":
            cmds.rkASRestoreClipBoard()
        else:
            mel.eval('sysFile -delete "' + cbFile +'"')
        

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
        cmds.setAttr(node + '.x3dGroupType', "Collision", type='string', lock=True)
        
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
        cmds.setAttr(node + '.x3dGroupType', "Group", type='string', lock=True)


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
        cmds.setAttr(node + '.x3dGroupType', "Switch", type='string', lock=True)


# Creating the MEL Command for the RawKee's Command to set a transform node to Billboard mode
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
                    cmds.setAttr(node + '.x3dGroupType', "Billboard", type='string', lock=True)


####################################################################
# X3D JSON Loader MPxCommand, indented to for used by RawKee 
# developers to test importing of X3D nodes. Can only be run from
# the MEL/Python command line.
####################################################################
class RKX3DAuxLoader(aom.MPxCommand):
    kPluginCmdName = "rkX3DAuxLoader"
    
    def __init__(self):
        aom.MPxCommand.__init__(self)
        
    @staticmethod
    def cmdCreator():
        return RKX3DAuxLoader()
        
    def doIt(self, args):
        # Grab Main Window
        mayaWin = self.mayaMainWindow()

        auxFilePath = RKOrganizer.__file__.replace("\\", "/").rsplit("/", 1)[0]
        auxFilePath += "/auxilary"

        x3dfilters = "X3D JSON (*.x3dj);;X3D JSON (*.json)"
        
        fullPath = auxFilePath
        fullPath, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(mayaWin, QtCore.QObject.tr("RawKee - Import X3D JSON File"), auxFilePath, QtCore.QObject.tr(x3dfilters))
        
        rko = RKOrganizer.RKOrganizer()
        loadedFile = None
        
        try:
            loadedFile = rko.rkio.jsonLoader.loadX3DJSON(fullPath)
        except:
            print("JSON Load Failed... " + fullPath)
        
        sceneLoaded = True
        try:
            scene = loadedFile["X3D"]["Scene"]
        except:
            sceneLoaded = False
            
        if sceneLoaded == True:
            rko.rkio.jsonLoader.processBranchForMaya(scene)
        else:
            print("X3D Scene not found in file")
        
        del rko


    # Function to get Maya Main Window Widget
    def mayaMainWindow(self):
        '''
        Using Qt and Shiboken to grab a pointer to the main Maya window and 
        return it as a QWidget
        '''
        mainWindowPtr = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mainWindowPtr), QtWidgets.QMainWindow)
        



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
        



