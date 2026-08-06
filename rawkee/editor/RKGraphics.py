from PySide6.QtGui     import *
from PySide6.QtWidgets import *
from PySide6.QtCore    import *

import math
    

class RKGraphicsScene(QGraphicsScene):
    
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        
        self.scene = scene
        
        #Settings
        self.gridSize          = 20
        self.gridSquares       = 5
        self._color_background = QColor("#393939")
        self._color_light      = QColor("#494949")
        self._color_dark       = QColor("#3f3f3f")
        
        self._pen_light        = QPen(self._color_light)
        self._pen_light.setWidth(1)
        
        self._pen_dark         = QPen(self._color_light)
        self._pen_dark.setWidth(2)
        
        self.setBackgroundBrush(self._color_background)
        
    def setGrScene(self, width, height):
        self.setSceneRect(-width//2, -height//2, width, height)
        
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        # Here we create our Grid - Booyah!!!
        left   = int(math.floor(rect.left()))
        right  = int(math.ceil(rect.right()))
        top    = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))
        
        first_left = left - (left % self.gridSize)
        first_top  = top  - (top  % self.gridSize)
        
        
        # Computer all lines to be drawn
        lines_light, lines_dark = [], []
        for x in range(first_left, right, self.gridSize):
            if (x % (self.gridSize * self.gridSquares) != 0):
                lines_light.append(QLine(x, top, x, bottom))
            else:
                lines_dark.append( QLine(x, top, x, bottom))
            
        for y in range(first_top, bottom, self.gridSize):
            if (y % (self.gridSize * self.gridSquares) !=0):
                lines_light.append(QLine(left, y, right, y))
            else:
                lines_dark.append( QLine(left, y, right, y))
        
        # Draw the lines
        # Unlike the tutorial - do not use: *lines_light in the drawLines() method, just use the list as is.
        painter.setPen(self._pen_light)
        painter.drawLines(lines_light)
        
        painter.setPen(self._pen_dark)
        painter.drawLines(lines_dark)



