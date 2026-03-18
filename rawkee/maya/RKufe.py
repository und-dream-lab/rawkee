import maya.cmds as cmds
import ufe


def getMatXSurfaceMaterialSceneItem(ufePath):
    ssPath = ufe.PathString.path(ufePath)
    ssItem = ufe.Hierarchy.createItem(ssPath)
    
    return ssItem
    
# TODO check for Compound node
def getMatXSurfaceShaderSceneItem(smSceneItem):
    pass
