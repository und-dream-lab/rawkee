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

        # On macOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)
        
        self.createWidgets()
            
    def createWidgets(self):
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        
        contentWidget = QtWidgets.QWidget()
        contentLayout = QtWidgets.QVBoxLayout(contentWidget)
        
        if self.dialogTitle == "X3D Export Options":
            self.loadOptionVars()

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
            self.loadOptionVars()

            contentLayout = self.buildX3DExportPanel(contentLayout)

            scrollArea.setWidget(contentWidget)
            dialogLayout = QtWidgets.QVBoxLayout()
            dialogLayout.addWidget(scrollArea)
            
            buttonRow = QtWidgets.QHBoxLayout()
            self.buttonSpace = QtWidgets.QLabel(" ")
            self.buttonSpace.setFixedWidth(400)
            self.buttonSpace.setAlignment(QtCore.Qt.AlignRight)
            self.cancelButton = QtWidgets.QPushButton("Save Options and Close")
            self.exportButton = QtWidgets.QPushButton("Save Options and Export Selected")
            
            buttonRow.addWidget(self.buttonSpace)
            buttonRow.addWidget(self.cancelButton)
            buttonRow.addWidget(self.exportButton)
            dialogLayout.addLayout(buttonRow)

            self.setLayout(dialogLayout)
            
        elif self.dialogTitle == "X3D Import Options":
            pass
        elif self.dialogTitle == "Castle Export All - Options":
            self.loadOptionVars()

            contentLayout = self.buildX3DExportPanel(contentLayout)

            scrollArea.setWidget(contentWidget)
            dialogLayout = QtWidgets.QVBoxLayout()
            dialogLayout.addWidget(scrollArea)
            
            buttonRow = QtWidgets.QHBoxLayout()
            self.buttonSpace = QtWidgets.QLabel(" ")
            self.buttonSpace.setFixedWidth(400)
            self.buttonSpace.setAlignment(QtCore.Qt.AlignRight)
            self.cancelButton = QtWidgets.QPushButton("Save Options and Close")
            self.exportButton = QtWidgets.QPushButton("Save Options and Send to Castle")
            
            buttonRow.addWidget(self.buttonSpace)
            buttonRow.addWidget(self.cancelButton)
            buttonRow.addWidget(self.exportButton)
            dialogLayout.addLayout(buttonRow)

            self.setLayout(dialogLayout)
            
        elif self.dialogTitle == "Castle Export Selected - Options":
            self.loadOptionVars()

            contentLayout = self.buildX3DExportPanel(contentLayout)

            scrollArea.setWidget(contentWidget)
            dialogLayout = QtWidgets.QVBoxLayout()
            dialogLayout.addWidget(scrollArea)
            
            buttonRow = QtWidgets.QHBoxLayout()
            self.buttonSpace = QtWidgets.QLabel(" ")
            self.buttonSpace.setFixedWidth(400)
            self.buttonSpace.setAlignment(QtCore.Qt.AlignRight)
            self.cancelButton = QtWidgets.QPushButton("Save Options and Close")
            self.exportButton = QtWidgets.QPushButton("Save Options and Send Selected to Castle")
            
            buttonRow.addWidget(self.buttonSpace)
            buttonRow.addWidget(self.cancelButton)
            buttonRow.addWidget(self.exportButton)
            dialogLayout.addLayout(buttonRow)

            self.setLayout(dialogLayout)
            


    def loadOptionVars(self):
        self.rkCastlePrjDir    = cmds.optionVar( q='rkCastlePrjDir'   )
        self.rkSunrizePrjDir   = cmds.optionVar( q='rkSunrizePrjDir'  )
        self.rkPrjDir          = cmds.optionVar( q='rkPrjDir'         )
        self.rkBaseDomain      = cmds.optionVar( q='rkBaseDomain'     )
        self.rkSubDir          = cmds.optionVar( q='rkSubDir'         )
        self.rkImagePath       = cmds.optionVar( q='rkImagePath'      )
        self.rkAudioPath       = cmds.optionVar( q='rkAudioPath'      )
        self.rkInlinePath      = cmds.optionVar( q='rkInlinePath'     )
        
        self.rk2dTexWrite      = cmds.optionVar( q='rk2dTexWrite'     )
        self.rkMovTexWrite     = cmds.optionVar( q='rkMovTexWrite'    )
        self.rkAudioWrite      = cmds.optionVar( q='rkAudioWrite'     )
        self.rk2dFileFormat    = cmds.optionVar( q='rk2dFileFormat'   )
        self.rkMovFileFormat   = cmds.optionVar( q='rkMovFileFormat'  )
        self.rkAudioFileFormat = cmds.optionVar( q='rkAudioFileFormat')
        self.rkExportCameras   = cmds.optionVar( q='rkExportCameras'  )
        self.rkExportLights    = cmds.optionVar( q='rkExportLights'   )
        self.rkExportSounds    = cmds.optionVar( q='rkExportSounds'   )
        self.rkExportMetadata  = cmds.optionVar( q='rkExportMetadata' )
        self.rkProcTexNode     = cmds.optionVar( q='rkProcTexNode'    )
        self.rkFileTexNode     = cmds.optionVar( q='rkFileTexNode'    )
        self.rkLayerTexNode    = cmds.optionVar( q='rkLayerTexNode'   )
        self.rkAdjTexSize      = cmds.optionVar( q='rkAdjTexSize'     )
        
        self.rkMovieAsURI      = cmds.optionVar( q='rkMovieAsURI'     )
        self.rkAudioAsURI      = cmds.optionVar( q='rkAudioAsURI'     )
        self.rkInlineAsURI     = cmds.optionVar( q='rkInlineAsURI'    )
        
        self.rkDefTexWidth     = cmds.optionVar( q='rkDefTexWidth'    )
        self.rkDefTexHeight    = cmds.optionVar( q='rkDefTexHeight'   )
        self.rkColorOpts       = cmds.optionVar( q='rkColorOpts'      )
        self.rkNormalOpts      = cmds.optionVar( q='rkNormalOpts'     )
        self.rkExportMode      = cmds.optionVar( q='rkExportMode'     )
        
        self.rkCreaseAngle     = cmds.optionVar( q='rkCreaseAngle'    )



    def buildX3DExportPanel(self, layout):
        #layout = QtWidgets.QVBoxLayout()

        # Option One
        layoutOne = QtWidgets.QHBoxLayout()
        self.mayaTexLabel = QtWidgets.QLabel("     Procedural Textures - Export as:")
        self.mayaTexLabel.setAlignment(QtCore.Qt.AlignRight)
        self.mayaTexLabel.setFixedWidth(250)
        self.comboMayaTexOptions = QtWidgets.QComboBox()
        self.comboMayaTexOptions.addItems(["ImageTexture", "ImagTexture w/DataURI", "PixelTexture"])
        self.comboMayaTexOptions.setFixedWidth(200)
        
        ###############################################################
        # Set the Type of X3D Texture Node for Maya Procedural Textures
        self.comboMayaTexOptions.setCurrentIndex(self.rkProcTexNode)
        # Add change method here.
        
        layoutOne.addWidget(self.mayaTexLabel)
        layoutOne.addWidget(self.comboMayaTexOptions)
        layoutOne.addStretch()
        
        # Option Two
        layoutTwo = QtWidgets.QHBoxLayout()
        self.mayaTexFileLabel = QtWidgets.QLabel("     File Textures - Export as:")
        self.mayaTexFileLabel.setAlignment(QtCore.Qt.AlignRight)
        self.mayaTexFileLabel.setFixedWidth(250)
        self.comboMayaTexFileOptions = QtWidgets.QComboBox()
        self.comboMayaTexFileOptions.addItems(["ImageTexture", "ImagTexture w/DataURI", "PixelTexture"])
        self.comboMayaTexFileOptions.setFixedWidth(200)
        
        ###############################################################
        # Set the Type of X3D Texture Node for Maya File Textures
        self.comboMayaTexFileOptions.setCurrentIndex(self.rkFileTexNode)
        # Add change method here.
        
        layoutTwo.addWidget(self.mayaTexFileLabel)
        layoutTwo.addWidget(self.comboMayaTexFileOptions)
        layoutTwo.addStretch()
        
        # Option Three
        layoutThree = QtWidgets.QHBoxLayout()
        self.mayaLayeredLabel = QtWidgets.QLabel("     Layered Textures - Export as:")
        self.mayaLayeredLabel.setAlignment(QtCore.Qt.AlignRight)
        self.mayaLayeredLabel.setFixedWidth(250)
        self.comboMayaLayeredOptions = QtWidgets.QComboBox()
        self.comboMayaLayeredOptions.addItems(["MultiTexture", "ImageTexture", "ImagTexture w/DataURI", "PixelTexture"])
        self.comboMayaLayeredOptions.setFixedWidth(200)
        
        ###############################################################
        # Set the Type of X3D Texture Node for Maya Layered Textures
        self.comboMayaLayeredOptions.setCurrentIndex(self.rkLayerTexNode)
        # Add change method here.
        
        layoutThree.addWidget(self.mayaLayeredLabel)
        layoutThree.addWidget(self.comboMayaLayeredOptions)
        layoutThree.addStretch()
        
        # Option Three Alpha
        layoutThreeAlpha = QtWidgets.QHBoxLayout()
        self.texFileFormatLabel = QtWidgets.QLabel("2D Texture Files:")
        self.texFileFormatLabel.setAlignment(QtCore.Qt.AlignRight)
        self.texFileFormatLabel.setFixedWidth(250)
        self.texFileFormatOptions = QtWidgets.QComboBox()
        self.texFileFormatOptions.addItems(["Current Media File", "PNG - Portable Netowrk Graphics", "JPG - Joint Photographic Experts Group", "GIF - Graphics Interchange Format", "WebP - Web Picture Format"])
        self.texFileFormatOptions.setFixedWidth(250)
        
        ###############################################################
        # Set the Type of Media Format for Maya File Textures
        self.texFileFormatOptions.setCurrentIndex(self.rk2dFileFormat)
        # Add change method here.
        
        layoutThreeAlpha.addWidget(self.texFileFormatLabel)
        layoutThreeAlpha.addWidget(self.texFileFormatOptions)
        layoutThreeAlpha.addStretch()
        
        
        # Option Three Bravo
        layoutThreeBravo = QtWidgets.QHBoxLayout()
        self.movFileFormatLabel = QtWidgets.QLabel("Movie/Video Files:")
        self.movFileFormatLabel.setAlignment(QtCore.Qt.AlignRight)
        self.movFileFormatLabel.setFixedWidth(250)
        self.movFileFormatOptions = QtWidgets.QComboBox()
        self.movFileFormatOptions.addItems(["Current Media File", "MP4 with H.264", "MOV with H.264", "Ogg with Theora/Vorbis", "WebM with VP9"])
        self.movFileFormatOptions.setFixedWidth(250)
        
        ###############################################################
        # Set the Type of Media Format for Maya Movie Textures
        self.movFileFormatOptions.setCurrentIndex(self.rkMovFileFormat)
        # Add change method here.
        
        layoutThreeBravo.addWidget(self.movFileFormatLabel)
        layoutThreeBravo.addWidget(self.movFileFormatOptions)
        layoutThreeBravo.addStretch()
        
        
        # Option Three Charlie
        layoutThreeCharlie = QtWidgets.QHBoxLayout()
        self.audFileFormatLabel = QtWidgets.QLabel("Audio Files:")
        self.audFileFormatLabel.setAlignment(QtCore.Qt.AlignRight)
        self.audFileFormatLabel.setFixedWidth(250)
        self.audFileFormatOptions = QtWidgets.QComboBox()
        self.audFileFormatOptions.addItems(["Current Media File", "MP3 - MPEG Audio Layer 3", "AAC - Advanced Audio Coding", "Ogg - Vorbis", "WAV - Waveform Audio File Format"])
        self.audFileFormatOptions.setFixedWidth(250)
        
        ###############################################################
        # Set the Type of Media Format for Maya Audio Clip Nodes
        self.texFileFormatOptions.setCurrentIndex(self.rkAudioFileFormat)
        # Add change method here.
        
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
        ###############################################################
        # Consolidate Maya File Textures Under Project
        self.texture2FileCheckBox.setChecked(self.rk2dTexWrite)
        # Add change method here.
        
        self.movie2FileCheckBox   = QtWidgets.QCheckBox("Movie Textures")
        ###############################################################
        # Consolidate Maya Movie Textures Under Project
        self.movie2FileCheckBox.setChecked(self.rkMovTexWrite)
        # Add change method here.
        
        self.audio2FileCheckBox   = QtWidgets.QCheckBox("Audio Clips")
        ###############################################################
        # Consolidate Maya Audio Clip files Under Project
        self.audio2FileCheckBox.setChecked(self.rkAudioWrite)
        # Add change method here.
        
        
        layoutFourB.addWidget(spacer4B)
        layoutFourB.addWidget(self.texture2FileCheckBox)
        layoutFourB.addWidget(self.movie2FileCheckBox)
        layoutFourB.addWidget(self.audio2FileCheckBox)
        layoutFourB.addStretch()
        
        # Option FourC
        layoutFourC = QtWidgets.QHBoxLayout()
        spacer4C = QtWidgets.QLabel(" ")
        spacer4C.setAlignment(QtCore.Qt.AlignRight)
        spacer4C.setFixedWidth(150)

        self.inlineURICheckBox = QtWidgets.QCheckBox("Inline as DataURI")
        ###############################################################
        # Set URL field value of node to a DataURI
        self.inlineURICheckBox.setChecked(self.rkInlineAsURI)
        # Add change method here.
        
        self.movieURICheckBox  = QtWidgets.QCheckBox("MovieTexture as DataURI")
        ###############################################################
        # Set URL field value of node to a DataURI
        self.movieURICheckBox.setChecked(self.rkMovieAsURI)
        # Add change method here.
        
        self.audioURICheckBox  = QtWidgets.QCheckBox("AudioClip as DataURI")
        ###############################################################
        # Set URL field value of node to a DataURI
        self.audioURICheckBox.setChecked(self.rkAudioAsURI)
        # Add change method here.
        
        
        layoutFourC.addWidget(spacer4C)
        layoutFourC.addWidget(self.inlineURICheckBox)
        layoutFourC.addWidget(self.movieURICheckBox)
        layoutFourC.addWidget(self.audioURICheckBox)
        layoutFourC.addStretch()
        
        # Option Five
        layoutFive = QtWidgets.QHBoxLayout()
        adjTexSizeLabel = QtWidgets.QLabel("Adjust Texture Size:")
        adjTexSizeLabel.setAlignment(QtCore.Qt.AlignRight)
        adjTexSizeLabel.setFixedWidth(250)
        layoutFive.addWidget(adjTexSizeLabel)
        
        # Option FiveB
        layoutFiveB = QtWidgets.QHBoxLayout()
        spacer5B = QtWidgets.QLabel(" ")
        spacer5B.setAlignment(QtCore.Qt.AlignRight)
        spacer5B.setFixedWidth(180)

        self.adjTexCheckBox = QtWidgets.QCheckBox()
        ###############################################################
        # Adjust Size of Texture at time of Export
        self.adjTexCheckBox.setChecked(self.rkAdjTexSize)
        # Add change method here.
        
        self.adjTexCheckBox.setFixedWidth(20)
        
        layoutFiveB.addWidget(spacer5B)
        layoutFive.addWidget(self.adjTexCheckBox)
       
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
        self.intWidVal = QtGui.QIntValidator()
        self.intWidVal.setRange(1,8192)
        self.textureWidth.setValidator(self.intWidVal)
        
        ###############################################################
        # Default Width Values for RawKee-written textures
        textValue = str(self.rkDefTexWidth)
        self.textureWidth.setText(textValue)
        # Add change method here.
        
        self.adjTexHeightLabel = QtWidgets.QLabel("Height:")
        self.adjTexHeightLabel.setAlignment(QtCore.Qt.AlignRight)
        self.adjTexHeightLabel.setFixedWidth(50)
        self.textureHeight = QtWidgets.QLineEdit()
        self.textureHeight.setAlignment(QtCore.Qt.AlignLeft)
        self.textureHeight.setFixedWidth(50)
        self.intHiVal = QtGui.QIntValidator()
        self.intHiVal.setRange(1,8192)
        self.textureHeight.setValidator(self.intHiVal)
        
        ###############################################################
        # Default Height Values for RawKee-written textures
        textValue = str(self.rkDefTexHeight)
        self.textureHeight.setText(textValue)
        # Add change method here.
        
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
        #############################################################################
        # Option as to whether Maya Cameras are exported as X3D Viewpoints or are 
        # ignored.
        self.exCameras.setChecked(self.rkExportCameras)
        # Add change method here.
        
        self.exLights   = QtWidgets.QCheckBox("Maya Lights as X3D Lights")
        #############################################################################
        # Option as to whether Maya Lights are exported as corresponding 
        # X3D Lights or are ignored.
        self.exLights.setChecked(self.rkExportLights)
        # Add change method here.
        
        self.exCameras.setFixedWidth(250)
        self.exLights.setFixedWidth(250)
        
        self.exSounds   = QtWidgets.QCheckBox("RawKee Sound as X3D Sound")
        #############################################################################
        # Option as to whether the custome RawKee node 'x3dSound' is exported as an 
        # X3D Sound node or is ignored.
        self.exSounds.setChecked(self.rkExportSounds)
        # Add change method here.
        
        self.exMetadata = QtWidgets.QCheckBox("RawKee Metadata as X3D Metadata")
        #############################################################################
        # Option as to whether the custome RawKee nodes conforming to X3D Metadata 
        # nodes are exporeted or are ignored.
        self.exMetadata.setChecked(self.rkExportMetadata)
        # Add change method here.
        
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
        
        prjDirTitle = "RawKee Project Directory:"
        if self.rkExportMode == 1:
            prjDirTitle = "Castle Project Data Folder:"
            
        self.rpdLabel = QtWidgets.QLabel(prjDirTitle)
        self.rpdLabel.setAlignment(QtCore.Qt.AlignRight)
        self.rpdLabel.setFixedWidth(250)
        
        self.rkProjectDir = QtWidgets.QLineEdit()
        self.rkProjectDir.setEnabled(False)
        #############################################################################
        # If 'rkExportMode' is 0, then load the RawKee Project Directory
        # else if 'rkExportMode is 1, then load the Castle Project Data Folder.
        if self.rkExportMode == 0:
            self.rkProjectDir.setText(self.rkPrjDir)
        elif self.rkExportMode == 1:
            self.rkProjectDir.setText(self.rkCastlePrjDir)
        
        self.rkProjectDir.setAlignment(QtCore.Qt.AlignLeft)
        self.rkProjectDir.setFixedWidth(300)
        
        self.rkPrjDirButton = QtWidgets.QPushButton()
        self.rkPrjDirButton.setIcon(QtGui.QIcon(":folder-open.png"))
        self.rkPrjDirButton.setContentsMargins(0,0,0,0)
        self.rkPrjDirButton.setFixedSize(20,20)
        # Add method connection here on 'rkPrjDirButton' for setting the rkProjectDir and its 
        # corresponding RawKee/Castle project directory optionVar
        
        layoutTen.addWidget(self.rpdLabel)
        layoutTen.addWidget(self.rkProjectDir)
        layoutTen.addWidget(self.rkPrjDirButton)
        layoutTen.addStretch()
        
        
        # Option Eleven
        layoutEleven = QtWidgets.QHBoxLayout()
        self.bDomLabel = QtWidgets.QLabel("Base Web Domain:")
        self.bDomLabel.setAlignment(QtCore.Qt.AlignRight)
        self.bDomLabel.setFixedWidth(250)
        
        self.rkBaseDomainText = QtWidgets.QLineEdit()
        self.rkBaseDomainText.setAlignment(QtCore.Qt.AlignLeft)
        self.rkBaseDomainText.setFixedWidth(300)
        # Manually type your primary web domain if you expect to publish to the web
        self.rkBaseDomainText.text  = self.rkBaseDomain
        # add method functionality to save user entered domain information.
        
        layoutEleven.addWidget(self.bDomLabel)
        layoutEleven.addWidget(self.rkBaseDomainText)
        layoutEleven.addStretch()
        
        
        # Option Twelve
        layoutTwelve = QtWidgets.QHBoxLayout()
        self.subDirLabel = QtWidgets.QLabel("Domain Sub-Directory Path:")
        self.subDirLabel.setAlignment(QtCore.Qt.AlignRight)
        self.subDirLabel.setFixedWidth(250)
        
        self.rkSubDirText = QtWidgets.QLineEdit()
        self.rkSubDirText.setAlignment(QtCore.Qt.AlignLeft)
        self.rkSubDirText.setFixedWidth(300)
        # Manually type the sub directory path for use with your web domain 
        # if you expect to publish to the web
        self.rkSubDirText.setText(self.rkSubDir)
        # add method functionality to save user entered sub directory path information.
        
        
        layoutTwelve.addWidget(self.subDirLabel)
        layoutTwelve.addWidget(self.rkSubDirText)
        layoutTwelve.addStretch()
        
        
        # Option Thirteen
        layoutThirteen = QtWidgets.QHBoxLayout()
        self.imagePathLabel = QtWidgets.QLabel("Image Path:")
        self.imagePathLabel.setAlignment(QtCore.Qt.AlignRight)
        self.imagePathLabel.setFixedWidth(250)
        
        self.rkImagePathText = QtWidgets.QLineEdit()
        self.rkImagePathText.setAlignment(QtCore.Qt.AlignLeft)
        self.rkImagePathText.setFixedWidth(300)
        # Manually type the sub directory path where you plan to store your
        # images. Can be the same as your Audio and Inline paths
        self.rkImagePathText.setText(self.rkImagePath)
        # add method functionality to save user entered media path information.
        
        
        layoutThirteen.addWidget(self.imagePathLabel)
        layoutThirteen.addWidget(self.rkImagePathText)
        layoutThirteen.addStretch()
        
        
        # Option Fourteen
        layoutFourteen = QtWidgets.QHBoxLayout()
        self.audioPathLabel = QtWidgets.QLabel("Audio Path:")
        self.audioPathLabel.setAlignment(QtCore.Qt.AlignRight)
        self.audioPathLabel.setFixedWidth(250)
        
        self.rkAudioPathText = QtWidgets.QLineEdit()
        self.rkAudioPathText.setAlignment(QtCore.Qt.AlignLeft)
        self.rkAudioPathText.setFixedWidth(300)
        # Manually type the sub directory path where you plan to store your
        # audio files. Can be the same as your Image and Inline paths
        self.rkAudioPathText.setText(self.rkAudioPath)
        # add method functionality to save user entered media path information.
        
        
        layoutFourteen.addWidget(self.audioPathLabel)
        layoutFourteen.addWidget(self.rkAudioPathText)
        layoutFourteen.addStretch()
        
        
        # Option Fifteen
        layoutFifteen = QtWidgets.QHBoxLayout()
        self.inlinePathLabel = QtWidgets.QLabel("Inline Path:")
        self.inlinePathLabel.setAlignment(QtCore.Qt.AlignRight)
        self.inlinePathLabel.setFixedWidth(250)
        
        self.rkInlinePathText = QtWidgets.QLineEdit()
        self.rkInlinePathText.setAlignment(QtCore.Qt.AlignLeft)
        self.rkInlinePathText.setFixedWidth(300)
        # Manually type the sub directory path where you plan to store your
        # inline X3D and glTF files. Can be the same as your Audio and Image paths
        self.rkInlinePathText.setText(self.rkInlinePath)
        # add method functionality to save user entered media path information.
        
        
        layoutFifteen.addWidget(self.inlinePathLabel)
        layoutFifteen.addWidget(self.rkInlinePathText)
        layoutFifteen.addStretch()
        
        
        # Option Sixteen
        layoutSixteen = QtWidgets.QHBoxLayout()
        self.normalLabel = QtWidgets.QLabel("     Normal Options:")
        self.normalLabel.setAlignment(QtCore.Qt.AlignRight)
        self.normalLabel.setFixedWidth(250)
        self.normalOptions = QtWidgets.QComboBox()
        self.normalOptions.addItems(["Map + Crease Angle + Per Vertex", "Map + Crease Angle", "Map + Per Vertex", "Map", "Crease Angle + Per Vertex", "Crease Angle", "Per Vertex"])
        self.normalOptions.setFixedWidth(250)
        ###############################################################
        # Set the type of X3D Normal information exported by RawKee
        self.normalOptions.setCurrentIndex(self.rkNormalOpts)
        # Add change method here.
        
        
        self.cAngleLabel = QtWidgets.QLabel("Crease Angle:")
        self.cAngleLabel.setAlignment(QtCore.Qt.AlignRight)
        self.cAngleLabel.setFixedWidth(80)
        self.creaseAngle = QtWidgets.QLineEdit()
        self.creaseAngle.setAlignment(QtCore.Qt.AlignLeft)
        self.creaseAngle.setFixedWidth(50)

        self.dubCAVal = QtGui.QDoubleValidator()
        self.dubCAVal.setRange(0.0, 3.14)
        self.dubCAVal.setDecimals(2)
        self.creaseAngle.setValidator(self.dubCAVal)
        
        ###############################################################
        # Default CreaseAngle Values for RawKee-written Shape nodes
        textValue = str(self.rkCreaseAngle)
        self.creaseAngle.setText(textValue)
        # Add change method here.



        layoutSixteen.addWidget(self.normalLabel)
        layoutSixteen.addWidget(self.normalOptions)
        layoutSixteen.addWidget(self.cAngleLabel)
        layoutSixteen.addWidget(self.creaseAngle)
        layoutSixteen.addStretch()
        
        
        # Option Sixteen
        layoutSeventeen = QtWidgets.QHBoxLayout()
        self.colorLabel = QtWidgets.QLabel("     Color Options:")
        self.colorLabel.setAlignment(QtCore.Qt.AlignRight)
        self.colorLabel.setFixedWidth(250)
        self.colorOptions = QtWidgets.QComboBox()
        self.colorOptions.addItems(["Textures + Per Vertex", "Textures", "Per Vertex"])
        self.colorOptions.setFixedWidth(250)
        ###############################################################
        # Set the type of X3D Color information exported by RawKee
        self.colorOptions.setCurrentIndex(self.rkColorOpts)
        # Add change method here.
        
        layoutSeventeen.addWidget(self.colorLabel)
        layoutSeventeen.addWidget(self.colorOptions)
        layoutSeventeen.addStretch()
        
        
        ##### Setting up the main layout #####

        # Section Header
        textureSection = QtWidgets.QLabel("Texture Options")

        generalSection = QtWidgets.QLabel("Media & Node Options")

        pathLabelText  = "Domain & Path Options"
        if self.rkExportMode == 1:
            pathLabelText  = "Game Engine Path Options"
        pathSection    = QtWidgets.QLabel(pathLabelText)
        meshSection    = QtWidgets.QLabel("Mesh & Shape Options")
        
        convLayout = QtWidgets.QHBoxLayout()
        spaceConv  = QtWidgets.QLabel(" ")
        spaceConv.setFixedWidth(80)
        spaceConv.setAlignment(QtCore.Qt.AlignRight)
        convLabel = QtWidgets.QLabel("Convert Media Formats:")
        convLabel.setFixedWidth(200)
        convLabel.setAlignment(QtCore.Qt.AlignLeft)
        convLayout.addWidget(spaceConv)
        convLayout.addWidget(convLabel)
        convLayout.addStretch()
        
        
        separator1 = QtWidgets.QFrame()
        separator1.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator1.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

        separator2 = QtWidgets.QFrame()
        separator2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

        separator3 = QtWidgets.QFrame()
        separator3.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator3.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

        layout.addWidget(generalSection)
        layout.addLayout(layoutFour)
        layout.addLayout(layoutFourB)
        layout.addLayout(layoutFourC)
        layout.addLayout(layoutSix)
        
        layout.addLayout(convLayout)
        layout.addLayout(layoutThreeAlpha)
        layout.addLayout(layoutThreeBravo)
        layout.addLayout(layoutThreeCharlie)

        layout.addLayout(layoutSeven)
        layout.addLayout(layoutEight)
        layout.addLayout(layoutNine)

        layout.addWidget(separator1)
        
        layout.addWidget(meshSection)
        layout.addLayout(layoutSixteen)
        layout.addLayout(layoutSeventeen)

        layout.addWidget(separator2)

        layout.addWidget(textureSection)
        layout.addLayout(layoutOne)
        layout.addLayout(layoutTwo)
        #if self.rkExportMode == 0:
        layout.addLayout(layoutThree)
        layout.addLayout(layoutFive)
        layout.addLayout(layoutFiveB)

        layout.addWidget(separator3)

        layout.addWidget(pathSection)
        layout.addLayout(layoutTen)
        if self.rkExportMode == 0:
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
        
        
    
    