from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui     import QPen, QColor, QPainterPath, QPainterPathStroker
from PySide6.QtCore    import Qt, QPointF


class RKXGraphicsEdge(QGraphicsPathItem):
    """
    Cubic Bezier connector drawn between two sockets in the node editor canvas.
    Positions are updated via setSourcePos / setDestPos, then update() is called
    by RKXEdge.updatePositions().
    """

    def __init__(self, edge, parent=None):
        super().__init__(parent)
        self.edge = edge

        self._color          = QColor("#FF009A44")   # UND green — connected
        self._color_selected = QColor("#FFFF671F")   # orange — selected
        self._color_dragging = QColor("#39FF14")     # neon green — in-progress drag

        self._pen = QPen(self._color)
        self._pen.setWidthF(2.0)

        self._pen_selected = QPen(self._color_selected)
        self._pen_selected.setWidthF(2.0)

        self._pen_dragging = QPen(self._color_dragging)
        self._pen_dragging.setWidthF(2.0)
        self._pen_dragging.setStyle(Qt.DashLine)

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(-1)  # draw beneath nodes

        self._src_pos = QPointF(0.0, 0.0)
        self._dst_pos = QPointF(0.0, 0.0)

    # ------------------------------------------------------------------
    def setSourcePos(self, pos: QPointF):
        self._src_pos = pos

    def setDestPos(self, pos: QPointF):
        self._dst_pos = pos

    # ------------------------------------------------------------------
    def _calcPath(self) -> QPainterPath:
        path = QPainterPath(self._src_pos)
        # Horizontal Bezier: control points are offset along X by half the distance
        dist = abs(self._dst_pos.x() - self._src_pos.x()) / 2.0
        ctrl1 = QPointF(self._src_pos.x() + dist, self._src_pos.y())
        ctrl2 = QPointF(self._dst_pos.x() - dist, self._dst_pos.y())
        path.cubicTo(ctrl1, ctrl2, self._dst_pos)
        return path

    # ------------------------------------------------------------------
    def boundingRect(self):
        return self.shape().boundingRect()

    def shape(self):
        # Widen the hit area to ~10px so right-click detection works reliably
        stroker = QPainterPathStroker()
        stroker.setWidth(10.0)
        return stroker.createStroke(self._calcPath())

    def paint(self, painter, option, widget=None):
        self.setPath(self._calcPath())
        pen = self._pen_selected if self.isSelected() else self._pen
        # Use dashed style when destination is not yet connected
        if self.edge is None or self.edge.end_socket is None:
            pen = self._pen_dragging
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())
