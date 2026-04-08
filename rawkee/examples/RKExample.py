import sys
import os
from rawkee.io.RKSceneTraversal import *

example = RKExample()
example.printExample()
example.exportExample()

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


    def printExample(self):
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
        tr = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "Transform", "myTransform")
        if tr[0] == False:
            transform = tr[1]
            transform.translation = (-5.0, 0.0, 0.0)
            
            ###########################################
            # Create the Shape node
            sh = self.trv.processBasicNodeAddition(transform, "children", "Shape", "shapeOne")
            if sh[0] == False:
                shape = sh[1]
                print("shapeOne Node did NOT already exist.")
                
                #############################################
                # Create Sphere primative for the Shape's geometry
                # -- could use 'shape' or 'sh[1]' -- as x3dParentNode
                sph = self.trv.processBasicNodeAddition(sh[1], "geometry",   "Sphere",     "myBall")

                #############################################
                # Create Appearance node for the Shape's appearance
                # -- could use 'shape' or 'sh[1]' -- as x3dParentNode
                app = self.trv.processBasicNodeAddition(shape, "appearance", "Appearance", "appOne")
                if app[0] == False:
                    appearance = app[1]

                    #############################################
                    # Create Material node for the Appearance and set it's diffuseColor field to a Red value
                    mat = self.trv.processBasicNodeAddition(appearance, "material", "Material", "red")
                    if mat[0] == False:
                        mat[1].diffuseColor = (1.0, 0.0, 0.0)
            else:
                print("shapeOne Node DID already exist.")

        ###############################################
        # Create and Locate Green Ball - Right
        tr2 = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "Transform", "otherTransform")
        if tr2[0] == False:
            nTransform = tr2[1]
            nTransform.translation = (5.0, 0.0, 0.0)
            
            ###########################################
            # Create the Shape node
            sh2 = self.trv.processBasicNodeAddition(nTransform, "children", "Shape", "shapeTwo")
            if sh2[0] == False:
                shape2 = sh2[1]
                print("shapeTwo Node did NOT already exist.")
                
                #############################################
                # Create Sphere primative for the Shape's geometry
                sph2 = self.trv.processBasicNodeAddition(shape2, "geometry",   "Sphere",     "myBall")

                #############################################
                # Create Appearance node for the Shape's appearance
                app2 = self.trv.processBasicNodeAddition(shape2, "appearance", "Appearance", "appTwo")
                if app2[0] == False:
                    appearance2 = app2[1]

                    #############################################
                    # Create Material node for the Appearance and set it's diffuseColor field to a Green value
                    mat2 = self.trv.processBasicNodeAddition(appearance2, "material", "Material", "green")
                    if mat2[0] == False:
                        mat2[1].diffuseColor = (0.0, 1.0, 0.0)
            else:
                print("shapeTwo Node DID already exist.")

        ###############################################
        # Locate and USE Red Ball - Top
        tr3 = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "Transform", "myTransform2")
        if tr3[0] == False:
            transform3 = tr3[1]
            transform3.translation = (0.0, 5.0, 0.0)
            
            sh3 = self.trv.processBasicNodeAddition(transform3, "children", "Shape", "shapeOne")
            if sh3[0] == False:
                print("shapeOne Node did NOT already exist.")
            else:
                print("shapeOne Node DID already exist.")

        ###############################################
        # Locate and USE Green Ball - Bottom
        tr4 = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "Transform", "otherTransform2")
        if tr4[0] == False:
            nTransform4 = tr4[1]
            nTransform4.translation = (0.0, -5.0, 0.0)
            
            sh4 = self.trv.processBasicNodeAddition(nTransform4, "children", "Shape", "shapeTwo")
            if sh4[0] == False:
                print("shapeTwo Node did NOT already exist.")
            else:
                print("shapeTwo Node DID already exist.")

        ###############################################
        # Create Viewpoint (aka camera)
        vpt = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "Viewpoint", "mainView")
        if vpt[0] == False:
            vpt[1].position = (0.0, 0.0, 20.0)

        ###############################################
        # Create a DirectionalLight
        dlt = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "DirectionalLight", "dirLight")
        if dlt[0] == False:
            directionalLight = dlt[1]
            directionalLight.direction = (-1.0, 0.0, -1.0)
            
        ###############################################
        # Create a NavigationInfo
        nvi = self.trv.processBasicNodeAddition(x3dDoc.Scene, "children", "NavigationInfo", "navInfo")
        if nvi[0] == False:
            navInfo = nvi[1]
            navInfo.headlight = False

        self.trv.x3d2disk(x3dDoc, self.exportFilePath, self.enc)
