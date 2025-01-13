import xmltodict
import json
import x3d
from x3d import *

x3dScene = Scene()

x3dShape = Shape()

x3dSphere = Sphere()

x3dShape.geometry = x3dSphere

x3dSphere.DEF = "Fun"

x3dScript = Script()

x3dScript.sourceCode = "ecmascript: "

myList = [x3dShape, x3dScript]

x3dScene.children = myList

x3dDoc = X3D(profile="Full", version="4.0")

print(x3dDoc.XML())

x3dTrans = Transform()#translation=(0.0,0.0,0.0))
x3dTrans2 = Transform(translation=(3.0,0.0,0.0), rotation=(0.3,4.3,30.21,0.0))

setattr(x3dTrans, "translation", (3.0,4.5,3.0))

tVals = getattr(x3dTrans2, "rotation")
print("Rotation: " + str(tVals[0]) + ","  + str(tVals[1]) + ","  + str(tVals[2]) + ","  + str(tVals[3]))

x3dTrans.DEF = "Garb"
x3dTrans.children = [x3dTrans2]

print("Doh!")

x3dScene.children.append(x3dTrans)

x3dDoc.Scene = x3dScene

print(x3dDoc.XML())
print("great!")

xpars = xmltodict.parse(x3dDoc.XML())
js = json.dumps(xpars, indent=4)
print(js)

print(x3dDoc.VRML())
print(x3dDoc.HTML5())
