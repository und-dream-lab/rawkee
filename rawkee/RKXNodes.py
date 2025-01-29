from rawkee.RKXGraphicsNode  import RKXGraphicsNode 
from rawkee.RKXContentWidget import RKXContentWidget
from rawkee.RKXSocket        import *

class RKXNode():
    def __init__(self, scene, title="Undefined Node", inputs=[], outputs=[]):
        self.scene = scene
        
        self.title = title
        
        self.content = RKXContentWidget()
        self.grNode = RKXGraphicsNode(self)
        
        self.scene.add_eNode(self)
        self.scene.grScene.addItem(self.grNode)
        
        self.socket_spacing = 22
        
        # create sockets for inputs and outputs
        self.inputs  = []
        self.outputs = []
        
        counter = 0
        for item in inputs:
            socket = RKXSocket(eNode=self, index=counter, position=LEFT_BOTTOM )
            self.inputs.append(socket)
            counter += 1
        
        counter = 0
        for item in outputs:
            socket = RKXSocket(eNode=self, index=counter, position=RIGHT_TOP, isOutput=True)
            self.outputs.append(socket)
            counter += 1

    @property
    def pos(self):
        return self.grNode.pos() #Returns a QPOintF class - so expeect to do pos.x, pos.y on the return to get the X,Y

    def setPos(self, x, y):
        self.grNode.setPos(x, y)

        
    def getSocketPosition(self, index, position):
        x = 0 if (position in (LEFT_TOP, LEFT_BOTTOM)) else self.grNode.width
        if position in (LEFT_BOTTOM, RIGHT_BOTTOM):
            # Start from bottom
            y = self.grNode.height - self.grNode.edge_size - self.grNode._padding - index * self.socket_spacing
        else:
            # Start from top
            y = (self.grNode.title_height * self.grNode._padding) + self.grNode.edge_size + (index * self.socket_spacing)

        return x, y


