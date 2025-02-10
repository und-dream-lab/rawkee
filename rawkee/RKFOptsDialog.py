try:
    #Qt5
    from PySide2           import QtCore
    from PySide2           import QtWidgets
    from PySide2           import QtGui
    from PySide2           import QMenu
    from PySide2.QtWidgets import QAction
    from PySide2.QtWidgets import QMenu
    from PySide2.QtCore    import QUrl
    from PySide2.QtQui     import QDesktopServices

    from shiboken2         import wrapInstance

except:
    #Qt6
    from PySide6           import QtCore
    from PySide6           import QtWidgets
    from PySide6           import QtGui
    from PySide6.QtGui     import QAction
    from PySide6.QtWidgets import QMenu
    from PySide6.QtCore    import QUrl
    from PySide6.QtGui     import QDesktopServices
    
    from shiboken6         import wrapInstance

import sys

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds

import os

#######################################
# Don't remember why this is here
#######################################
# import inspect
# import maya.standalone as mst
# print(inspect.getfile(mst))

def mayaMainWindow():
    mainWindowPtr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPtr), QtWidgets.QWidget)
    
class RKFOptsDialog(QtWidgets.QDialog):
    def __init__(self, parent=mayaMainWindow(), dialogTitle="X3D"):
        super(RKFOptsDialog, self).__init__(parent)
        self.dialogTitle = dialogTitle
        self.setWindowTitle(self.dialogTitle)
        self.setMinimumSize(600,400)
        self.setFixedWidth(800)

        #On macOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)
            
 #       self.createLayout()
        self.createWidgets()
            
    def createWidgets(self):
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        
        contentWidget = QtWidgets.QWidget()
        contentLayout = QtWidgets.QVBoxLayout(contentWidget)
        
        if self.dialogTitle == "X3D Export Options":
            contentLayout = self.buildX3DExportPanel(contentLayout)

            scrollArea.setWidget(contentWidget)
            dialogLayout = QtWidgets.QVBoxLayout()
            dialogLayout.addWidget(scrollArea)
            
            buttonRow = QtWidgets.QHBoxLayout()
            self.buttonSpace = QtWidgets.QLabel(" ")
            self.buttonSpace.setFixedWidth(400)
            self.buttonSpace.setAlignment(QtCore.Qt.AlignRight)
            self.cancelButton = QtWidgets.QPushButton("Save Options and Close")
            self.exportButton = QtWidgets.QPushButton("Save Options and Export")
            
            buttonRow.addWidget(self.buttonSpace)
            buttonRow.addWidget(self.cancelButton)
            buttonRow.addWidget(self.exportButton)
            dialogLayout.addLayout(buttonRow)

            self.setLayout(dialogLayout)
            
        elif self.dialogTitle == "X3D Export Selected Options":
            pass
        elif self.dialogTitle == "X3D Import Options":
            pass
        elif self.dialogTitle == "Castle Export All - Options":
            pass
        elif self.dialogTitle == "Castle Export Selected - Options":
            pass



    def buildX3DExportPanel(self, layout):
        #layout = QtWidgets.QVBoxLayout()

        # Option One
        layoutOne = QtWidgets.QHBoxLayout()
        self.mayaTexLabel = QtWidgets.QLabel("     Procedural Textures - Export as:")
        self.mayaTexLabel.setAlignment(QtCore.Qt.AlignRight)
        self.mayaTexLabel.setFixedWidth(250)
        self.comboMayaTexOptions = QtWidgets.QComboBox()
        self.comboMayaTexOptions.addItems(["ImageTexture", "PixelTexture"])
        self.comboMayaTexOptions.setFixedWidth(200)
        
        layoutOne.addWidget(self.mayaTexLabel)
        layoutOne.addWidget(self.comboMayaTexOptions)
        layoutOne.addStretch()
        
        # Option Two
        layoutTwo = QtWidgets.QHBoxLayout()
        self.mayaTexFileLabel = QtWidgets.QLabel("     File Textures - Export as:")
        self.mayaTexFileLabel.setAlignment(QtCore.Qt.AlignRight)
        self.mayaTexFileLabel.setFixedWidth(250)
        self.comboMayaTexFileOptions = QtWidgets.QComboBox()
        self.comboMayaTexFileOptions.addItems(["ImageTexture", "PixelTexture"])
        self.comboMayaTexFileOptions.setFixedWidth(200)
        
        layoutTwo.addWidget(self.mayaTexFileLabel)
        layoutTwo.addWidget(self.comboMayaTexFileOptions)
        layoutTwo.addStretch()
        
        # Option Three
        layoutThree = QtWidgets.QHBoxLayout()
        self.mayaLayeredLabel = QtWidgets.QLabel("     Layered Textures - Export as:")
        self.mayaLayeredLabel.setAlignment(QtCore.Qt.AlignRight)
        self.mayaLayeredLabel.setFixedWidth(250)
        self.comboMayaLayeredOptions = QtWidgets.QComboBox()
        self.comboMayaLayeredOptions.addItems(["MultiTexture", "ImageTexture", "PixelTexture"])
        self.comboMayaLayeredOptions.setFixedWidth(200)
        
        layoutThree.addWidget(self.mayaLayeredLabel)
        layoutThree.addWidget(self.comboMayaLayeredOptions)
        layoutThree.addStretch()
        
        # Option Three Alpha
        layoutThreeAlpha = QtWidgets.QHBoxLayout()
        self.texFileFormatLabel = QtWidgets.QLabel("     2D Texture File Format:")
        self.texFileFormatLabel.setAlignment(QtCore.Qt.AlignRight)
        self.texFileFormatLabel.setFixedWidth(250)
        self.texFileFormatOptions = QtWidgets.QComboBox()
        self.texFileFormatOptions.addItems(["PNG - Portable Netowrk Graphics", "WebP - Web Picture", "JPG - Joint Photographic Experts Group"])
        self.texFileFormatOptions.setFixedWidth(250)
        
        layoutThreeAlpha.addWidget(self.texFileFormatLabel)
        layoutThreeAlpha.addWidget(self.texFileFormatOptions)
        layoutThreeAlpha.addStretch()
        
        
        # Option Three Bravo
        layoutThreeBravo = QtWidgets.QHBoxLayout()
        self.movFileFormatLabel = QtWidgets.QLabel("     Movie/Video File Format:")
        self.movFileFormatLabel.setAlignment(QtCore.Qt.AlignRight)
        self.movFileFormatLabel.setFixedWidth(250)
        self.movFileFormatOptions = QtWidgets.QComboBox()
        self.movFileFormatOptions.addItems(["MP4 with H.264", "WebM with VP9", "Ogg with Theora/Vorbis"])
        self.movFileFormatOptions.setFixedWidth(250)
        
        layoutThreeBravo.addWidget(self.movFileFormatLabel)
        layoutThreeBravo.addWidget(self.movFileFormatOptions)
        layoutThreeBravo.addStretch()
        
        
        # Option Three Charlie
        layoutThreeCharlie = QtWidgets.QHBoxLayout()
        self.audFileFormatLabel = QtWidgets.QLabel("     Audio File Format:")
        self.audFileFormatLabel.setAlignment(QtCore.Qt.AlignRight)
        self.audFileFormatLabel.setFixedWidth(250)
        self.audFileFormatOptions = QtWidgets.QComboBox()
        self.audFileFormatOptions.addItems(["MP3 - MPEG Audio Layer 3", "AAC - Advanced Audio Coding", "Ogg Vorbis"])
        self.audFileFormatOptions.setFixedWidth(250)
        
        layoutThreeCharlie.addWidget(self.audFileFormatLabel)
        layoutThreeCharlie.addWidget(self.audFileFormatOptions)
        layoutThreeCharlie.addStretch()
        
        
        # Option Four
        layoutFour = QtWidgets.QHBoxLayout()
        spacer4 = QtWidgets.QLabel(" ")
        spacer4.setAlignment(QtCore.Qt.AlignLeft)
        spacer4.setFixedWidth(80)
        self.media2FileLabel = QtWidgets.QLabel("Consolidate Media Files (write/overwrite) in RawKee Project Folder:")
        self.media2FileLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.media2FileLabel.setFixedWidth(400)

        layoutFour.addWidget(spacer4)
        layoutFour.addWidget(self.media2FileLabel)
        layoutFour.addStretch()
        
        # Option FourB
        layoutFourB = QtWidgets.QHBoxLayout()
        spacer4B = QtWidgets.QLabel(" ")
        spacer4B.setAlignment(QtCore.Qt.AlignRight)
        spacer4B.setFixedWidth(150)
        self.texture2FileCheckBox = QtWidgets.QCheckBox("2D Textures")
        self.movie2FileCheckBox   = QtWidgets.QCheckBox("Movie Textures")
        self.audio2FileCheckBox   = QtWidgets.QCheckBox("Audio Clips")
        
        layoutFourB.addWidget(spacer4B)
        layoutFourB.addWidget(self.texture2FileCheckBox)
        layoutFourB.addWidget(self.movie2FileCheckBox)
        layoutFourB.addWidget(self.audio2FileCheckBox)
        layoutFourB.addStretch()
        
        # Option Five
        layoutFive = QtWidgets.QHBoxLayout()
        adjTexSizeLabel = QtWidgets.QLabel("Adjust Texture Size:")
        adjTexSizeLabel.setAlignment(QtCore.Qt.AlignRight)
        adjTexSizeLabel.setFixedWidth(250)
        layoutFive.addWidget(adjTexSizeLabel)
