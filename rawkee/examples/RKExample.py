import sys
import os
from rawkee.io.RKSceneTraversal import *

class RKExample():
    def __init__(self):
        ###################################################
        # Create the RKSceneTraversal object
        self.trv = RKSceneTraversal()
        
        ###################################################
        # Set the X3D file encoding to XML using 'x3d'
        # Other options would be: 'x3dv', 'x3dj', or 'html'
        self.enc = "x3d"
        
        ###############################################################################
        # Create file path for example file export to the RawKee app's "example" module
        self.exportFilePath = sys.modules[self.trv.__class__.__module__].__file__.replace("\\", "/").rsplit("/", 1)[0].replace("/io", "/examples") + "/example." + self.enc


    def printExampleFilePath(self):
        print(self.exportFilePath)


    # Important Function
    def exportExample(self):
        ########################################
        # Create the X3D Document
        x3dDoc       = self.trv.getX3DObject()
        
        ########################################
        # Create the Scene of the X3D Document
        x3dDoc.Scene = self.trv.getSceneObject()
        
        #############################
        # RKSceneTraversal.processBasicNodeAddition(self, x3dParentNode, x3dFieldName, x3dNodeType, nodeName="")
        
        ###############################################
        # Create and Locate Red Ball - Left
        transform = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "Transform", "myTransform")
        if transform:
            transform.translation = (-5.0, 0.0, 0.0)
            
            ###########################################
            # Create the Shape node
            shape = self.trv.processBasicNodeAddition(transform, "children", "Shape", "shapeOne")
            if shape:
                print("shapeOne Node did NOT already exist.")
                
                #############################################
                # Create Sphere primative for the Shape's geometry
                sphere = self.trv.processBasicNodeAddition(shape, "geometry",   "Sphere",     "myBall")

                #############################################
                # Create Appearance node for the Shape's appearance
                appearance = self.trv.processBasicNodeAddition(shape, "appearance", "Appearance", "appOne")
                if appearance:
                    #############################################
                    # Create Material node for the Appearance and set it's diffuseColor field to a Red value
                    material = self.trv.processBasicNodeAddition(appearance, "material", "Material", "red")
                    if material:
                        material.diffuseColor = (1.0, 0.0, 0.0)
            else:
                print("shapeOne Node DID already exist.")

        ###############################################
        # Create and Locate Green Ball - Right
        transform = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "Transform", "otherTransform")
        if transform:
            transform.translation = (5.0, 0.0, 0.0)
            
            ###########################################
            # Create the Shape node
            shape = self.trv.processBasicNodeAddition(transform, "children", "Shape", "shapeTwo")
            if shape:
                print("shapeTwo Node did NOT already exist.")
                
                #############################################
                # Create Sphere primative for the Shape's geometry
                sphere = self.trv.processBasicNodeAddition(shape, "geometry",   "Sphere",     "myBall")

                #############################################
                # Create Appearance node for the Shape's appearance
                appearance = self.trv.processBasicNodeAddition(shape, "appearance", "Appearance", "appTwo")
                if appearance:

                    #############################################
                    # Create Material node for the Appearance and set it's diffuseColor field to a Green value
                    material = self.trv.processBasicNodeAddition(appearance, "material", "Material", "green")
                    if material:
                        material.diffuseColor = (0.0, 1.0, 0.0)
            else:
                print("shapeTwo Node DID already exist.")

        ###############################################
        # Locate and USE Red Ball - Top
        transform = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "Transform", "myTransform2")
        if transform:
            transform.translation = (0.0, 5.0, 0.0)
            
            shape = self.trv.processBasicNodeAddition(transform, "children", "Shape", "shapeOne")
            if shape:
                print("shapeOne Node did NOT already exist.")
            else:
                print("shapeOne Node DID already exist.")

        ###############################################
        # Locate and USE Green Ball - Bottom
        transform = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "Transform", "otherTransform2")
        if transform:
            transform.translation = (0.0, -5.0, 0.0)
            
            shape = self.trv.processBasicNodeAddition(transform, "children", "Shape", "shapeTwo")
            if shape:
                print("shapeTwo Node did NOT already exist.")
            else:
                print("shapeTwo Node DID already exist.")

        ###############################################
        # Create Viewpoint (aka camera)
        viewpoint = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "Viewpoint", "mainView")
        if viewpoint:
            viewpoint.position = (0.0, 0.0, 20.0)

        ###############################################
        # Create a DirectionalLight
        directionalLight = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "DirectionalLight", "dirLight")
        if directionalLight:
            directionalLight.direction = (-1.0, 0.0, -1.0)
            
        ###############################################
        # Create a NavigationInfo
        navInfo = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "NavigationInfo", "navInfo")
        if navInfo:
            navInfo.headlight = False

        self.trv.x3d2disk(x3dDoc, self.exportFilePath, self.enc)

example = RKExample()
example.printExampleFilePath()
example.exportExample()

