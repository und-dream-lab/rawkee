import sys
import maya.api.OpenMaya as aom
import maya.OpenMayaUI   as omui
import maya.cmds         as cmds
import maya.mel          as mel
import os
import signal
import subprocess        as sp

from rawkee import RKOrganizer
from rawkee.RKUtils import *

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
        
        self.rko = None #RKOrganizer.RKOrganizer()
        
        self.server = None 
        
        self.curDir   = ""
        self.fileName = ""
        self.dirPath  = ""
        self.fullPath = ""
        self.selectedFilter = ""
        # self.x3dfilters = "X3D XML (*.x3d);;X3D Classic (*.x3dv);;X3D Binary (*.x3db);;X3D Enhanced Binary (*.x3de);;X3D JSON (*.x3dj);;X3D JSON (*.json);;VRML97 (*.wrl);;Web3D Files (*.x3d *.x3db *.x3de *.x3dj *.x3dv *.json *.wrl)"
        self.x3dfilters = "X3D XML (*.x3d);;X3D Classic (*.x3dv);;VRML 97 (*.wrl);;X3D JSON (*.x3dj);;X3D JSON (*.json);;Web3D Files (*.x3d *.x3dv *.wrl *.x3dj *.json)"
        
        # Setup the main 'RawKee X3D' plugin menu
        self.rkMenuName ="rawkee_menu"

        self.rawKeeMenu = ""#cmds.menu(label = 'RawKee (X3D)', tearOff=True)#QMenu("RawKee (X3D)", self.mayaWin)
        #self.rawKeeMenu.setTearOffEnabled(True)
        
        # Find the length of actions in the Menu Bar so that the "RawKee (X3D)" menu can be inserted before the main Maya "Help" menu.
        #mbLen = len(self.mayaWin.menuBar().actions())
        
        # Insert RawKee X3D Menu before the help Menu.
        #self.mayaWin.menuBar().insertMenu(self.mayaWin.menuBar().actions()[mbLen-1], self.rawKeeMenu) 

        # TODO: Change Comment - Maya Main Window 'File' menu actions
        #self.x3dSceneNodes        = ""#QMenu("Add Scene Nodes", self.mayaWin)
        #self.x3dGroupingNodes     = ""#QMenu("Add Grouping Nodes", self.mayaWin)
        #self.x3dPrimitivesNodes   = ""#QMenu("Add Primitives", self.mayaWin)
        #self.x3dAudioNodes        = ""#QMenu("Add Audio Nodes", self.mayaWin)
        #self.x3dNetworkingNodes   = ""#QMenu("Add Networking Nodes", self.mayaWin)
        #self.x3dEventUtilityNodes = ""#QMenu("Add Event Utility Nodes", self.mayaWin)

        #self.x3dMetadataNodes     = ""#QMenu("Add Metadata Nodes", self.mayaWin)
        #self.x3dSensorNodes       = ""#QMenu("Add Sensor Nodes", self.mayaWin)
        #self.x3dAnimationNodes    = ""#QMenu("Add Animation Nodes", self.mayaWin)
        #self.x3dUserDNodes        = ""#QMenu("Add User-Defined Nodes", self.mayaWin)
	
        #self.x3dExport            = ""#QAction("Export X3D Files", self.mayaWin)
        #self.x3dSelExport         = ""#QAction("Export X3D Files", self.mayaWin)
        ####self.x3dExport.triggered.connect(self.activateExportFunctions)
        #self.x3dExportOpt         = ""#QAction(QIcon(":menu_options.png"), "BOX", self.mayaWin)
        #self.x3dSelExportOpt      = ""#QAction(QIcon(":menu_options.png"), "BOX", self.mayaWin)
        ####self.x3dExportOpt.setIcon()

        #self.x3dImport            = ""#QAction("Import X3D Files", self.mayaWin)
        ####self.x3dImport.triggered.connect(self.activateImportFunctions)
        #self.x3dImportOpt         = ""#QAction(QIcon(":menu_options.png"), "BOX", self.mayaWin)
        ####self.x3dImportOpt.setIcon(QIcon.fromTheme(SP_TitleBarMaxButton))
        #self.x3dEWA               = ""#QWidgetAction(self.mayaWin)
        #self.bGroup               = ""#QButtonGroup(self.mayaWin)
        #self.x3dEBut              = ""#QPushButton("Export X3D Files", self.mayaWin)
        #self.x3dEBO               = ""#QPushButton(QIcon(":menu_options.png"),"", self.mayaWin)
        ####self.bGroup.addButton(self.x3dEBut)
        ####self.bGroup.addButton(self.x3dEBO)
        ####self.x3dEWA.setDefaultWidget(self.x3dEBut) #.setDefaultWidget(self.bGroup)
        
        #   self.launchServer()

        #Populate the RawKee X3D Menu
        self.addRawKeeMenu()
        
    def __del__(self):
        self.removeRawKeeMenu()
        self.termServer()
        
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

        cmds.menuItem(label='RawKee Tutorials')#self.rawKeeMenu.addAction("RawKee Tutorials")# -command "showX3DTutorials";
        cmds.menuItem(label='RawKee Documentation')#self.rawKeeMenu.addAction("RawKee Documentation")# -command "showX3DTutorials";

        cmds.menuItem(divider=True, dividerLabel='File - Import/Export' )                                                           #self.rawKeeMenu.addSection("File - Import/Export")
        self.x3dExport       = cmds.menuItem(label='Export All - X3D',      command='maya.cmds.rkX3DExport()')
        self.x3dExportOpt    = cmds.menuItem(image=':menu_options.png',     command='maya.cmds.rkX3DExportOp()',    optionBox=True) #self.rawKeeMenu.addAction(self.x3dExportOpt)
        self.x3dSelExport    = cmds.menuItem(label='Export Selected - X3D', command='maya.cmds.rkX3DSelExport()')
        self.x3dSelExportOpt = cmds.menuItem(image=':menu_options.png',     command='maya.cmds.rkX3DSelExportOp()', optionBox=True) #self.rawKeeMenu.addAction(self.x3dExportOpt)
        self.x3dImport       = cmds.menuItem(label='Import X3D Files',      command='maya.cmds.rkX3DImport()')                      #self.rawKeeMenu.addAction(self.x3dImport)
        self.x3dImportOpt    = cmds.menuItem(image=':menu_options.png',     command='maya.cmds.rkX3DImportOp()',    optionBox=True) #self.rawKeeMenu.addAction(self.x3dImportOpt)
