import sys
import x3d as rkx
from rawkee.RKGraphics import RKGraphicsScene

class RKXScene(rkx.Scene):# class X3D_Transform (aom.MPxNode, x3d.Transform):
    
    def __init__(self):
        super().__init__()
        #super(RKScene, self).__init__()
		#x3d.Transform.__init__(self)
        
        self.eNodes = []
        self.eEdges = []
        
        self.scene_width  = 64000
        self.scene_height = 64000
        
        self.initUI()
    
    ###################################################################
    # Used 'add_eNode' instead of 'addNode' to void overlapping with 
    # any potential X3D methods of a similar name.
    # Same goes for eNode, eEdge, add_eEdge, remove_eNode, remove_eEdge
    ###################################################################
    def add_eNode(self, eNode):
        self.eNodes.append(eNode)
        
    def add_eEdge(self, eEdge):
        self.eEdges.append(eEdge)
        
    def remove_eNode(self, eNode):
        self.eNodes.remove(eNode)
        
    def remove_eEdge(self, eEdge):
        self.eEdges.remove(eEdge)
        
    def initUI(self):
        self.grScene = RKGraphicsScene(self)
        self.grScene.setGrScene(self.scene_width, self.scene_height)

        

    @classmethod
    def creator(cls):
        return RKScene()

    @classmethod
    def initialize(cls):
        pass
