try:
    #Qt5
    from PySide2.QtGui     import *
    from PySide2.QtWidgets import *

    from PySide2.QtCore    import *

except:
    #Qt6
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
        return super().mousePressEvent(event)
        
    def leftMouseButtonRelease(self, event):
        return super().mouseReleaseEvent(event)
        
    def rightMouseButtonPress(self, event):
        return super().mousePressEvent(event)
        
    def rightMouseButtonRelease(self, event):
        return super().mouseReleaseEvent(event)
    
    # Middle Mouse Button Event overrides that implement middle mouse button scene dragging.
    def middleMouseButtonPress(self, event):
        releaseEvent = QMouseEvent(QEvent.MouseButtonRelease, event.localPos(), event.screenPos(), Qt.LeftButton, Qt.NoButton, event.modifiers())
        super().mouseReleaseEvent(releaseEvent)
        self.setDragMode(RKGraphicsView.ScrollHandDrag)
        fakeEvent = QMouseEvent(event.type(), event.localPos(), event.screenPos(), Qt.LeftButton, event.buttons() | Qt.LeftButton, event.modifiers())
        super().mousePressEvent(fakeEvent)
        
    def middleMouseButtonRelease(self, event):
        fakeEvent = QMouseEvent(event.type(), event.localPos(), event.screenPos(), Qt.LeftButton, event.buttons() | Qt.LeftButton, event.modifiers())
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
