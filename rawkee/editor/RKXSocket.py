from rawkee.editor.RKXGraphicsSocket import RKXGraphicsSocket

LEFT_TOP = 1
LEFT_BOTTOM = 2
RIGHT_TOP = 3
RIGHT_BOTTOM = 4


class RKXSocket():
    def __init__(self, eNode, index=0, position=LEFT_TOP, isOutput=False, field_type='', field_name=''):
        
        self.eNode      = eNode
        self.index      = index
        self.position   = position
        self.isOutput   = isOutput
        self.field_type = field_type
        self.field_name = field_name
        
        self.grSocket = RKXGraphicsSocket(self.eNode.grNode, isOutput, field_type, field_name)
        self.grSocket.socket = self  # back-reference for drag-to-connect

        self.grSocket.setPos(*self.eNode.getSocketPosition(index, position))
