try:
    from PySide2 import QtWidgets # Qt5
except:
    from PySide6 import QtWidgets # Qt6
    
import maya.cmds as cmds

class HelloQtWindow(QtWidgets.QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Hello Qt")
        
        # Create controls
        self.name_line_edit = QtWidgets.QLineEdit()
        self.cube_btn = QtWidgets.QPushButton("Create Cube")
        self.sphere_btn = QtWidgets.QPushButton("Create Sphere")
        
        # Create Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.name_line_edit)
        layout.addWidget(self.cube_btn)
        layout.addWidget(self.sphere_btn)
        
        self.setLayout(layout)
        
        # Create Connections
        self.cube_btn.clicked.connect(self.createCube)
        self.sphere_btn.clicked.connect(self.createSphere)
        
    def getName(self):
        return(self.name_line_edit.text())
    
    def createCube(self):
        cmds.polyCube(name=self.getName())

    def createSphere(self):
        cmds.polySphere(name=self.getName())

if __name__ == "__main__":
    win = HelloQtWindow()
    win.show()
    