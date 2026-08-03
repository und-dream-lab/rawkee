from PySide6.QtCore import QPointF


class RKXEdge:
    """
    Represents a directed connection between two RKXSocket instances in the scene graph.
    start_socket must be an output socket; end_socket must be an input socket.
    Corresponds to an X3D ROUTE when both ends are connected.
    """

    def __init__(self, scene, start_socket=None, end_socket=None):
        self.scene        = scene
        self.start_socket = start_socket  # output socket (source)
        self.end_socket   = end_socket    # input socket  (destination)

        from rawkee.editor.RKXGraphicsEdge import RKXGraphicsEdge
        self.grEdge = RKXGraphicsEdge(self)

        self.scene.add_eEdge(self)
        self.scene.grScene.addItem(self.grEdge)

        self.updatePositions()

    # ------------------------------------------------------------------
    def updatePositions(self):
        self.grEdge.setSourcePos(self._socket_scene_pos(self.start_socket))
        self.grEdge.setDestPos(self._socket_scene_pos(self.end_socket))
        self.grEdge.update()

    def _socket_scene_pos(self, socket):
        if socket is None:
            return QPointF(0.0, 0.0)
        lx, ly = socket.eNode.getSocketPosition(socket.index, socket.position)
        node_pos = socket.eNode.grNode.pos()
        return QPointF(node_pos.x() + lx, node_pos.y() + ly)

    # ------------------------------------------------------------------
    def remove(self):
        self.scene.grScene.removeItem(self.grEdge)
        self.scene.remove_eEdge(self)
        self.grEdge = None
