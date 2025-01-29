from rawkee.RKXGraphicsSocket import RKXGraphicsSocket

LEFT_TOP = 1
LEFT_BOTTOM = 2
RIGHT_TOP = 3
RIGHT_BOTTOM = 4


class RKXSocket():
    def __init__(self, eNode, index=0, position=LEFT_TOP, isOutput=False):
        
        self.eNode = eNode
        self.index = index
        self.position = position
        self.isOutput = isOutput
        
        self.grSocket = RKXGraphicsSocket(self.eNode.grNode, isOutput)

        self.grSocket.setPos(*self.eNode.getSocketPosition(index, position))
