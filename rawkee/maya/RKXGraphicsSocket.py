try:
    #Qt5
    from PySide2.QtWidgets import *
    from PySide2.QtCore    import *
    from PySide2.QtGui     import *

except:
    #Qt6
    from PySide6.QtWidgets import *
    from PySide6.QtCore    import *
    from PySide6.QtGui     import *
 
class RKXGraphicsSocket(QGraphicsItem):
    def __init__(self, parent=None, isOutput=False):
        super().__init__(parent)

        self.isOutput = isOutput
        
        self._und_green         = QColor("#FF009A44")
        self._und_green_trans   = QColor("#55009A44")
        self._und_green_ptrans  = QColor("#CC009A44")
        self._und_orange        = QColor("#FFFF671F")
        self._und_orange_trans  = QColor("#55FF671F")
        self._und_orange_ptrans = QColor("#CCFF671F")
        self._und_pink          = QColor("#FFF5B6CD")
        self._und_pink_trans    = QColor("#55F5B6CD")
        self._und_pink_ptrans   = QColor("#CCF5B6CD")
        
        self.outline_width      = 1.0
        
        self._und_black         = QColor(Qt.black)
        
        self.radius = 6.0
        if self.isOutput:
            self._color_background = self._und_green
        else:
            self._color_background = self._und_orange
        self._color_outline    = self._und_black
        
        self._pen   = QPen(self._color_outline)
        self._brush = QBrush(self._color_background)
        
        self._pen.setWidthF(self.outline_width)

        
    def boundingRect(self):
        # Return the bounding rectangle of your item
        return QRectF(
            -self.radius - self.outline_width, 
            -self.radius - self.outline_width,
            2 * (self.radius - self.outline_width),
            2 * (self.radius - self.outline_width)
            ).normalized()


    def paint (self, painter, options, widget=None):
        
        #painting cirlce
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

