import rawkee.io.RKx3d as rkx
from rawkee.editor.RKGraphics import RKGraphicsScene

def _is_inputoutput_field(field_name, x3d_node):
    """Return True only if field_name is declared inputOutput on x3d_node's type."""
    if not hasattr(type(x3d_node), 'FIELD_DECLARATIONS'):
        return False
    for decl in type(x3d_node).FIELD_DECLARATIONS():
        try:
            access_str = decl[3]()
        except Exception:
            continue
        if decl[0] == field_name and access_str == 'inputOutput':
            return True
    return False


def _fields_match(name_a, name_b, x3d_node):
    """True if name_a and name_b name the same routable event on x3d_node.
    set_foo / foo_changed are treated as aliases only when foo is inputOutput."""
    if name_a == name_b:
        return True
    for raw, aliased in ((name_a, name_b), (name_b, name_a)):
        if aliased.endswith('_changed') and aliased[:-8] == raw:
            if _is_inputoutput_field(raw, x3d_node):
                return True
        elif aliased.startswith('set_') and aliased[4:] == raw:
            if _is_inputoutput_field(raw, x3d_node):
                return True
    return False

# Field types that are implicitly compatible for ROUTE purposes
_COMPAT_GROUPS = [
    {'SFFloat', 'SFDouble', 'SFTime'},
    {'MFFloat', 'MFDouble', 'MFTime'},
]

def _types_compatible(t1, t2):
    if t1 == t2:
        return True
    for group in _COMPAT_GROUPS:
        if t1 in group and t2 in group:
            return True
    # SFNode and MFNode fields are routable when both sides match
    if t1 in ('SFNode', 'MFNode') and t2 in ('SFNode', 'MFNode'):
        return True
    return False

class RKXScene(rkx.Scene):# class X3D_Transform (aom.MPxNode, x3d.Transform):
    
    def __init__(self):
        super().__init__()
        
        self.eNodes = []
        self.eEdges = []
        self._x3d_scene = None  # reference to rkx.Scene; used for ROUTE insertion
        
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
        self._add_route_for_edge(eEdge)
        
    def remove_eNode(self, eNode):
        self.eNodes.remove(eNode)
        
    def remove_eEdge(self, eEdge):
        self._remove_route_for_edge(eEdge)
        self.eEdges.remove(eEdge)

    def _remove_route_for_edge(self, edge):
        """When an edge is removed, delete the corresponding ROUTE from the X3D scene."""
        if self._x3d_scene is None:
            return
        ss = edge.start_socket
        es = edge.end_socket
        if ss is None or es is None:
            return
        from_x3d = getattr(ss.eNode, 'x3d_node', None)
        to_x3d   = getattr(es.eNode, 'x3d_node', None)
        if from_x3d is None or to_x3d is None:
            return
        from_def = getattr(from_x3d, 'DEF', '')
        to_def   = getattr(to_x3d,   'DEF', '')
        if not from_def or not to_def:
            return
        out_fields = ss.eNode.output_fields
        in_fields  = es.eNode.input_fields
        if ss.index >= len(out_fields) or es.index >= len(in_fields):
            return
        from_field = out_fields[ss.index][0]
        to_field   = in_fields[es.index][0]
        if not from_field or not to_field:
            return
        self._x3d_scene.children = [
            c for c in self._x3d_scene.children
            if not (hasattr(c, 'fromNode') and
                    c.fromNode == from_def and
                    _fields_match(c.fromField, from_field, from_x3d) and
                    c.toNode   == to_def   and
                    _fields_match(c.toField, to_field, to_x3d))
        ]

    def set_x3d_scene(self, x3d_scene):
        self._x3d_scene = x3d_scene

    def clear_graph(self):
        """Remove all nodes and edges from the canvas without touching the scenegraph tree."""
        for edge in list(self.eEdges):
            if edge.grEdge is not None:
                self.grScene.removeItem(edge.grEdge)
        for node in list(self.eNodes):
            if node.grNode is not None:
                self.grScene.removeItem(node.grNode)
        self.eNodes.clear()
        self.eEdges.clear()

    def _add_route_for_edge(self, edge):
        """When a fully-connected edge is added, append a ROUTE to the X3D scene."""
        if self._x3d_scene is None:
            return
        if edge.start_socket is None or edge.end_socket is None:
            return
        from_x3d = getattr(edge.start_socket.eNode, 'x3d_node', None)
        to_x3d   = getattr(edge.end_socket.eNode,   'x3d_node', None)
        if from_x3d is None or to_x3d is None:
            return
        from_def = getattr(from_x3d, 'DEF', '')
        to_def   = getattr(to_x3d,   'DEF', '')
        if not from_def or not to_def:
            return
        out_fields = edge.start_socket.eNode.output_fields
        in_fields  = edge.end_socket.eNode.input_fields
        si = edge.start_socket.index
        ei = edge.end_socket.index
        if si >= len(out_fields) or ei >= len(in_fields):
            return
        from_field, from_type = out_fields[si]
        to_field,   to_type   = in_fields[ei]
        if not from_field or not to_field:
            return
        # Skip if an equivalent ROUTE already exists (legacy set_/_changed aliases for inputOutput only)
        for existing in self._x3d_scene.children:
            if (hasattr(existing, 'fromNode') and
                    existing.fromNode == from_def and
                    _fields_match(existing.fromField, from_field, from_x3d) and
                    existing.toNode   == to_def   and
                    _fields_match(existing.toField, to_field, to_x3d)):
                return
        route = rkx.ROUTE()
        route.fromNode  = from_def
        route.fromField = from_field
        route.toNode    = to_def
        route.toField   = to_field
        self._x3d_scene.children.append(route)

    def initUI(self):
        self.grScene = RKGraphicsScene(self)
        self.grScene.setGrScene(self.scene_width, self.scene_height)

    @classmethod
    def creator(cls):
        return RKScene()

    @classmethod
    def initialize(cls):
        pass