#        layoutFive.addStretch()
        
        # Option FiveB
        layoutFiveB = QtWidgets.QHBoxLayout()
        spacer5B = QtWidgets.QLabel(" ")
        spacer5B.setAlignment(QtCore.Qt.AlignRight)
        spacer5B.setFixedWidth(180)
        self.adjTexCheckBox = QtWidgets.QCheckBox()
        self.adjTexCheckBox.setFixedWidth(20)
        
        layoutFiveB.addWidget(spacer5B)
        layoutFive.addWidget(self.adjTexCheckBox)
#        layoutFiveB.addStretch()
        
        # Option Six
        layoutSix = QtWidgets.QHBoxLayout()
        spacer6 = QtWidgets.QLabel(" ")
        spacer6.setAlignment(QtCore.Qt.AlignRight)
        spacer6.setFixedWidth(180)
        
        self.adjTexWidthLabel = QtWidgets.QLabel("Width:")
        self.adjTexWidthLabel.setAlignment(QtCore.Qt.AlignRight)
        self.adjTexWidthLabel.setFixedWidth(50)
        self.textureWidth = QtWidgets.QLineEdit()
        self.textureWidth.setAlignment(QtCore.Qt.AlignLeft)
        self.textureWidth.setFixedWidth(50)
        intVal = QtGui.QIntValidator()
        intVal.setRange(1,8192)
        self.textureWidth.setValidator(intVal)
        
        self.adjTexHeightLabel = QtWidgets.QLabel("Height:")
        self.adjTexHeightLabel.setAlignment(QtCore.Qt.AlignRight)
        self.adjTexHeightLabel.setFixedWidth(50)
        self.textureHeight = QtWidgets.QLineEdit()
        self.textureHeight.setAlignment(QtCore.Qt.AlignLeft)
        self.textureHeight.setFixedWidth(50)
        self.textureHeight.setValidator(intVal)
        
        layoutFive.addWidget(self.adjTexWidthLabel)
        layoutFive.addWidget(self.textureWidth)
        layoutFive.addWidget(self.adjTexHeightLabel)
        layoutFive.addWidget(self.textureHeight)
        layoutFive.addStretch()
        
        # Option Seven
        layoutSeven = QtWidgets.QHBoxLayout()
        self.regOptsLabel = QtWidgets.QLabel("Include Nodes for Export:")
        self.regOptsLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.regOptsLabel.setFixedWidth(300)
        
        spacer7 = QtWidgets.QLabel(" ")
        spacer7.setAlignment(QtCore.Qt.AlignLeft)
        spacer7.setFixedWidth(80)
        
        layoutSeven.addWidget(spacer7)
        layoutSeven.addWidget(self.regOptsLabel)
        layoutSeven.addStretch()
        
        # Option Eight and Nine
        layoutEight = QtWidgets.QHBoxLayout()
        spacer8 = QtWidgets.QLabel(" ")
        spacer8.setAlignment(QtCore.Qt.AlignLeft)
        spacer8.setFixedWidth(150)
        
        layoutNine = QtWidgets.QHBoxLayout()
        spacer9 = QtWidgets.QLabel(" ")
        spacer9.setAlignment(QtCore.Qt.AlignLeft)
        spacer9.setFixedWidth(150)
        
        self.exCameras  = QtWidgets.QCheckBox("Maya Cameras as X3D Viewpoints")
        self.exLights   = QtWidgets.QCheckBox("Maya Lights as X3D Lights")
        self.exCameras.setFixedWidth(250)
        self.exLights.setFixedWidth(250)
        
        self.exSounds   = QtWidgets.QCheckBox("RawKee Sound as X3D Sound")
        self.exMetadata = QtWidgets.QCheckBox("RawKee Metadata as X3D Metadata")
        self.exSounds.setFixedWidth(250)
        self.exMetadata.setFixedWidth(250)
        
        layoutEight.addWidget(spacer8)
        layoutEight.addWidget(self.exCameras)
        layoutEight.addWidget(self.exLights)
        layoutEight.addStretch()
        
        layoutNine.addWidget(spacer9)
        layoutNine.addWidget(self.exSounds)
        layoutNine.addWidget(self.exMetadata)
        layoutNine.addStretch()
        
        
        # Option Ten
        layoutTen = QtWidgets.QHBoxLayout()
        self.rpdLabel = QtWidgets.QLabel("RawKee Project Directory:")
        self.rpdLabel.setAlignment(QtCore.Qt.AlignRight)
        self.rpdLabel.setFixedWidth(250)
        
        self.rkProjectDir = QtWidgets.QLineEdit()
        self.rkProjectDir.setAlignment(QtCore.Qt.AlignLeft)
        self.rkProjectDir.setFixedWidth(300)
        
        self.rkPrjDirButton = QtWidgets.QPushButton()
        self.rkPrjDirButton.setIcon(QtGui.QIcon(":folder-open.png"))
        self.rkPrjDirButton.setContentsMargins(0,0,0,0)
        self.rkPrjDirButton.setFixedSize(20,20)
        
        layoutTen.addWidget(self.rpdLabel)
        layoutTen.addWidget(self.rkProjectDir)
        layoutTen.addWidget(self.rkPrjDirButton)
        layoutTen.addStretch()
        
        
        # Option Eleven
        layoutEleven = QtWidgets.QHBoxLayout()
        self.bDomLabel = QtWidgets.QLabel("Base Web Domain:")
        self.bDomLabel.setAlignment(QtCore.Qt.AlignRight)
        self.bDomLabel.setFixedWidth(250)
        
        self.rkBaseDomain = QtWidgets.QLineEdit()
        self.rkBaseDomain.setAlignment(QtCore.Qt.AlignLeft)
        self.rkBaseDomain.setFixedWidth(300)
        
        
        layoutEleven.addWidget(self.bDomLabel)
        layoutEleven.addWidget(self.rkBaseDomain)
        layoutEleven.addStretch()
        
        
        # Option Twelve
        layoutTwelve = QtWidgets.QHBoxLayout()
        self.basePathLabel = QtWidgets.QLabel("Base Path:")
        self.basePathLabel.setAlignment(QtCore.Qt.AlignRight)
        self.basePathLabel.setFixedWidth(250)
        
        self.rkBasePath = QtWidgets.QLineEdit()
        self.rkBasePath.setAlignment(QtCore.Qt.AlignLeft)
        self.rkBasePath.setFixedWidth(300)
        
        
        layoutTwelve.addWidget(self.basePathLabel)
        layoutTwelve.addWidget(self.rkBasePath)
        layoutTwelve.addStretch()
        
        
        # Option Thirteen
        layoutThirteen = QtWidgets.QHBoxLayout()
        self.imagePathLabel = QtWidgets.QLabel("Image Path:")
        self.imagePathLabel.setAlignment(QtCore.Qt.AlignRight)
        self.imagePathLabel.setFixedWidth(250)
        
        self.rkImagePath = QtWidgets.QLineEdit()
        self.rkImagePath.setAlignment(QtCore.Qt.AlignLeft)
        self.rkImagePath.setFixedWidth(300)
        
        
        layoutThirteen.addWidget(self.imagePathLabel)
        layoutThirteen.addWidget(self.rkImagePath)
        layoutThirteen.addStretch()
        
        
        # Option Fourteen
        layoutFourteen = QtWidgets.QHBoxLayout()
        self.audioPathLabel = QtWidgets.QLabel("Audio Path:")
        self.audioPathLabel.setAlignment(QtCore.Qt.AlignRight)
        self.audioPathLabel.setFixedWidth(250)
        
        self.rkAudioPath = QtWidgets.QLineEdit()
        self.rkAudioPath.setAlignment(QtCore.Qt.AlignLeft)
        self.rkAudioPath.setFixedWidth(300)
        
        
        layoutFourteen.addWidget(self.audioPathLabel)
        layoutFourteen.addWidget(self.rkAudioPath)
        layoutFourteen.addStretch()
        
        
        # Option Fifteen
        layoutFifteen = QtWidgets.QHBoxLayout()
        self.inlinePathLabel = QtWidgets.QLabel("Inline Path:")
        self.inlinePathLabel.setAlignment(QtCore.Qt.AlignRight)
        self.inlinePathLabel.setFixedWidth(250)
        
        self.rkInlinePath = QtWidgets.QLineEdit()
        self.rkInlinePath.setAlignment(QtCore.Qt.AlignLeft)
        self.rkInlinePath.setFixedWidth(300)
        
        
        layoutFifteen.addWidget(self.inlinePathLabel)
        layoutFifteen.addWidget(self.rkInlinePath)
        layoutFifteen.addStretch()
        
        
        ##### Setting up the main layout #####

        # Section Header
        textureSection = QtWidgets.QLabel("Texture Options")
        generalSection = QtWidgets.QLabel("RawKee Project Options")
        pathSection    = QtWidgets.QLabel("Domain & Path Options")
        
        
        separator1 = QtWidgets.QFrame()
        separator1.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator1.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

        separator2 = QtWidgets.QFrame()
        separator2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

        layout.addWidget(generalSection)
        layout.addLayout(layoutFour)
        layout.addLayout(layoutFourB)
        layout.addLayout(layoutSix)
        
        layout.addLayout(layoutThreeAlpha)
        layout.addLayout(layoutThreeBravo)
        layout.addLayout(layoutThreeCharlie)

        layout.addLayout(layoutSeven)
        layout.addLayout(layoutEight)
        layout.addLayout(layoutNine)

        layout.addWidget(separator1)

        layout.addWidget(textureSection)
        layout.addLayout(layoutOne)
        layout.addLayout(layoutTwo)
        layout.addLayout(layoutThree)
        layout.addLayout(layoutFive)
        layout.addLayout(layoutFiveB)

        layout.addWidget(separator2)

        layout.addWidget(pathSection)
        layout.addLayout(layoutTen)
        layout.addLayout(layoutEleven)
        layout.addLayout(layoutTwelve)
        layout.addLayout(layoutThirteen)
        layout.addLayout(layoutFourteen)
        layout.addLayout(layoutFifteen)
        
        layout.addStretch()
        
        return layout
        
    def printMessages(self):
        print("Blah")
        
    def createLayout(self):
        pass
        
    def createConnections(self):
        pass
        
    def getOptionVarString(self, optionName):
        optStr = ""
        
        return optStr
        
    def setOptionVarString(self, strVal):
        pass
        
    def getOptionVarInt(self, optionName):
        
        optInt = 0
        
        return optInt
        
    def setOptionVarInt(self, intVal):
        pass
        
        
if __name__ == "__main__":
    try:
        openImportDialog.close()
        openImportDialog.deleteLater()
    except:
        pass
        
    openImportDialog = RKFOptsDialog()
    openImportDialog.show()
        
        
    
    