class RKGraphicsView(QGraphicsView):
    
    def __init__(self, grScene, parent=None):
        super().__init__(parent)
        
        self.grScene = grScene
        
        self.initUI()
        
        self.setScene(self.grScene)

        self.zoomInFactor = 1.25
        self.zoomClamp = True
        self.zoom = 10
        self.zoomStep = 1
        self.zoomRange = [0, 20]

        self._drag_start_socket = None
        self._drag_edge         = None
        self._add_node_cb       = None

    def set_add_node_callback(self, fn):
        self._add_node_cb = fn

        
    def initUI(self):
        # At least in PySide6 - Tutorial's use of HighQualityAntialiasing is not supported
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        
        #Fixes Redraw Issue where when moving objects, the background grid would not get redrawng correctly.
        self.setViewportUpdateMode(RKGraphicsView.FullViewportUpdate)
        
        #Hide ScrollBars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        #Force zoom to translate to point under mouse cursor during zoom
        self.setTransformationAnchor(RKGraphicsView.AnchorUnderMouse)

        
    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middleMouseButtonPress(event)
        elif event.button() == Qt.LeftButton:
            self.leftMouseButtonPress(event)
        elif event.button() == Qt.RightButton:
            self.rightMouseButtonPress(event)
        else:
            super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middleMouseButtonRelease(event)
        elif event.button() == Qt.LeftButton:
            self.leftMouseButtonRelease(event)
        elif event.button() == Qt.RightButton:
            self.rightMouseButtonRelease(event)
        else:
            super().mouseReleaseEvent(event)
            
    def leftMouseButtonPress(self, event):
        from rawkee.editor.RKXGraphicsSocket import RKXGraphicsSocket
        item = self.itemAt(event.pos())
        if isinstance(item, RKXGraphicsSocket):
            self._begin_drag_edge(item)
            return
        super().mousePressEvent(event)
        
    def leftMouseButtonRelease(self, event):
        if self._drag_start_socket is not None:
            from rawkee.editor.RKXGraphicsSocket import RKXGraphicsSocket
            item = self.itemAt(event.pos())
            if isinstance(item, RKXGraphicsSocket) and item is not self._drag_start_socket:
                self._complete_drag_edge(item)
            else:
                self._cancel_drag_edge()
            return
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_edge is not None:
            self._drag_edge.setDestPos(self.mapToScene(event.pos()))
            self._drag_edge.update()
        super().mouseMoveEvent(event)

    def _begin_drag_edge(self, gr_socket):
        from rawkee.editor.RKXGraphicsEdge import RKXGraphicsEdge
        self._drag_start_socket = gr_socket
        self._drag_edge = RKXGraphicsEdge(None)
        self.grScene.addItem(self._drag_edge)
        src = gr_socket.scenePos()
        self._drag_edge.setSourcePos(src)
        self._drag_edge.setDestPos(src)
        self._drag_edge.update()

    def _complete_drag_edge(self, end_gr_socket):
        from rawkee.editor.RKXEdge import RKXEdge
        self.grScene.removeItem(self._drag_edge)
        self._drag_edge = None
        start, end = self._drag_start_socket, end_gr_socket
        self._drag_start_socket = None
        # Enforce output → input direction
        if start.isOutput and not end.isOutput:
            pass
        elif end.isOutput and not start.isOutput:
            start, end = end, start
        else:
            return  # both same direction — reject
        start_sock = getattr(start, 'socket', None)
        end_sock   = getattr(end,   'socket', None)
        if start_sock and end_sock:
            RKXEdge(self.grScene.scene, start_sock, end_sock)

    def _cancel_drag_edge(self):
        if self._drag_edge is not None:
            self.grScene.removeItem(self._drag_edge)
        self._drag_edge         = None
        self._drag_start_socket = None

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            from rawkee.editor.RKXGraphicsEdge import RKXGraphicsEdge
            for item in self.grScene.selectedItems():
                if isinstance(item, RKXGraphicsEdge) and item.edge is not None:
                    self._delete_edge(item.edge)
            return
        super().keyPressEvent(event)

    def _delete_edge(self, edge):
        edge.remove()

    def contextMenuEvent(self, event):
        from rawkee.editor.RKXGraphicsEdge import RKXGraphicsEdge
        gr_node = self._find_graphics_node_at(event.pos())
        gr_edge = self._find_graphics_edge_at(event.pos())
        menu = QMenu(self)
        menu.setStyleSheet("QMenu::separator { background: #39FF14; height: 2px; margin: 2px 4px; }")
        if gr_edge is not None and gr_edge.edge is not None:
            action = menu.addAction("Delete Route")
            if menu.exec(event.globalPos()) == action:
                self._delete_edge(gr_edge.edge)
        elif gr_node is not None:
            action_fit   = menu.addAction("Fit Node to View")
            menu.addSeparator()
            action_graph = menu.addAction("Display All Nodes in Connected Graph")
            menu.addSeparator()
            action_both  = menu.addAction("Display Connected Adjacent Nodes")
            action_up    = menu.addAction("Display Upstream Adjacent Nodes")
            action_down  = menu.addAction("Display Downstream Adjacent Nodes")
            menu.addSeparator()
            action_clear = menu.addAction("Clear From Graph Editor")
            chosen = menu.exec(event.globalPos())
            if chosen == action_fit:
                from PySide6.QtCore import Qt
                self.fitInView(gr_node.sceneBoundingRect().adjusted(-40, -40, 40, 40), Qt.KeepAspectRatio)
            elif chosen == action_clear:
                self._remove_node(gr_node)
            elif chosen == action_both:
                self._add_adjacent_nodes(gr_node, 'both')
            elif chosen == action_up:
                self._add_adjacent_nodes(gr_node, 'upstream')
            elif chosen == action_down:
                self._add_adjacent_nodes(gr_node, 'downstream')
            elif chosen == action_graph:
                self._add_connected_graph_nodes(gr_node)
        else:
            action_add   = menu.addAction("Add Node")
            menu.addSeparator()
            action_clear = menu.addAction("Clear Graph Editor")
            chosen = menu.exec(event.globalPos())
            if chosen == action_add and self._add_node_cb is not None:
                self._add_node_cb(self.mapToScene(event.pos()))
            elif chosen == action_clear:
                self.grScene.scene.clear_graph()

    def _add_adjacent_nodes(self, gr_node, direction):
        """Add graph editor nodes for X3D nodes connected via ROUTEs ('upstream'|'downstream'|'both')."""
        from PySide6.QtCore import QPointF

        x3d_scene = self.grScene.scene._x3d_scene
        if x3d_scene is None:
            return

        def_val = getattr(getattr(gr_node.eNode, 'x3d_node', None), 'DEF', '')
        if not def_val:
            return

        parent_editor = self.parent()
        if not hasattr(parent_editor, 'addNodeFromX3D'):
            return

        # Build DEF→node map; prefer the tree registry (includes nested nodes)
        def_map = {}
        if hasattr(parent_editor, '_tree_widget') and parent_editor._tree_widget is not None:
            for node in parent_editor._tree_widget._node_registry.values():
                d = getattr(node, 'DEF', '')
                if d:
                    def_map[d] = node
        else:
            for child in x3d_scene.children:
                d = getattr(child, 'DEF', '')
                if d:
                    def_map[d] = child

        upstream_defs   = []
        downstream_defs = []
        for child in x3d_scene.children:
            if not hasattr(child, 'fromNode'):
                continue
            if direction in ('upstream', 'both') and child.toNode == def_val:
                if child.fromNode not in upstream_defs:
                    upstream_defs.append(child.fromNode)
            if direction in ('downstream', 'both') and child.fromNode == def_val:
                if child.toNode not in downstream_defs:
                    downstream_defs.append(child.toNode)

        node_pos   = gr_node.pos()
        spacing_x  = gr_node.width + 80
        spacing_y  = 200

        for i, adj_def in enumerate(upstream_defs):
            if adj_def in def_map:
                place = QPointF(node_pos.x() - spacing_x * 1.5, node_pos.y() + i * spacing_y)
                parent_editor.addNodeFromX3D(def_map[adj_def], place)

        for i, adj_def in enumerate(downstream_defs):
            if adj_def in def_map:
                place = QPointF(node_pos.x() + spacing_x * 1.5, node_pos.y() + i * spacing_y)
                parent_editor.addNodeFromX3D(def_map[adj_def], place)

        # Center the view on all nodes now visible in the graph
        from PySide6.QtCore import Qt
        self.fitInView(self.grScene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def _add_connected_graph_nodes(self, gr_node):
        """BFS through all ROUTEs in both directions to add every reachable node."""
        from PySide6.QtCore import QPointF, Qt

        x3d_scene = self.grScene.scene._x3d_scene
        if x3d_scene is None:
            return

        start_def = getattr(getattr(gr_node.eNode, 'x3d_node', None), 'DEF', '')
        if not start_def:
            return

        parent_editor = self.parent()
        if not hasattr(parent_editor, 'addNodeFromX3D'):
            return

        def_map = {}
        if hasattr(parent_editor, '_tree_widget') and parent_editor._tree_widget is not None:
            for node in parent_editor._tree_widget._node_registry.values():
                d = getattr(node, 'DEF', '')
                if d:
                    def_map[d] = node
        else:
            for child in x3d_scene.children:
                d = getattr(child, 'DEF', '')
                if d:
                    def_map[d] = child

        # Build adjacency: for each DEF, collect all DEFs connected via any ROUTE
        adjacency = {}
        for child in x3d_scene.children:
            if not hasattr(child, 'fromNode'):
                continue
            fn, tn = child.fromNode, child.toNode
            adjacency.setdefault(fn, set()).add(tn)
            adjacency.setdefault(tn, set()).add(fn)

        # BFS from start_def
        visited = set()
        queue   = [start_def]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for neighbour in adjacency.get(current, []):
                if neighbour not in visited:
                    queue.append(neighbour)

        # Layout: column per BFS depth layer
        from collections import deque
        layers   = {start_def: 0}
        bfs_q    = deque([start_def])
        while bfs_q:
            cur = bfs_q.popleft()
            for nb in adjacency.get(cur, []):
                if nb not in layers:
                    layers[nb] = layers[cur] + 1
                    bfs_q.append(nb)

        layer_nodes = {}
        for d, l in layers.items():
            if d in visited:
                layer_nodes.setdefault(l, []).append(d)

        node_pos  = gr_node.pos()
        spacing_x = (gr_node.width if hasattr(gr_node, 'width') else 220) + 80
        spacing_y = 200

        for layer, defs in layer_nodes.items():
            x = node_pos.x() + layer * spacing_x
            for row, d in enumerate(defs):
                if d == start_def:
                    continue
                if d in def_map:
                    y = node_pos.y() + row * spacing_y
                    parent_editor.addNodeFromX3D(def_map[d], QPointF(x, y))

        self.fitInView(self.grScene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def _find_graphics_node_at(self, pos):
        from rawkee.editor.RKXGraphicsNode import RKXGraphicsNode as GrNode
        item = self.itemAt(pos)
        while item is not None:
            if isinstance(item, GrNode):
                return item
            item = item.parentItem()
        return None

    def _find_graphics_edge_at(self, pos):
        from rawkee.editor.RKXGraphicsEdge import RKXGraphicsEdge
        for item in self.items(pos):
            if isinstance(item, RKXGraphicsEdge):
                return item
        return None

    def _remove_node(self, gr_node):
        eNode = gr_node.eNode
        scene = self.grScene.scene
        s_ids = set(id(s) for s in eNode.inputs + eNode.outputs)
        for edge in [e for e in list(scene.eEdges)
                     if id(e.start_socket) in s_ids or id(e.end_socket) in s_ids]:
            # Remove visual edge only; preserve the ROUTE in the X3D scene
            if edge.grEdge is not None:
                scene.grScene.removeItem(edge.grEdge)
            if edge in scene.eEdges:
                scene.eEdges.remove(edge)
        scene.grScene.removeItem(gr_node)
        if eNode in scene.eNodes:
            scene.eNodes.remove(eNode)

    def rightMouseButtonPress(self, event):
        return super().mousePressEvent(event)
        
    def rightMouseButtonRelease(self, event):
        return super().mouseReleaseEvent(event)
    
    # Middle Mouse Button Event overrides that implement middle mouse button scene dragging.
    def middleMouseButtonPress(self, event):
        releaseEvent = QMouseEvent(QEvent.Type.MouseButtonRelease, event.position(), event.globalPosition(), Qt.LeftButton, Qt.NoButton, event.modifiers())
        super().mouseReleaseEvent(releaseEvent)
        self.setDragMode(RKGraphicsView.ScrollHandDrag)
        fakeEvent = QMouseEvent(event.type(), event.position(), event.globalPosition(), Qt.LeftButton, event.buttons() | Qt.LeftButton, event.modifiers())
        super().mousePressEvent(fakeEvent)

    def middleMouseButtonRelease(self, event):
        fakeEvent = QMouseEvent(event.type(), event.position(), event.globalPosition(), Qt.LeftButton, event.buttons() | Qt.LeftButton, event.modifiers())
        super().mouseReleaseEvent(fakeEvent)
        self.setDragMode(RKGraphicsView.NoDrag)
    
    # Mouse Wheel Event override that Zooms the scene in/out if the mouse wheel is scrolled.
    def wheelEvent(self, event):

        #Calculate our Zoom Factor
        zoomOutFactor = 1 / self.zoomInFactor

        #Calcualte the zoom
        if event.angleDelta().y() > 0:
            zoomFactor = self.zoomInFactor
            self.zoom += self.zoomStep
        else:
            zoomFactor = zoomOutFactor
            self.zoom -= self.zoomStep

        clamped = False

        if self.zoom < self.zoomRange[0]:
            self.zoom, clamped = self.zoomRange[0], True
        if self.zoom > self.zoomRange[1]:
            self.zoom, clamped = self.zoomRange[1], True

        #Set scene scale
        if not clamped or self.zoomClamp is False:
            self.scale(zoomFactor, zoomFactor)
