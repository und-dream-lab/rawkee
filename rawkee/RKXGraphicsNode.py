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
 

class RKXGraphicsNode(QGraphicsItem):
    def __init__(self, eNode, parent=None):
        super().__init__(parent)
        
        self.eNode = eNode
        self.content = self.eNode.content
        
        self._und_green         = QColor("#FF009A44")
        self._und_green_trans   = QColor("#55009A44")
        self._und_green_ptrans  = QColor("#CC009A44")
        self._und_orange        = QColor("#FFFF671F")
        self._und_orange_trans  = QColor("#55FF671F")
        self._und_orange_ptrans = QColor("#CCFF671F")
        self._und_pink          = QColor("#FFF5B6CD")
        self._und_pink_trans    = QColor("#55F5B6CD")
        self._und_pink_ptrans   = QColor("#CCF5B6CD")
        self._title_color       = Qt.white
        self._title_font        = QFont(['Century Gothic', 'Arial', 'Helvetica', 'sans-serif'])
        self._title_font.setPixelSize(11)
        self._title_font.setWeight(QFont.Weight.Bold)
        
        self.width  = 220
        self.height = 280
        
        self.title_height = 24.0
        self._padding = 2.0
        
        self.edge_size = 10.0
        
        self._pen_basic    = QPen(self._und_green_ptrans)
        self._pen_default  = QPen(QColor("#FF000000"))
        self._pen_unselect = QPen(self._und_pink_trans)
        self._pen_selected = QPen(self._und_green)
        
        self._pen_default.setWidth(2)
        self._pen_basic.setWidth(2)
        self._pen_unselect.setWidth(2)
        self._pen_selected.setWidth(2)
        
        self._brush_title        = QBrush(QColor("#77313131"))
        self._brush_background   = QBrush(QColor("#FF212121"))
        self._brush_indicatorBk  = QBrush(QColor(Qt.black))
        self._brush_notIndicated = QBrush(self._und_pink_trans)
        self._brush_indicated    = QBrush(self._und_pink_ptrans)

        # Init Title
        self.initTitle()
        self.title = self.eNode.title
        
        # Init Sockets
        self.initSockets()
        
        # Init Content
        self.initContent()
        
        self.initUI()
        
    def boundingRect(self):
        # Return the bounding rectangle of your item
        return QRectF(
            0, 
            0,
            self.width,
            self.height
            ).normalized()
        
    def initUI(self):
        self.setFlag(RKXGraphicsNode.ItemIsSelectable)
        self.setFlag(RKXGraphicsNode.ItemIsMovable)


    @property
    def title(self): return self._title
    @title.setter
    def title(self, value):
        self._title = value
        nodeDEFChop = self._title[:28]
        self.title_item.setPlainText(nodeDEFChop)
        
    
        
    def initTitle(self):
        self.headerItem = QGraphicsTextItem(self)
        self.headerItem.setDefaultTextColor(self._und_orange)
        self.headerItem.setFont(self._title_font)
        self.headerItem.setPos(self._padding, self._padding)
        self.headerItem.setPlainText("DEF:")
        
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setDefaultTextColor(self._title_color)
        self.title_item.setFont(self._title_font)
        self.title_item.setPos(self._padding + 27, self._padding)

    def initContent(self):
        self.grContent = QGraphicsProxyWidget(self)
        self.content.setGeometry(self.edge_size, self.title_height + self.edge_size, 
                                 self.width - (2 * self.edge_size), self.height - (2 * self.edge_size) - self.title_height)
        self.grContent.setWidget(self.content)
        
    def initSockets(self):
        pass

    def paint(self, painter, option, widget):

        #title
        path_title = QPainterPath()
        path_title.setFillRule(Qt.WindingFill)
        path_title.addRoundedRect(0, 0, self.width, self.title_height, self.edge_size, self.edge_size)
        path_title.addRect(                          0, self.title_height - self.edge_size, self.edge_size, self.edge_size)
        path_title.addRect(self.width - self.edge_size, self.title_height - self.edge_size, self.edge_size, self.edge_size)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(path_title.simplified())
        
        #content
        path_content = QPainterPath()
        path_content.setFillRule(Qt.WindingFill)
        path_content.addRoundedRect(0, self.title_height, self.width, self.height - self.title_height, self.edge_size, self.edge_size)
        path_content.addRect(                          0, self.title_height, self.edge_size, self.edge_size)
        path_content.addRect(self.width - self.edge_size, self.title_height, self.edge_size, self.edge_size)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_content.simplified())
        
        #outline
        path_outline = QPainterPath()
        path_outline.addRoundedRect(0, 0, self.width, self.height, self.edge_size, self.edge_size)
        
        #painter.setPen(self._pen_basic)
        painter.setPen(self._pen_basic if not self.isSelected() else self._pen_selected)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path_outline.simplified())
        
        #selected light indicator outline
        path_indicator = QPainterPath()
        path_indicator.addRoundedRect(self.width-60, -3, 40, 6, 3, 3)
        painter.setPen(self._pen_default)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path_indicator.simplified())
        
        path_indicator_light = QPainterPath()
        path_indicator_light.setFillRule(Qt.WindingFill)
        path_indicator_light.addRoundedRect(self.width-60, -3, 40, 6, 3, 3)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_indicatorBk)
        painter.drawPath(path_indicator_light.simplified())
        
        painter.setBrush(self._brush_notIndicated if not self.isSelected() else self._brush_indicated )
        painter.drawPath(path_indicator_light.simplified())
        