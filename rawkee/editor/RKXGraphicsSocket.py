from PySide6.QtWidgets import *
from PySide6.QtCore    import *
from PySide6.QtGui     import *

# Socket fill color keyed by X3D field type; falls back to input/output default
_TYPE_COLORS = {
    'SFBool':      '#999999', 'MFBool':      '#999999',
    'SFInt32':     '#00BFFF', 'MFInt32':     '#00BFFF',
    'SFFloat':     '#7FFF00', 'MFFloat':     '#7FFF00',
    'SFDouble':    '#7FFF00', 'MFDouble':    '#7FFF00',
    'SFTime':      '#7FFF00', 'MFTime':      '#7FFF00',
    'SFVec2f':     '#FFD700', 'MFVec2f':     '#FFD700',
    'SFVec3f':     '#FFD700', 'MFVec3f':     '#FFD700',
    'SFVec4f':     '#FFD700', 'MFVec4f':     '#FFD700',
    'SFVec2d':     '#FFD700', 'MFVec2d':     '#FFD700',
    'SFVec3d':     '#FFD700', 'MFVec3d':     '#FFD700',
    'SFVec4d':     '#FFD700', 'MFVec4d':     '#FFD700',
    'SFColor':     '#FF8C00', 'MFColor':     '#FF8C00',
    'SFColorRGBA': '#FF8C00', 'MFColorRGBA': '#FF8C00',
    'SFRotation':  '#9B59B6', 'MFRotation':  '#9B59B6',
    'SFString':    '#FF69B4', 'MFString':    '#FF69B4',
    'SFMatrix3f':  '#E74C3C', 'MFMatrix3f':  '#E74C3C',
    'SFMatrix4f':  '#E74C3C', 'MFMatrix4f':  '#E74C3C',
    'SFMatrix3d':  '#E74C3C', 'MFMatrix3d':  '#E74C3C',
    'SFMatrix4d':  '#E74C3C', 'MFMatrix4d':  '#E74C3C',
    'SFImage':     '#8B6914', 'MFImage':     '#8B6914',
}

class RKXGraphicsSocket(QGraphicsItem):
    def __init__(self, parent=None, isOutput=False, field_type='', field_name=''):
        super().__init__(parent)

        self.isOutput   = isOutput
        self.field_type = field_type
        self.socket     = None  # set by RKXSocket after creation
        
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
        type_color = _TYPE_COLORS.get(field_type)
        if type_color:
            self._color_background = QColor(type_color)
        elif self.isOutput:
            self._color_background = self._und_green
        else:
            self._color_background = self._und_orange
        self._color_outline    = self._und_black
        
        self._pen   = QPen(self._color_outline)
        self._brush = QBrush(self._color_background)
        self._pen.setWidthF(self.outline_width)
        self.setZValue(1)  # render above splines (edges are at Z=-1)

        # Field name label positioned inside the node
        self._label = QGraphicsSimpleTextItem(field_name, self)
        lbl_font = QFont('Arial')
        lbl_font.setPixelSize(9)
        lbl_font.setBold(True)
        self._label.setFont(lbl_font)
        self._label.setBrush(QBrush(QColor('#FFFFFF')))
        lbl_w = self._label.boundingRect().width()
        if isOutput:
            self._label.setPos(-self.radius - lbl_w - 4, -7)  # left of dot, inside node
        else:
            self._label.setPos(self.radius + 4, -7)            # right of dot, inside node

        
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