#        self.x3dExport.addAction("Export Scene Prep")# -c "x3dPrepareSceneForExport";

        cmds.menuItem(divider=True, dividerLabel='Create X3D Nodes')                                   
        cmds.menuItem(label='Add Scene Nodes', subMenu=True)                      
        cmds.menuItem(label='Viewpoint')                        # -c "createX3DViewpoints";
        cmds.menuItem(label='NavigationInfo')                   # -c "createX3DNavigationInfos";
        cmds.menuItem(label='WorldInfo')                        # -c "createX3DWorldInfos";
        cmds.menuItem(label='DirectionalLight')                 # -c "createX3DDirectionalLights";
        cmds.menuItem(label='SpotLight')                        # -c "createX3DSpotLights";
        cmds.menuItem(label='PointLight')                       # -c "createX3DPointLights";
        
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(label='Add Grouping Nodes', subMenu=True) 
        cmds.menuItem(label='Transform', command='maya.cmds.createNode("transform")')                        # -c "createX3DTransforms";
        cmds.menuItem(label='Group',     command='maya.cmds.rkAddGroup()')                            # -c "createX3DGroups";
        cmds.menuItem(label='Switch',    command='maya.cmds.rkAddSwitch()') # -c "createX3DSwitches";
        cmds.menuItem(label='Collision', command='maya.cmds.rkAddCollision()')# -c "createX3DCollisions";
        cmds.menuItem(label='LOD',       command='mel.eval("LevelOfDetailGroup")') # -c "createX3DlodGroup";
        cmds.menuItem(label='Billboard', command='maya.cmds.rkSetAsBillboard()')                        # -c "createX3DBillboards";
        
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(label='Add Primitive Nodes', subMenu=True)
        cmds.menuItem(label='Box')                              #  -c "createX3DBoxes";
        cmds.menuItem(label='Cone')                             #   -c "createX3DCones";
        cmds.menuItem(label='Cylinder')                         #  -c "createX3DCylinders";
        cmds.menuItem(label='Sphere')                           # -c "createX3DSpheres";
        cmds.menuItem(label='IndexedFaceSet')                   #  -c "createX3DIndexedFaceSets";
	
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(label='Add Audio Nodes', subMenu=True) 
        cmds.menuItem(label='AudioClip', command='maya.cmds.createNode("audio")')#  -c "createX3DAudioClips";
        cmds.menuItem(label='Sound', command='maya.cmds.createNode("x3dSound")') #  -c "createX3DSounds";
	
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(label='Add Networking Nodes', subMenu=True)
        cmds.menuItem(label='Anchor')                           #  -c "createX3DAnchors";
        cmds.menuItem(label='Inline')                           #  -c "createX3DInlines";
        cmds.menuItem(label='LoadSensor')                       #  -c "createX3DLoadSensors";
	
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(label='Add Event Utility Nodes', subMenu=True)
        cmds.menuItem(label='BooleanFilter')                         #  -c "createX3DBooleanFilters";
        cmds.menuItem(label='BooleanSequencer')                      #  -c "createX3DBooleanSequencers";
        cmds.menuItem(label='BooleanToggle')                         #  -c "createX3DBooleanToggle";
        cmds.menuItem(label='BooleanTrigger')                        #  -c "createX3DBooleanTrigger";
        cmds.menuItem(label='IntegerSequencer')                      #  -c "createX3DIntegerSequencer";
        cmds.menuItem(label='IntegerTrigger')                        #  -c "createX3DIntegerTrigger";
        cmds.menuItem(label='TimeTrigger')                           #  -c "createX3DTimeTrigger";
        
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(label='Add Metadata Nodes', subMenu=True)
        cmds.menuItem(label='MetadataDouble')                        # -c "createX3DMetadataDoubles";
        cmds.menuItem(label='MetadataFloat')                         # -c "createX3DMetadataFloats";
        cmds.menuItem(label='MetadataInteger')                       # -c "createX3DMetadataIntegers";
        cmds.menuItem(label='MetadataSet')                           # -c "createX3DMetadataSets";
        cmds.menuItem(label='MetadataString')                        # -c "createX3DMetadataStrings";
	
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(label='Add Sensor Nodes', subMenu=True)
        cmds.menuItem(label='CylinderSensor')                        # -c "createX3DCylinderSensors";
        cmds.menuItem(label='KeySensor')                             # -c "createX3DKeySensors";
        cmds.menuItem(label='PlaneSensor')                           # -c "createX3DPlaneSensors";
        cmds.menuItem(label='ProximitySensor')                       # -c "createX3DProximitySensors";
        cmds.menuItem(label='SphereSensor')                          # -c "createX3DSphereSensors";
        cmds.menuItem(label='StringSensor')                          # -c "createX3DStringSensors";
        cmds.menuItem(label='TimeSensor')                            # -c "createX3DTimeSensors";
        cmds.menuItem(label='TouchSensor')                           # -c "createX3DTouchSensors";
        cmds.menuItem(label='VisibilitySensor')#                     # -c "createX3DVisibilitySensors";
        cmds.menuItem(label='GamepadSensor')                         # -c "createX3DGamepadSensors";
	
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(label='Add Animation Nodes', subMenu=True)
        cmds.menuItem(label='ColorInterpolator')                     # -c "createX3DColorInterpolators";
        cmds.menuItem(label='CoordinateInterpolator')                # -c "createX3DCoordinateInterpolators";
        cmds.menuItem(label='NormalInterpolator')                    # -c "createX3DNormalInterpolators";
        cmds.menuItem(label='OrientationInterpolator')               # -c "createX3DOrientationInterpolators";
        cmds.menuItem(label='PositionInterpolator')                  # -c "createX3DPositionInterpolators";
        cmds.menuItem(label='ScalarInterpolator')                    # -c "createX3DScalarInterpolators";
	
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(label='Add User Defined Nodes', subMenu=True)
        cmds.menuItem(label='Script')                                # -c "createX3DScripts";
	
        #	menuItem -subMenu true -label "Add Geospatial Nodes" -allowOptionBoxes true;
	
        #	menuItem -subMenu true -label "Add DIS Nodes" -allowOptionBoxes true;

        #--------------------------------------------------------------------
        # Finishing off the  X3D Plug-in menu
        #--------------------------------------------------------------------
        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(divider=True, dividerLabel='RawKee Editors')
        cmds.menuItem(label='X3D Interaction Editor')                # -command "showX3DIEditor";
        cmds.menuItem(label='X3D Character Editor')                  # -command "x3dCharacterEditor";
        cmds.menuItem(label='X3D Animation Editor')                  # -command "x3dAnimationEditor";

        cmds.setParent(self.rkMenuName, menu=True)
        cmds.menuItem(divider=True, dividerLabel='Texture Utility Commands')
        cmds.menuItem(label='Set All MultiTexture Modes: Default')   # -c ("x3dSetAllSingleTextureModes 0");
        cmds.menuItem(label='Set All MultiTexture Modes: Replace')   # -c ("x3dSetAllSingleTextureModes 1");
        cmds.menuItem(label='Set All MultiTexture Modes: Modulate')  # -c ("x3dSetAllSingleTextureModes 2");
        cmds.menuItem(label='Set All MultiTexture Modes: Add')       # -c ("x3dSetAllSingleTextureModes 3");
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Make All Textures PixelTextures')       # -c ("x3dSetAllTexturesPixel");
        cmds.menuItem(label='Make All Textures ImageTextures')       # -c ("x3dSetAllTexturesFile");
        cmds.menuItem(divider=True, dividerLabel='Code Repositories')
        cmds.menuItem(label='RawKee GitHub Python Repo')
        cmds.menuItem(divider=True, dividerLabel='Websites')
        cmds.menuItem(label='Univ. of North Dakota - DREAM Lab')
        cmds.menuItem(label='Web3D Consortium')
        cmds.menuItem(label='Metaverse Standards Forum')
        ###################################################
    
    
    
    # Destroy "RawKee (X3D)" - main plugin menu
    def removeRawKeeMenu(self):
        '''
        Remove and destroy the RawKee Primary Menu
        '''
        #self.mayaWin.menuBar().removeAction(self.rawKeeMenu.menuAction())
        if  cmds.menu(self.rkMenuName,  label = 'RawKee (X3D)', p='MayaWindow') != 0:
            cmds.deleteUI(cmds.menu(self.rkMenuName,  label = 'RawKee (X3D)', e=1, dai=1))
            cmds.deleteUI(self.rkMenuName)     
            cmds.refresh()
    
    
    
    # Export Function
    def activateExportFunctions(self):
        print("RawKee X3D Export")
        
        if self.curDir == "":
            self.curDir = cmds.internalVar(userAppDir=True)

        self.dirPath = self.curDir
        self.fullPath = self.dirPath
        self.fullPath, self.selectedFilter = QtWidgets.QFileDialog.getSaveFileName(self.mayaWin, QtCore.QObject.tr("RawKee - Export File As..."), self.fullPath, QtCore.QObject.tr(self.x3dfilters))
        
        if self.fullPath != None and self.fullPath != "":
        
            #self.rko.processExportFile(self.fullPath, self.selectedFilter)
        
            #From RKUtils.py
            setX3DProcTreeTrue()
        
            #From RKUtils.py
            #processNonFileTextures()
        
            self.rko = RKOrganizer.RKOrganizer()
        
            #Setup Basic File Path Info
            self.rko.fileName = self.fullPath
            idx = self.rko.fileName.rfind("/")
            self.rko.localPath = self.rko.fileName[:idx+1]
            print(self.rko.localPath)
            
            
            ###############################################
            #x3dEO.setFileSax3dWriter(tempFile);
            self.rko.rkio.fullPath = self.rko.fileName
            
            #x3dEO.setExportStyle(filter());
            self.rko.setExportStyle(self.selectedFilter)

            # Not Using - Options set differently from C++ file chooser ## x3dEO.optionsString.operator =(optionsString);
            
            #x3dEO.organizeExport();
            self.rko.organizeExport()
            
            ###############################################
            # These aren't being used in the Python version
            # at least not at the moment.
            # - Now default profileType is "Full"
            # - X3D Version defaults to "4.0", or whatever the
            #   current x3d.py module supports.
            # - No addition components are required.
            ###############################################
            # C++ Code
            ###############################################
            # x3dEO.sax3dw.profileType.set("Immersive");	
            # x3dEO.sax3dw.version.set("3.1");
            # x3dEO.setAdditionalComps();
            
            self.rko.rkio.comments.clear()
            self.rko.rkio.comments.append(self.pVersion)
            self.rko.rkio.commentNames.clear()
            self.rko.rkio.commentNames.append("created_with")
            
            self.rko.rkio.startDocument()
            self.rko.exportAll()
            self.rko.writeRoutes()
            self.rko.rkio.endDocument()
            
        else:
            print("User Cancelled file selection.")
        
        del self.rko
        
        
        
    # Export Function
    def activateSelExportFunctions(self):
        print("RawKee X3D Selected Export")


    # Export Options Function
    def activateExportOptions(self):
        print("TODO: Implement Export Options Window")
        
    
    # Export Options Function
    def activateSelExportOptions(self):
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
        print("TODO: Implement Import Options Window")
    
    # File Import/Export Options Window
    def activateFOptsDialog(self):
        pass
        
        

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
                
        

