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

    from PySide2.QtGui     import QIntValidator, QDoubleValidator

    from PySide2           import QtUiTools

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
    
    from PySide6.QtGui     import QIntValidator, QDoubleValidator

    from PySide6           import QtUiTools
    
    from shiboken6         import wrapInstance

import sys
import os

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds


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
        
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        
        self.dialogTitle = dialogTitle
        self.setWindowTitle(self.dialogTitle)
        self.setMinimumSize(600,400)
        self.setFixedWidth(800)
        
        # On macOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)
            
        self.optsUIPath = os.path.abspath(__file__)
        self.optsUIPath = os.path.dirname(self.optsUIPath)
        self.optsUIPath = self.optsUIPath + "/auxilary/RKGeneralExportOptions.ui"
        
        loader           = QtUiTools.QUiLoader()
        expOptGUIFile    = QtCore.QFile(self.optsUIPath)
        expOptGUIFile.open(QtCore.QFile.ReadOnly)
        self.expOptFrame = loader.load(expOptGUIFile)

        self.createWidgets()
        

            
    def createWidgets(self):
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        
        if self.dialogTitle == "Castle Export All - Options" or self.dialogTitle == "Castle Export Selected - Options":
            self.rkExportMode = 1
        else:
            self.rkExportMode = 0
        
        self.loadOptionVars()
        scrollArea.setWidget(self.expOptFrame)

        ###########################################################  rkPrjDirButton
        self.rkPrjDirButton = self.expOptFrame.findChild(QtWidgets.QPushButton, 'rkPrjDirButton')
        self.rkPrjDirButton.setIcon(QtGui.QIcon(":folder-open.png"))
        self.rkPrjDirButton.setContentsMargins(0,0,0,0)
        self.rkPrjDirButton.setFixedSize(20,20)
        self.rkPrjDirButton.clicked.connect(self.setProjectFolder)
        
        
        
        if self.dialogTitle == "X3D Export Options":
            dialogLayout = QtWidgets.QVBoxLayout()
            dialogLayout.addWidget(scrollArea)
            
            buttonRow = QtWidgets.QHBoxLayout()
            self.buttonSpace = QtWidgets.QLabel(" ")
            self.buttonSpace.setFixedWidth(400)
            self.buttonSpace.setAlignment(QtCore.Qt.AlignRight)
            
            self.cancelButton = QtWidgets.QPushButton("Save Options and Close")
            self.cancelButton.setObjectName("RKOptPanel")
            self.cancelButton.clicked.connect(self.saveOptionsCloseDialog)
            
            self.exportButton = QtWidgets.QPushButton("Save Options and Export")
            self.exportButton.setObjectName("RKOptPanel")
            self.exportButton.clicked.connect(self.saveOptionsExportX3D)
            
            buttonRow.addWidget(self.buttonSpace)
            buttonRow.addWidget(self.cancelButton)
            buttonRow.addWidget(self.exportButton)
            dialogLayout.addLayout(buttonRow)

            self.setLayout(dialogLayout)
            
        elif self.dialogTitle == "X3D Export Selected Options":
            dialogLayout = QtWidgets.QVBoxLayout()
            dialogLayout.addWidget(scrollArea)
            
            buttonRow = QtWidgets.QHBoxLayout()
            self.buttonSpace = QtWidgets.QLabel(" ")
            self.buttonSpace.setFixedWidth(400)
            self.buttonSpace.setAlignment(QtCore.Qt.AlignRight)

            self.cancelButton = QtWidgets.QPushButton("Save Options and Close")
            self.cancelButton.setObjectName("RKOptPanel")
            self.cancelButton.clicked.connect(self.saveOptionsCloseDialog)

            self.exportButton = QtWidgets.QPushButton("Save Options and Export Selected")
            self.exportButton.setObjectName("RKOptPanel")
            self.exportButton.clicked.connect(self.saveOptionsExportX3D)
            
            buttonRow.addWidget(self.buttonSpace)
            buttonRow.addWidget(self.cancelButton)
            buttonRow.addWidget(self.exportButton)
            dialogLayout.addLayout(buttonRow)

            self.setLayout(dialogLayout)
            
        elif self.dialogTitle == "X3D Import Options":
            pass
        elif self.dialogTitle == "Castle Export All - Options":
            dialogLayout = QtWidgets.QVBoxLayout()
            dialogLayout.addWidget(scrollArea)
            
            buttonRow = QtWidgets.QHBoxLayout()
            self.buttonSpace = QtWidgets.QLabel(" ")
            self.buttonSpace.setFixedWidth(400)
            self.buttonSpace.setAlignment(QtCore.Qt.AlignRight)

            self.cancelButton = QtWidgets.QPushButton("Save Options and Close")
            self.cancelButton.setObjectName("RKOptPanel")
            self.cancelButton.clicked.connect(self.saveOptionsCloseDialog)

            self.exportButton = QtWidgets.QPushButton("Save Options and Send to Castle")
            self.exportButton.setObjectName("RKOptPanel")
            self.exportButton.clicked.connect(self.saveOptionsExportX3D)
            
            buttonRow.addWidget(self.buttonSpace)
            buttonRow.addWidget(self.cancelButton)
            buttonRow.addWidget(self.exportButton)
            dialogLayout.addLayout(buttonRow)

            self.setLayout(dialogLayout)
            
        elif self.dialogTitle == "Castle Export Selected - Options":
            dialogLayout = QtWidgets.QVBoxLayout()
            dialogLayout.addWidget(scrollArea)
            
            buttonRow = QtWidgets.QHBoxLayout()
            self.buttonSpace = QtWidgets.QLabel(" ")
            self.buttonSpace.setFixedWidth(400)
            self.buttonSpace.setAlignment(QtCore.Qt.AlignRight)

            self.cancelButton = QtWidgets.QPushButton("Save Options and Close")
            self.cancelButton.setObjectName("RKOptPanel")
            self.cancelButton.clicked.connect(self.saveOptionsCloseDialog)

            self.exportButton = QtWidgets.QPushButton("Save Options and Send Selected to Castle")
            self.exportButton.setObjectName("RKOptPanel")
            self.exportButton.clicked.connect(self.saveOptionsExportX3D)
            
            buttonRow.addWidget(self.buttonSpace)
            buttonRow.addWidget(self.cancelButton)
            buttonRow.addWidget(self.exportButton)
            dialogLayout.addLayout(buttonRow)

            self.setLayout(dialogLayout)
            


    def loadOptionVars(self):
        ###################################################################################
        self.rkCastlePrjDir  = cmds.optionVar( q='rkCastlePrjDir' )
        self.rkSunrizePrjDir = cmds.optionVar( q='rkSunrizePrjDir')
        self.rkPrjDir        = cmds.optionVar( q='rkPrjDir'       )

        self.rkImagePath     = cmds.optionVar( q='rkImagePath'    )
        self.rkAudioPath     = cmds.optionVar( q='rkAudioPath'    )

        self.rkUseHAnimSites = cmds.optionVar( q='rkUseHAnimSites')
        self.rkSkinInfluence = cmds.optionVar( q='rkSkinInfluence')

        self.rkAdjTexSize    = cmds.optionVar(q='rkAdjTexSize'  )
        self.rkDefTexWidth   = cmds.optionVar(q='rkTextureWidth' )
        self.rkDefTexHeight  = cmds.optionVar(q='rkTextureHeight')

        self.rkConsolidate   = cmds.optionVar(q='rkConsolidate'  )
        self.rkProcTexFormat = cmds.optionVar(q='rkProcTexFormat')
        self.rkFileTexFormat = cmds.optionVar(q='rkFileTexFormat')
        self.rkProcTexType   = cmds.optionVar(q='rkProcTexType'  )
        self.rkFileTexType   = cmds.optionVar(q='rkFileTexType'  )
        self.rkMovieTexType  = cmds.optionVar(q='rkMovieTexType' )
        self.rkAudioClipType = cmds.optionVar(q='rkAudioClipType')

        self.rkNormalOpts  = cmds.optionVar(q='rkNormalOpts' )
        self.rkCreaseAngle = cmds.optionVar(q='rkCreaseAngle')
        self.rkColorOpts   = cmds.optionVar(q='rkColorOpts'  )

        #sdlf.rkExportMode - Not loaded here
        ###########################################################  rkPrjDirButton
        self.rkProjectDirText = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'rkProjectDirText')
        if  self.rkExportMode == 1:
            self.rkProjectDirText.setText(self.rkCastlePrjDir)
        else:
            self.rkProjectDirText.setText(self.rkPrjDir)
        
        self.rkImagePathText  = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'rkImagePathText' )
        self.rkImagePathText.setText(self.rkImagePath)
        
        self.rkAudioPathText  = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'rkAudioPathText' )
        self.rkAudioPathText.setText(self.rkAudioPath)
        
        self.rkHAnimSiteCheckbox     = self.expOptFrame.findChild(QtWidgets.QCheckBox, 'rkHAnimSiteCheckbox'    )
        self.rkHAnimSiteCheckbox.setChecked(self.rkUseHAnimSites)
        
        self.rkSkinInfluenceComboBox = self.expOptFrame.findChild(QtWidgets.QComboBox, 'rkSkinInfluenceComboBox')
        self.rkSkinInfluenceComboBox.setCurrentIndex(self.rkSkinInfluence)
        
        self.rkAdjTexSizeCB     = self.expOptFrame.findChild(QtWidgets.QCheckBox, 'adjTexCheckBox'  )
        self.rkAdjTexSizeCB.setChecked(self.rkAdjTexSize)
        
        self.rkDefTexWidthLE    = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'textureWidth' )
        twValidator = QIntValidator(1, 4096, self.expOptFrame)
        self.rkDefTexWidthLE.setValidator(twValidator)
        self.rkDefTexWidthLE.setText(str(self.rkDefTexWidth))

        self.rkDefTexHeightLE   = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'textureHeight')
        thValidator = QIntValidator(1, 4096, self.expOptFrame)
        self.rkDefTexHeightLE.setValidator(thValidator)
        self.rkDefTexHeightLE.setText(str(self.rkDefTexHeight))

        self.rkConsolidateCheckbox = self.expOptFrame.findChild(QtWidgets.QCheckBox, 'rkConsolidateCheckbox')
        self.rkConsolidateCheckbox.setChecked(self.rkConsolidate)
        
        self.procTextureComboBox   = self.expOptFrame.findChild(QtWidgets.QComboBox, 'procTextureComboBox'  )
        self.procTextureComboBox.setCurrentIndex(self.rkProcTexType)
        
        self.procFormatComboBox    = self.expOptFrame.findChild(QtWidgets.QComboBox, 'proceduralFormat')
        self.procFormatComboBox.setCurrentIndex(self.rkProcTexFormat)
        
        self.fileTextureComboBox   = self.expOptFrame.findChild(QtWidgets.QComboBox, 'fileTextureComboBox'  )
        self.fileTextureComboBox.setCurrentIndex(self.rkFileTexType)
        
        self.consFormatComboBox    = self.expOptFrame.findChild(QtWidgets.QComboBox, 'consolidateFormat')
        self.consFormatComboBox.setCurrentIndex(self.rkFileTexFormat)
        
        self.movieTextureComboBox  = self.expOptFrame.findChild(QtWidgets.QComboBox, 'movieTextureComboBox' )
        self.movieTextureComboBox.setCurrentIndex(self.rkMovieTexType)
        
        self.audioClipComboBox     = self.expOptFrame.findChild(QtWidgets.QComboBox, 'audioClipComboBox'    )
        self.audioClipComboBox.setCurrentIndex(self.rkAudioClipType)
        
        self.normalOptions = self.expOptFrame.findChild(QtWidgets.QComboBox, 'normalOptions')
        self.normalOptions.setCurrentIndex(self.rkNormalOpts)
        
        self.creaseAngle = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'creaseAngle')
        self.caValidator = QDoubleValidator(0.0, 3.1416, 4, self.expOptFrame)
        self.creaseAngle.setValidator(self.caValidator)
        self.creaseAngle.setText(str(self.rkCreaseAngle))
        
        self.colorOptions  = self.expOptFrame.findChild(QtWidgets.QComboBox, 'colorOptions')
        self.colorOptions.setCurrentIndex(self.rkColorOpts)


        
    def setProjectFolder(self):
        print("Set Project Folder")
        
        if self.dialogTitle == "X3D Export Options" or self.dialogTitle == "X3D Export Selected Options":
            cmds.rkX3DSetProject()
            
            self.rkPrjDir = cmds.optionVar( q='rkPrjDir' )
            self.rkProjectDirText.setText(self.rkPrjDir)
            
        elif self.dialogTitle == "Castle Export All - Options" or self.dialogTitle == "Castle Export Selected - Options":
            cmds.rkCASSetProject()
            
            self.rkCastlePrjDir = cmds.optionVar( q='rkCastlePrjDir' )
            self.rkProjectDirText.setText(self.rkCastlePrjDir)
        
        
    def saveOptionsCloseDialog(self):
        self.saveOptions()
        self.close()

    
    def saveOptionsExportX3D(self):
        self.saveOptions()
        self.close()
        self.exportX3D()
        
    def saveOptions(self):
        #print("Options Saved!")
        
        ###########################################################  rkPrjDirButton
        self.rkProjectDirText        = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'rkProjectDirText'       )
        self.rkImagePathText         = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'rkImagePathText'        )
        self.rkAudioPathText         = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'rkAudioPathText'        )
        
        self.rkHAnimSiteCheckbox     = self.expOptFrame.findChild(QtWidgets.QCheckBox, 'rkHAnimSiteCheckbox'    )
        self.rkSkinInfluenceComboBox = self.expOptFrame.findChild(QtWidgets.QComboBox, 'rkSkinInfluenceComboBox')
        
        self.rkAdjTexSizeCB          = self.expOptFrame.findChild(QtWidgets.QCheckBox, 'adjTexCheckBox'         )
        self.rkDefTexWidthLE         = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'textureWidth'           )
        self.rkDefTexHeightLE        = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'textureHeight'          )

        self.rkConsolidateCheckbox   = self.expOptFrame.findChild(QtWidgets.QCheckBox, 'rkConsolidateCheckbox'  )
        self.procTextureComboBox     = self.expOptFrame.findChild(QtWidgets.QComboBox, 'procTextureComboBox'    )
        self.fileTextureComboBox     = self.expOptFrame.findChild(QtWidgets.QComboBox, 'fileTextureComboBox'    )
        self.movieTextureComboBox    = self.expOptFrame.findChild(QtWidgets.QComboBox, 'movieTextureComboBox'   )
        self.audioClipComboBox       = self.expOptFrame.findChild(QtWidgets.QComboBox, 'audioClipComboBox'      )
        
        self.normalOptions           = self.expOptFrame.findChild(QtWidgets.QComboBox, 'normalOptions'          )
        self.creaseAngle             = self.expOptFrame.findChild(QtWidgets.QLineEdit, 'creaseAngle'            )
        self.colorOptions            = self.expOptFrame.findChild(QtWidgets.QComboBox, 'colorOptions'           )

        self.procFormatComboBox      = self.expOptFrame.findChild(QtWidgets.QComboBox, 'proceduralFormat'       )
        self.consFormatComboBox      = self.expOptFrame.findChild(QtWidgets.QComboBox, 'consolidateFormat'      )
        
        cmds.optionVar(iv=('rkExportMode', self.rkExportMode))
        
        if self.rkExportMode == 0:
            cmds.optionVar(sv=('rkPrjDir',     self.rkProjectDirText.text()))

        elif self.rkExportMode == 1:
            cmds.optionVar(sv=('rkCastlePrjDir', self.rkProjectDirText.text()))
        elif self.rkExportMode == 2:
            #cmds.optionVar( q='rkSunrizePrjDir'  ) TODO
            pass
        
        cmds.optionVar( sv=('rkImagePath', self.rkImagePathText.text()))
        cmds.optionVar( sv=('rkAudioPath', self.rkAudioPathText.text()))
        
        cmds.optionVar( iv=('rkUseHAnimSites', self.rkHAnimSiteCheckbox.isChecked()))
        cmds.optionVar( iv=('rkSkinInfluence', self.rkSkinInfluenceComboBox.currentIndex()))

        cmds.optionVar( iv=('rkAdjTexSize'   , self.rkAdjTexSizeCB.isChecked()))

        # Texture Width
        twt = self.rkDefTexWidthLE.text()
        if twt.strip() == "":
            twt = "0"
        twi = int(twt)
        if twi < 1:
            twi = 1
        elif twi > 4096:
            twi = 4096
        cmds.optionVar( iv=('rkTextureWidth' , twi))
        
        # Texture Height
        hwt = self.rkDefTexWidthLE.text()
        if hwt.strip() == "":
            hwt = "0"
        hwi = int(hwt)
        if hwi < 1:
            hwi = 1
        elif hwi > 4096:
            hwi = 4096
        cmds.optionVar( iv=('rkTextureHeight', hwi))

        cmds.optionVar( iv=('rkConsolidate'  , self.rkConsolidateCheckbox.isChecked()))
        cmds.optionVar( iv=('rkProcTexType'  , self.procTextureComboBox.currentIndex()))
        cmds.optionVar( iv=('rkFileTexType'  , self.fileTextureComboBox.currentIndex()))
        cmds.optionVar( iv=('rkMovieTexType' , self.movieTextureComboBox.currentIndex()))
        cmds.optionVar( iv=('rkAudioClipType', self.audioClipComboBox.currentIndex()))
        
        cmds.optionVar( iv=('rkNormalOpts', self.normalOptions.currentIndex()))
        cmds.optionVar( iv=('rkColorOpts' , self.colorOptions.currentIndex()))

        # Crease Angle
        cat = self.creaseAngle.text()
        if cat.strip() == "":
            cat = "0.0"
        caf = float(cat)
        if caf < 0.0:
            caf = 0.0
        elif caf > 3.1416:
            caf = 3.1416
        cmds.optionVar( fv=('rkCreaseAngle', caf))

        cmds.optionVar( iv=('rkProcTexFormat', self.procTextureComboBox.currentIndex()))
        cmds.optionVar( iv=('rkFileTexFormat', self.fileTextureComboBox.currentIndex()))


    def exportX3D(self):
        if self.rkExportMode == 0:
            if self.dialogTitle == "X3D Export Options":
                cmds.rkX3DExport()
            else:
                cmds.rkX3DSelExport()
        elif self.rkExportMode == 1:
            if self.dialogTitle == "Castle Export All - Options":
                cmds.rkCASExport()
            else:
                cmds.rkCASSelExport()
        print("X3D file exported!")

        
        
if __name__ == "__main__":
    try:
        openImportDialog.close()
        openImportDialog.deleteLater()
    except:
        pass
        
    openImportDialog = RKFOptsDialog()
    openImportDialog.show()
        
        
    
    