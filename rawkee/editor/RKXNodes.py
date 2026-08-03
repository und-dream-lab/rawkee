from rawkee.editor.RKXGraphicsNode  import RKXGraphicsNode 
from rawkee.editor.RKXContentWidget import RKXContentWidget
from rawkee.editor.RKXSocket        import *

class RKXNode():
    @staticmethod
    def _norm(fields):
        """Accept [(name, type)] or [name] and always return [(name, type)]."""
        result = []
        for f in fields:
            if isinstance(f, (list, tuple)) and len(f) >= 2:
                result.append((str(f[0]), str(f[1])))
            else:
                result.append((str(f), ''))
        return result

    def __init__(self, scene, title="Undefined Node", inputs=[], outputs=[], x3d_node=None, node_type=''):
        self.scene = scene
        
        self.title    = title
        self.x3d_node = x3d_node
        self.input_fields  = self._norm(inputs)
        self.output_fields = self._norm(outputs)
        
        self.content = RKXContentWidget()
        self.content.setNodeType(node_type)
        self.grNode = RKXGraphicsNode(self)

        self.socket_spacing = 22

        # Compute height before placing sockets so positions are correct
        n_out = len(self.output_fields)
        n_in  = len(self.input_fields)
        top_start = int(self.grNode.title_height * self.grNode._padding) + self.grNode.edge_size
        bot_start = self.grNode.edge_size + int(self.grNode._padding)
        # Height spans max(n_in, n_out) rows so inputs and outputs share the same Y range
        n = max(n_in, n_out, 1)
        needed = top_start + (n - 1) * self.socket_spacing + bot_start
        self.grNode.height = max(needed, 100)
        self.grNode.initContent()

        self.scene.add_eNode(self)
        self.scene.grScene.addItem(self.grNode)

        # create sockets for inputs and outputs
        self.inputs  = []
        self.outputs = []

        for counter, (field_name, field_type) in enumerate(self.input_fields):
            socket = RKXSocket(eNode=self, index=counter, position=LEFT_BOTTOM, field_type=field_type, field_name=field_name)
            self.inputs.append(socket)

        for counter, (field_name, field_type) in enumerate(self.output_fields):
            socket = RKXSocket(eNode=self, index=counter, position=RIGHT_TOP, isOutput=True, field_type=field_type, field_name=field_name)
            self.outputs.append(socket)

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

    def _resize_for_sockets(self):
        """Recompute node height from current socket counts; reposition input sockets."""
        n_out = len(self.output_fields)
        n_in  = len(self.input_fields)
        top_start = int(self.grNode.title_height * self.grNode._padding) + self.grNode.edge_size
        bot_start = self.grNode.edge_size + int(self.grNode._padding)
        n = max(n_in, n_out, 1)
        needed = top_start + (n - 1) * self.socket_spacing + bot_start
        new_height = max(needed, 100)
        if new_height == self.grNode.height:
            return
        self.grNode.prepareGeometryChange()
        self.grNode.height = new_height
        self.grNode.initContent()
        for sock in self.inputs:
            sock.grSocket.setPos(*self.getSocketPosition(sock.index, LEFT_BOTTOM))
        self.grNode.update()


