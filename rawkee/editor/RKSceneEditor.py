from PySide6           import QtCore
from PySide6           import QtWidgets
from PySide6.QtWebEngineWidgets import *
from PySide6           import QtGui
from PySide6.QtGui     import *
from PySide6.QtWidgets import *
from PySide6.QtWidgets import QGraphicsItem as rkgItem
from PySide6.QtCore    import *
from PySide6.QtWebEngineCore  import *

import json
import os
import sys
import time
import http.server
import threading


def apply_dark_palette(app):
    app.setStyle('Fusion')
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,               QColor(45,  45,  45))
    p.setColor(QPalette.ColorRole.WindowText,           QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Base,                 QColor(30,  30,  30))
    p.setColor(QPalette.ColorRole.AlternateBase,        QColor(45,  45,  45))
    p.setColor(QPalette.ColorRole.ToolTipBase,          QColor(30,  30,  30))
    p.setColor(QPalette.ColorRole.ToolTipText,          QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Text,                 QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Button,               QColor(55,  55,  55))
    p.setColor(QPalette.ColorRole.ButtonText,           QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.BrightText,           QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.Link,                 QColor(0,   154,  68))
    p.setColor(QPalette.ColorRole.Highlight,            QColor(0,   154,  68))
    p.setColor(QPalette.ColorRole.HighlightedText,      QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.PlaceholderText,      QColor(120, 120, 120))
    disabled = QPalette.ColorGroup.Disabled
    p.setColor(disabled, QPalette.ColorRole.WindowText, QColor(120, 120, 120))
    p.setColor(disabled, QPalette.ColorRole.Text,       QColor(120, 120, 120))
    p.setColor(disabled, QPalette.ColorRole.ButtonText, QColor(120, 120, 120))
    p.setColor(disabled, QPalette.ColorRole.Highlight,  QColor(60,  100,  60))
    app.setPalette(p)

from functools import partial

import rawkee.io.RKx3d as rkx
from rawkee.io.RKLoadSceneFromFile import RKLoadSceneFromFile
from rawkee.io.RKSceneTraversal import RKSceneTraversal
from rawkee.editor.RKAIAssistant import RKAIAssistantPanel

# Pure outputOnly/inputOnly event fields missing from FIELD_DECLARATIONS in RKx3d.py.
# Format: {NodeTypeName: [(field_name, field_type, access)]}  access = 'inputOnly'|'outputOnly'
_EXTRA_EVENT_FIELDS = {
    'TimeSensor': [
        ('cycleTime',        'SFTime',    'outputOnly'),
        ('elapsedTime',      'SFTime',    'outputOnly'),
        ('fraction_changed', 'SFFloat',   'outputOnly'),
        ('isActive',         'SFBool',    'outputOnly'),
        ('isPaused',         'SFBool',    'outputOnly'),
        ('time',             'SFTime',    'outputOnly'),
    ],
    'PositionInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFVec3f',    'outputOnly'),
    ],
    'PositionInterpolator2D': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFVec2f',    'outputOnly'),
    ],
    'OrientationInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFRotation', 'outputOnly'),
    ],
    'ColorInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFColor',    'outputOnly'),
    ],
    'ScalarInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFFloat',    'outputOnly'),
    ],
    'NormalInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'MFVec3f',    'outputOnly'),
    ],
    'CoordinateInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'MFVec3f',    'outputOnly'),
    ],
    'CoordinateInterpolator2D': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'MFVec2f',    'outputOnly'),
    ],
    'SquadOrientationInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFRotation', 'outputOnly'),
    ],
    'SplinePositionInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFVec3f',    'outputOnly'),
    ],
    'SplinePositionInterpolator2D': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFVec2f',    'outputOnly'),
    ],
    'SplineScalarInterpolator': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('value_changed', 'SFFloat',    'outputOnly'),
    ],
    'EaseInEaseOut': [
        ('set_fraction',  'SFFloat',    'inputOnly'),
        ('modifiedFraction_changed', 'SFFloat', 'outputOnly'),
    ],
    'TouchSensor': [
        ('hitNormal_changed',   'SFVec3f',  'outputOnly'),
        ('hitPoint_changed',    'SFVec3f',  'outputOnly'),
        ('hitTexCoord_changed', 'SFVec2f',  'outputOnly'),
        ('isActive',            'SFBool',   'outputOnly'),
        ('isOver',              'SFBool',   'outputOnly'),
        ('touchTime',           'SFTime',   'outputOnly'),
    ],
    'ProximitySensor': [
        ('centerOfRotation_changed', 'SFVec3f',    'outputOnly'),
        ('isActive',                 'SFBool',     'outputOnly'),
        ('orientation_changed',      'SFRotation', 'outputOnly'),
        ('position_changed',         'SFVec3f',    'outputOnly'),
        ('enterTime',                'SFTime',     'outputOnly'),
        ('exitTime',                 'SFTime',     'outputOnly'),
    ],
    'VisibilitySensor': [
        ('isActive',   'SFBool', 'outputOnly'),
        ('enterTime',  'SFTime', 'outputOnly'),
        ('exitTime',   'SFTime', 'outputOnly'),
    ],
    'PlaneSensor': [
        ('isActive',           'SFBool',   'outputOnly'),
        ('isOver',             'SFBool',   'outputOnly'),
        ('translation_changed','SFVec3f',  'outputOnly'),
        ('trackPoint_changed', 'SFVec3f',  'outputOnly'),
    ],
    'CylinderSensor': [
        ('isActive',           'SFBool',    'outputOnly'),
        ('isOver',             'SFBool',    'outputOnly'),
        ('rotation_changed',   'SFRotation','outputOnly'),
        ('trackPoint_changed', 'SFVec3f',   'outputOnly'),
    ],
    'SphereSensor': [
        ('isActive',           'SFBool',    'outputOnly'),
        ('isOver',             'SFBool',    'outputOnly'),
        ('rotation_changed',   'SFRotation','outputOnly'),
        ('trackPoint_changed', 'SFVec3f',   'outputOnly'),
    ],
    'KeySensor': [
        ('actionKeyPress',   'SFInt32', 'outputOnly'),
        ('actionKeyRelease', 'SFInt32', 'outputOnly'),
        ('altKey',           'SFBool',  'outputOnly'),
        ('controlKey',       'SFBool',  'outputOnly'),
        ('isActive',         'SFBool',  'outputOnly'),
        ('keyPress',         'SFString','outputOnly'),
        ('keyRelease',       'SFString','outputOnly'),
        ('shiftKey',         'SFBool',  'outputOnly'),
    ],
    'StringSensor': [
        ('enteredText',  'SFString', 'outputOnly'),
        ('finalText',    'SFString', 'outputOnly'),
        ('isActive',     'SFBool',   'outputOnly'),
    ],
    'BooleanFilter': [
        ('set_boolean',    'SFBool', 'inputOnly'),
        ('inputFalse',     'SFBool', 'outputOnly'),
        ('inputNegate',    'SFBool', 'outputOnly'),
        ('inputTrue',      'SFBool', 'outputOnly'),
    ],
    'BooleanToggle': [
        ('set_boolean', 'SFBool', 'inputOnly'),
    ],
    'BooleanTrigger': [
        ('set_triggerTime', 'SFTime', 'inputOnly'),
        ('triggerTrue',     'SFBool', 'outputOnly'),
    ],
    'IntegerTrigger': [
        ('set_boolean',       'SFBool',  'inputOnly'),
        ('triggerValue',      'SFInt32', 'outputOnly'),
    ],
    'TimeTrigger': [
        ('set_boolean',  'SFBool', 'inputOnly'),
        ('triggerTime',  'SFTime', 'outputOnly'),
    ],
}
from rawkee.editor.RKXScene   import RKXScene
from rawkee.editor.RKXNodes   import RKXNode
from rawkee.editor.RKXSocket  import RKXSocket
from rawkee.editor.RKGraphics import RKGraphicsView


###########################################################################
# Custom QTreeWidget that enables dragging X3D nodes into the node editor.
###########################################################################
class RKX3DTreeWidget(QTreeWidget):

    MIME_TYPE = "application/x-rawkee-x3d-node"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._node_registry  = {}  # str(id(node)) -> rkx node object
        self._reparent_src   = None
        self._reparent_hover = None
        self._reparent_cb    = None
        self._insert_key_cb  = None
        self._bind_key_cb    = None
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def set_reparent_callback(self, fn):
        self._reparent_cb = fn

    def set_bind_key_callback(self, fn):
        self._bind_key_cb = fn

    def set_insert_key_callback(self, fn):
        self._insert_key_cb = fn

    def registerNode(self, node):
        """Store node in registry and return its key string."""
        key = str(id(node))
        self._node_registry[key] = node
        return key

    def nodeForKey(self, key):
        return self._node_registry.get(key)

    def clearRegistry(self):
        self._node_registry.clear()

    def mimeData(self, items):
        mime = QMimeData()
        # Only drag items that carry a node key (ignore field-group items)
        for item in items:
            key = item.data(0, Qt.UserRole)
            if key:
                mime.setData(self.MIME_TYPE, key.encode('utf-8'))
                break
        return mime

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            return
        if event.button() == Qt.LeftButton and (event.modifiers() & Qt.ControlModifier):
            item = self.itemAt(event.pos())
            # Start reparent drag only when pressing on an already-selected item
            if item is not None and item.data(0, Qt.UserRole) and item in self.selectedItems():
                self._reparent_src = item
                self.setCursor(Qt.DragMoveCursor)
                return
        item = self.itemAt(event.pos())
        # Deselect only when clicking empty space, not when re-clicking a selected item
        self._deselect_on_release = (item is None)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._reparent_src is not None:
            target = self.itemAt(event.pos())
            if target is not self._reparent_hover:
                if self._reparent_hover is not None:
                    self._reparent_hover.setBackground(0, QBrush())
                self._reparent_hover = target
                selected_ids = {id(i) for i in self.selectedItems()}
                if (target is not None
                        and id(target) not in selected_ids
                        and target.data(0, Qt.UserRole)):
                    target.setBackground(0, QBrush(QColor(0, 200, 80, 70)))
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._reparent_src is not None:
            self.unsetCursor()
            if self._reparent_hover is not None:
                self._reparent_hover.setBackground(0, QBrush())
            target = self.itemAt(event.pos())
            selected_ids = {id(i) for i in self.selectedItems()}
            if (target is not None
                    and id(target) not in selected_ids
                    and target.data(0, Qt.UserRole)
                    and self._reparent_cb):
                tgt_node  = self.nodeForKey(target.data(0, Qt.UserRole))
                src_nodes = [self.nodeForKey(i.data(0, Qt.UserRole))
                             for i in self.selectedItems()
                             if i.data(0, Qt.UserRole)]
                src_nodes = [n for n in src_nodes if n is not None and n is not tgt_node]
                if src_nodes and tgt_node is not None:
                    self._reparent_cb(src_nodes, tgt_node)
            self._reparent_src   = None
            self._reparent_hover = None
            return
        super().mouseReleaseEvent(event)
        # Deselect after Qt has finished its own release-time selection logic
        if getattr(self, '_deselect_on_release', False):
            self.clearSelection()
        self._deselect_on_release = False

    def event(self, event):
        # Tab is consumed by Qt focus traversal before keyPressEvent; handle it here.
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key_Tab:
            if self._insert_key_cb is not None:
                self._insert_key_cb()
            return True
        return super().event(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_B:
            return  # suppress type-ahead so keyReleaseEvent can bind without changing selection
        if event.key() == Qt.Key_Insert:
            if self._insert_key_cb is not None:
                self._insert_key_cb()
            return
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected = self.selectedItems()
            if selected:
                key  = selected[0].data(0, Qt.UserRole)
                node = self.nodeForKey(key) if key else None
                if node is not None and not getattr(node, 'USE', '') and self._reparent_cb:
                    # _reparent_cb.__self__ is RKSceneEditor; reuse its _delete_node
                    scene_editor = getattr(self._reparent_cb, '__self__', None)
                    if scene_editor and hasattr(scene_editor, '_delete_node'):
                        scene_editor._delete_node(node)
                        return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_B and not event.isAutoRepeat():
            selected = self.selectedItems()
            if selected and self._bind_key_cb:
                key  = selected[0].data(0, Qt.UserRole)
                node = self.nodeForKey(key) if key else None
                if node is not None:
                    self._bind_key_cb(node)
                    return
        super().keyReleaseEvent(event)


###########################################################################
# RKGraphicsView subclass that accepts X3D node drops from the tree widget.
###########################################################################
class RKNodeEditorDropView(RKGraphicsView):

    def __init__(self, grScene, tree_widget, parent=None):
        super().__init__(grScene, parent)
        self._tree_widget = tree_widget
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(RKX3DTreeWidget.MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(RKX3DTreeWidget.MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(RKX3DTreeWidget.MIME_TYPE):
            key = bytes(event.mimeData().data(RKX3DTreeWidget.MIME_TYPE)).decode('utf-8')
            x3d_node = self._tree_widget.nodeForKey(key)
            if x3d_node is not None:
                scene_pos = self.mapToScene(event.pos())
                parent_editor = self.parent()
                if parent_editor and hasattr(parent_editor, 'addNodeFromX3D'):
                    parent_editor.addNodeFromX3D(x3d_node, scene_pos)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class _RKFieldLineEdit(QLineEdit):
    """QLineEdit that reverts to its pre-focus text on blur unless Enter was pressed."""
    committed = Signal(str)

    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self._snapshot = text

    def focusInEvent(self, event):
        self._snapshot = self.text()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.setText(self._snapshot)
        self.setStyleSheet('')
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._snapshot = self.text()   # freeze so FocusOut won't revert
            self.committed.emit(self.text())
        super().keyPressEvent(event)


class _JSEditorDialog(QDialog):
    """Floating Monaco ECMAScript editor for a Script node."""

    _HTML_PATH = os.path.join(os.path.dirname(__file__), 'monaco_editor.html')

    # X3D field type → TypeScript type for UDF IntelliSense declarations
    _X3D_TO_TS = {
        'SFBool':       'boolean',    'MFBool':       'MFBool',
        'SFInt32':      'number',     'MFInt32':      'MFInt32',
        'SFFloat':      'number',     'MFFloat':      'MFFloat',
        'SFDouble':     'number',     'MFDouble':     'MFDouble',
        'SFTime':       'number',     'MFTime':       'MFTime',
        'SFString':     'string',     'MFString':     'MFString',
        'SFVec2f':      'SFVec2f',    'MFVec2f':      'MFVec2f',
        'SFVec3f':      'SFVec3f',    'MFVec3f':      'MFVec3f',
        'SFVec4f':      'SFVec4f',    'MFVec4f':      'MFVec4f',
        'SFVec2d':      'SFVec2d',    'MFVec2d':      'MFVec2d',
        'SFVec3d':      'SFVec3d',    'MFVec3d':      'MFVec3d',
        'SFVec4d':      'SFVec4d',    'MFVec4d':      'MFVec4d',
        'SFColor':      'SFColor',    'MFColor':      'MFColor',
        'SFColorRGBA':  'SFColorRGBA','MFColorRGBA':  'MFColorRGBA',
        'SFRotation':   'SFRotation', 'MFRotation':   'MFRotation',
        'SFMatrix3f':   'SFMatrix3f', 'MFMatrix3f':   'MFMatrix3f',
        'SFMatrix4f':   'SFMatrix4f', 'MFMatrix4f':   'MFMatrix4f',
        'SFImage':      'SFImage',    'MFImage':      'Uint32Array',
        'SFNode':       'X3DNode',    'MFNode':       'MFNode',
    }

    def __init__(self, node, on_apply, parent=None):
        super().__init__(parent)
        def_name = getattr(node, 'DEF', '') or 'Script'
        self.setWindowTitle(f'Script Editor \u2014 {def_name}')
        self.resize(820, 580)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint
        )
        self._on_apply = on_apply
        self._node     = node

        self._view = QWebEngineView()
        # file:// pages can't load CDN scripts without this
        self._view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        self._view.load(QUrl.fromLocalFile(self._HTML_PATH))
        self._view.loadFinished.connect(self._on_load_finished)
        # Ctrl+S inside Monaco signals Apply via document.title
        self._view.titleChanged.connect(self._on_title_changed)

        apply_btn = QPushButton('Apply')
        close_btn = QPushButton('Close')
        apply_btn.setFixedWidth(80)
        close_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self._apply)
        close_btn.clicked.connect(self.close)

        btn_bar = QWidget()
        btn_lay = QHBoxLayout(btn_bar)
        btn_lay.setContentsMargins(4, 4, 4, 4)
        btn_lay.addStretch()
        btn_lay.addWidget(apply_btn)
        btn_lay.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._view)
        layout.addWidget(btn_bar)

    def _on_load_finished(self, ok):
        if ok:
            src = getattr(self._node, 'sourceCode', '') or ''
            self._view.page().runJavaScript(
                f'window.monacoSetValue({json.dumps(src)})'
            )
            udf_dts = self._build_udf_dts()
            if udf_dts:
                self._view.page().runJavaScript(
                    f'window.monacoAddNodeLib({json.dumps(udf_dts)})'
                )

    def _build_udf_dts(self):
        lines = []
        for fobj in getattr(self._node, 'field', []):
            name    = getattr(fobj, 'name', None)
            x3dtype = getattr(fobj, 'type', 'SFString')
            access  = getattr(fobj, 'accessType', 'inputOutput')
            if not name:
                continue
            ts_type = self._X3D_TO_TS.get(x3dtype, 'any')
            lines.append(f'/** {x3dtype}  {access} */\ndeclare let {name}: {ts_type};')
        return '\n'.join(lines)

    def _on_title_changed(self, title):
        if title.startswith('__APPLY__:'):
            self._apply()

    def _apply(self):
        self._view.page().runJavaScript(
            'window.monacoGetValue()',
            lambda v: self._on_apply(v or '')
        )


class RKMFFieldRow(QWidget):
    """One MF field row: read-only display of val[idx] + optional inline edit."""

    committed = Signal(str, object)   # (field_name, new_full_list)

    _MF_WIDTHS = {
        'MFVec2f':2,'MFVec2d':2,
        'MFVec3f':3,'MFVec3d':3,'MFColor':3,
        'MFVec4f':4,'MFVec4d':4,'MFColorRGBA':4,'MFRotation':4,
    }

    def __init__(self, fname, ftype, parent=None):
        super().__init__(parent)
        self.fname    = fname
        self.ftype    = ftype
        self._width   = self._MF_WIDTHS.get(ftype, 1)
        self._value   = []
        self._idx     = 0
        self._editing = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)

        self._display = QLineEdit()
        self._display.setReadOnly(True)
        self._display.setPlaceholderText('—')
        self._display.setStyleSheet('color:#aaa;')
        self._display.returnPressed.connect(self._commit)
        self._display.installEventFilter(self)

        self._edit_btn = QPushButton('\u270f')  # ✏ pencil
        self._edit_btn.setFixedSize(24, 24)
        self._edit_btn.setCheckable(True)
        self._edit_btn.setToolTip('Edit this value')
        self._edit_btn.setStyleSheet(
            'QPushButton{color:#4CAF50;font-size:13px;padding:0;'
            'border:1px solid #555;border-radius:3px;background:#333;}'
            'QPushButton:checked{background:#1a3a1a;border-color:#4CAF50;}'
            'QPushButton:hover{border-color:#81C784;}'
        )
        self._edit_btn.clicked.connect(self._toggle_edit)

        lay.addWidget(self._display, 1)
        lay.addWidget(self._edit_btn)

    def load(self, full_list, idx=0):
        self._value   = full_list
        self._idx     = idx
        self._editing = False
        self._edit_btn.setChecked(False)
        self._display.setReadOnly(True)
        self._display.setStyleSheet('color:#aaa;')
        self._refresh()

    def set_index(self, idx):
        if self._editing:
            self._cancel()
        self._idx = idx
        self._refresh()

    def _refresh(self):
        if not self._value or self._idx >= len(self._value):
            self._display.setText('')
            return
        elem = self._value[self._idx]
        if isinstance(elem, tuple):
            self._display.setText(' '.join(str(v) for v in elem))
        elif isinstance(elem, bool):
            self._display.setText('true' if elem else 'false')
        else:
            self._display.setText(str(elem))

    def _toggle_edit(self, checked):
        if checked:
            self._editing = True
            self._display.setReadOnly(False)
            self._display.setStyleSheet('')
            self._display.setFocus()
            self._display.selectAll()
        else:
            self._cancel()

    def _commit(self):
        if not self._editing or not self._value or self._idx >= len(self._value):
            return
        text = self._display.text().strip()
        try:
            if self.ftype == 'MFBool':
                elem = text.lower() in ('true', '1', 'yes')
            elif self.ftype == 'MFString':
                elem = text.strip('"\'')
            elif self.ftype == 'MFInt32':
                elem = int(float(text))
            elif self._width > 1:
                parts = [float(p) for p in text.split()]
                elem  = tuple(parts[:self._width])
            else:
                elem = float(text)
        except Exception:
            self._display.setStyleSheet('background:#5a1a1a;')
            return
        new_list = list(self._value)
        new_list[self._idx] = elem
        self._value = new_list
        self._editing = False
        self._edit_btn.setChecked(False)
        self._display.setReadOnly(True)
        self._display.setStyleSheet('color:#aaa;')
        self._display.setStyleSheet('')
        self.committed.emit(self.fname, list(self._value))

    def _cancel(self):
        self._editing = False
        self._edit_btn.setChecked(False)
        self._display.setReadOnly(True)
        self._display.setStyleSheet('color:#aaa;')
        self._refresh()

    def eventFilter(self, obj, event):
        if obj is self._display and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self._cancel()
                return True
        if obj is self._display and event.type() == QEvent.Type.FocusOut:
            if self._editing:
                self._cancel()
        return super().eventFilter(obj, event)


class RKNodeFieldEditor(QWidget):
    """Attribute-editor panel for scalar/vector fields of a selected X3D node.

    MF fields display one element at a time via a shared or per-field index spinbox.
    Parallel MF arrays (same length) share a single index control at the top.
    """

    _SF_WIDTHS = {
        'SFVec2f':2,'SFVec2d':2,
        'SFVec3f':3,'SFVec3d':3,'SFColor':3,
        'SFVec4f':4,'SFVec4d':4,'SFColorRGBA':4,'SFRotation':4,
        'SFMatrix3f':9,'SFMatrix3d':9,
        'SFMatrix4f':16,'SFMatrix4d':16,
    }
    _MF_WIDTHS = {
        'MFVec2f':2,'MFVec2d':2,
        'MFVec3f':3,'MFVec3d':3,'MFColor':3,
        'MFVec4f':4,'MFVec4d':4,'MFColorRGBA':4,'MFRotation':4,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._node          = None
        self._sai_runner    = None
        self._node_def_map  = {}
        self._undo_push_fn  = None
        self._field_undo_fn = None
        self._widgets         = {}    # fname -> (widget, ftype)  — SF fields only
        self._mf_rows         = {}    # fname -> RKMFFieldRow
        self._per_field_spins = []    # explicit Python refs so GC can't sever signal
        self._graph_refresh_fn = None
        self._udf_widgets = {}  # id(fobj) → (widget, ftype) for editable non-node UDFs
        self._js_editor_ref  = None   # open _JSEditorDialog instance

        self._header = QLabel('No selection')
        self._header.setContentsMargins(4, 3, 4, 3)
        f = self._header.font(); f.setBold(True); self._header.setFont(f)

        # Shared MF index bar — visible when ≥2 MF fields share the same length
        self._idx_bar  = QWidget()
        _ilay          = QHBoxLayout(self._idx_bar)
        _ilay.setContentsMargins(4, 2, 4, 2)
        _ilay.setSpacing(4)
        self._idx_spin = QSpinBox()
        self._idx_spin.setMinimum(0)
        self._idx_spin.setMaximum(0)
        self._idx_of   = QLabel('of 0')
        _ilay.addWidget(self._idx_spin)
        _ilay.addWidget(self._idx_of)
        _ilay.addStretch()
        self._idx_bar.setVisible(False)
        self._idx_spin.valueChanged.connect(self._on_shared_idx)

        self._scroll    = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._container = QWidget()
        self._form      = QFormLayout(self._container)
        self._form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._form.setSpacing(3)
        self._form.setContentsMargins(4, 4, 4, 4)
        self._scroll.setWidget(self._container)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._header)
        lay.addWidget(self._idx_bar)
        lay.addWidget(self._scroll)

    # ── public interface ──────────────────────────────────────────────────────

    def set_sai_runner(self, fn):      self._sai_runner      = fn
    def set_node_def_map(self, m):     self._node_def_map    = m
    def set_undo_push_fn(self, fn):    self._undo_push_fn    = fn
    def set_field_undo_fn(self, fn):   self._field_undo_fn   = fn
    def set_graph_refresh_fn(self, fn): self._graph_refresh_fn = fn

    def set_node(self, node):
        self._node = node
        self._widgets.clear()
        self._mf_rows.clear()
        self._per_field_spins.clear()
        self._udf_widgets.clear()
        self._js_editor_ref = None
        while self._form.rowCount():
            self._form.removeRow(0)
        self._idx_bar.setVisible(False)
        self._idx_spin.blockSignals(True)
        self._idx_spin.setValue(0)
        self._idx_spin.blockSignals(False)

        if node is None:
            self._header.setText('No selection')
            return

        try:
            ntype = type(node).NAME() if hasattr(type(node), 'NAME') else type(node).__name__
            def_  = getattr(node, 'DEF', '')
            self._header.setText(ntype + (f'  [{def_}]' if def_ else ''))
        except Exception:
            self._header.setText(type(node).__name__)

        if not hasattr(type(node), 'FIELD_DECLARATIONS'):
            return

        _is_script = (type(node).NAME() if hasattr(type(node), 'NAME') else '') == 'Script'
        # sourceCode shown in the dedicated JS editor below, not as a text line
        _SKIP = frozenset({'DEF','USE','IS','class_','id_','style_','metadata'}
                          | ({'sourceCode'} if _is_script else set()))
        sf_rows, mf_rows = [], []

        for decl in type(node).FIELD_DECLARATIONS():
            fname = decl[0]
            if fname in _SKIP:
                continue
            try:    ftype  = decl[2]()
            except: ftype  = ''
            try:    access = decl[3]()
            except: access = ''
            if ftype in ('SFNode', 'MFNode'):
                continue
            try:    val = getattr(node, fname)
            except: continue
            ro = (access == 'outputOnly')
            if ftype.startswith('MF'):
                mf_rows.append((fname, ftype, val, ro))
            else:
                sf_rows.append((fname, ftype, val, ro))

        # SF fields
        for fname, ftype, val, ro in sf_rows:
            w = self._make_sf_widget(fname, ftype, val, ro)
            if w is None:
                continue
            self._widgets[fname] = (w, ftype)
            lbl = QLabel(fname)
            if ro:
                lbl.setStyleSheet('color:#888;')
            self._form.addRow(lbl, w)

        # MF fields
        if mf_rows:
            lengths     = [len(v) for _, _, v, _ in mf_rows if isinstance(v, list) and v]
            use_shared  = len(lengths) >= 2 and len(set(lengths)) == 1
            shared_len  = lengths[0] if use_shared else 0

            if use_shared:
                self._idx_spin.blockSignals(True)
                self._idx_spin.setMaximum(max(0, shared_len - 1))
                self._idx_spin.setValue(0)
                self._idx_spin.blockSignals(False)
                self._idx_of.setText(f'of {shared_len}')
                self._idx_bar.setVisible(True)

            for fname, ftype, val, ro in mf_rows:
                row = RKMFFieldRow(fname, ftype)
                row.load(val if isinstance(val, list) else [], 0)
                row.committed.connect(self._mf_committed)
                self._mf_rows[fname] = row
                lbl = QLabel(fname)
                if ro:
                    lbl.setStyleSheet('color:#888;')
                    row.setEnabled(False)

                if use_shared:
                    self._form.addRow(lbl, row)
                else:
                    # Per-field index spinbox
                    length  = len(val) if isinstance(val, list) else 0
                    wrapper = QWidget()
                    wlay    = QHBoxLayout(wrapper)
                    wlay.setContentsMargins(0, 0, 0, 0)
                    wlay.setSpacing(3)
                    spin    = QSpinBox()
                    spin.setMinimum(0)
                    spin.setMaximum(max(0, length - 1))
                    spin.setFixedWidth(60)
                    spin.valueChanged.connect(lambda v, r=row: r.set_index(v))
                    self._per_field_spins.append(spin)  # prevent GC
                    wlay.addWidget(spin)
                    wlay.addWidget(row, 1)
                    wlay.addWidget(QLabel(f'/{length}'))
                    self._form.addRow(lbl, wrapper)

        # User-defined fields section (Script nodes only)
        ntype = type(node).NAME() if hasattr(type(node), 'NAME') else ''
        if ntype == 'Script':
            self._build_script_source_editor(node)
            self._build_script_user_fields(node)

    # ── source-code editor (Script only) ──────────────────────────────────

    def _build_script_source_editor(self, node):
        sep = QLabel('\u2500\u2500 Source Code \u2500\u2500')
        sep.setAlignment(Qt.AlignCenter)
        sep.setStyleSheet('color:#666; font-size:9px; padding:2px 0;')
        self._form.addRow(sep)
        btn = QPushButton('Edit Source Code\u2026')
        btn.clicked.connect(lambda: self._open_js_editor(node))
        self._form.addRow(btn)

    def _open_js_editor(self, node):
        if self._js_editor_ref is not None and not self._js_editor_ref.isHidden():
            self._js_editor_ref.raise_()
            self._js_editor_ref.activateWindow()
            return
        dlg = _JSEditorDialog(
            node,
            on_apply=lambda text: self._commit_source_code(text, node),
        )
        dlg.setModal(False)
        dlg.show()
        self._js_editor_ref = dlg

    def _commit_source_code(self, text, node):
        if getattr(node, 'sourceCode', '') == text:
            return
        if self._undo_push_fn:
            self._undo_push_fn()
        try:
            node.sourceCode = text
        except Exception:
            return
        self._push_sai('sourceCode', text, 'SFString')

    # ── user-defined fields (Script only) ──────────────────────────────────

    # SFNode/MFNode excluded here; managed via tree right-click menu
    _UDF_FIELD_TYPES = [
        'SFBool','MFBool','SFColor','MFColor','SFColorRGBA','MFColorRGBA',
        'SFDouble','MFDouble','SFFloat','MFFloat','SFImage','MFImage',
        'SFInt32','MFInt32','SFRotation','MFRotation',
        'SFString','MFString','SFTime','MFTime',
        'SFVec2d','MFVec2d','SFVec2f','MFVec2f',
        'SFVec3d','MFVec3d','SFVec3f','MFVec3f',
        'SFVec4d','MFVec4d','SFVec4f','MFVec4f',
    ]
    _UDF_ACCESS_TYPES = ['inputOnly', 'outputOnly', 'inputOutput', 'initializeOnly']

    def _build_script_user_fields(self, node):
        sep = QLabel('\u2500\u2500 User-Defined Fields \u2500\u2500')
        sep.setAlignment(Qt.AlignCenter)
        sep.setStyleSheet('color:#666; font-size:9px; padding:2px 0;')
        self._form.addRow(sep)

        for fobj in list(getattr(node, 'field', None) or []):
            fname   = getattr(fobj, 'name',       '') or ''
            ftype   = getattr(fobj, 'type',       '') or ''
            faccess = getattr(fobj, 'accessType', '') or ''

            if ftype in ('SFNode', 'MFNode'):
                # Node-type UDFs: read-only label; managed via tree context menu
                info = QLabel(f'{fname}  [{ftype}  {faccess}]')
                info.setStyleSheet('color:#666; font-size:9px; font-style:italic;')
                self._form.addRow(info)
                continue

            # Non-node UDF: editable value widget + remove button
            ro = faccess in ('outputOnly', 'inputOnly')
            fval = getattr(fobj, 'value', None)

            if ftype.startswith('MF') and ftype != 'MFString':
                row = RKMFFieldRow(fname, ftype)
                val_list = fval if isinstance(fval, list) else []
                row.load(val_list, 0)
                row.committed.connect(
                    lambda _fn, new_list, fo=fobj: self._udf_mf_committed(fo, new_list)
                )
                if ro:
                    row.setEnabled(False)
                self._udf_widgets[id(fobj)] = (row, ftype)
                w_or_row = row
            else:
                w_or_row = self._make_udf_sf_widget(fobj, fval, ro)
                self._udf_widgets[id(fobj)] = (w_or_row, ftype)

            lbl = QLabel(fname)
            if ro:
                lbl.setStyleSheet('color:#888;')

            rm_btn = QPushButton('\u2715')
            rm_btn.setFixedSize(20, 18)
            rm_btn.setStyleSheet('font-size:9px; padding:0;')
            rm_btn.clicked.connect(lambda _c, fo=fobj: self._remove_user_field(fo))

            cell = QWidget()
            lay  = QHBoxLayout(cell)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(2)
            lay.addWidget(w_or_row, 1)
            lay.addWidget(rm_btn)
            self._form.addRow(lbl, cell)

        # "Add" row (SFNode/MFNode excluded from combo)
        name_e = QLineEdit()
        name_e.setPlaceholderText('name')
        name_e.setMinimumWidth(55)

        type_cb = QComboBox()
        type_cb.addItems(self._UDF_FIELD_TYPES)
        type_cb.setMinimumWidth(80)

        access_cb = QComboBox()
        access_cb.addItems(self._UDF_ACCESS_TYPES)
        access_cb.setMinimumWidth(90)

        add_btn = QPushButton('+')
        add_btn.setFixedSize(20, 18)
        add_btn.setStyleSheet('font-size:11px; font-weight:bold; padding:0;')
        add_btn.clicked.connect(
            lambda: self._add_user_field_clicked(name_e, type_cb, access_cb)
        )

        add_row = QWidget()
        add_lay = QHBoxLayout(add_row)
        add_lay.setContentsMargins(0, 0, 0, 0)
        add_lay.setSpacing(2)
        add_lay.addWidget(name_e, 1)
        add_lay.addWidget(type_cb)
        add_lay.addWidget(access_cb)
        add_lay.addWidget(add_btn)
        add_lbl = QLabel('Add:')
        add_lbl.setStyleSheet('color:#888; font-size:9px;')
        self._form.addRow(add_lbl, add_row)

    def _make_udf_sf_widget(self, fobj, fval, ro):
        """Create an SF (or MFString) widget for a non-node UDF field."""
        ftype = getattr(fobj, 'type', '') or ''
        fname = getattr(fobj, 'name', '') or ''
        if ftype == 'SFBool':
            w = QCheckBox()
            w.setChecked(bool(fval))
            w.setEnabled(not ro)
            if not ro:
                w.toggled.connect(lambda _v, fo=fobj: self._udf_changed(fo))
            return w
        if ftype == 'MFString':
            text = ', '.join(f'"{v}"' for v in (fval or []))
        else:
            text = self._val_to_str(fval)
        if ro:
            w = QLineEdit(text)
            w.setReadOnly(True)
            w.setStyleSheet('color:#888;')
        else:
            w = _RKFieldLineEdit(text)
            w.committed.connect(lambda _t, fo=fobj: self._udf_changed(fo))
        return w

    def _udf_changed(self, fobj):
        """Commit a value change for an editable non-node UDF field."""
        if self._node is None:
            return
        fname = getattr(fobj, 'name', '') or ''
        ftype = getattr(fobj, 'type', '') or ''
        entry = self._udf_widgets.get(id(fobj))
        if not entry:
            return
        w, _ = entry
        try:
            parsed = self._parse(w, ftype)
        except Exception:
            if isinstance(w, QLineEdit):
                w.setStyleSheet('background:#5a1a1a;')
            return
        if isinstance(w, QLineEdit):
            w.setStyleSheet('')
        if self._undo_push_fn:
            self._undo_push_fn()
        try:
            fobj.value = parsed
        except Exception:
            if isinstance(w, QLineEdit):
                w.setStyleSheet('background:#5a1a1a;')
            return
        self._push_sai(fname, parsed, ftype)

    def _udf_mf_committed(self, fobj, new_list):
        """Commit an MF value change for a non-node UDF field."""
        if self._node is None:
            return
        fname = getattr(fobj, 'name', '') or ''
        ftype = getattr(fobj, 'type', '') or ''
        if self._undo_push_fn:
            self._undo_push_fn()
        try:
            fobj.value = new_list
        except Exception:
            return
        self._push_sai(fname, new_list, ftype)

    @staticmethod
    def _script_field_names(node):
        """All field names already taken on a Script node (declared + user-defined)."""
        names = set()
        if hasattr(type(node), 'FIELD_DECLARATIONS'):
            for decl in type(node).FIELD_DECLARATIONS():
                names.add(decl[0])
        for fobj in list(getattr(node, 'field', None) or []):
            fn = getattr(fobj, 'name', '') or ''
            if fn:
                names.add(fn)
        return names

    def _add_user_field_clicked(self, name_edit, type_combo, access_combo):
        if self._node is None:
            return
        fname   = name_edit.text().strip()
        ftype   = type_combo.currentText()
        faccess = access_combo.currentText()
        if not fname:
            name_edit.setStyleSheet('background:#5a1a1a;')
            name_edit.setToolTip('Field name is required')
            return
        if fname in self._script_field_names(self._node):
            name_edit.setStyleSheet('background:#5a1a1a;')
            name_edit.setToolTip(f'"{fname}" is already defined on this Script node')
            return
        name_edit.setStyleSheet('')
        name_edit.setToolTip('')
        import rawkee.io.RKx3d as _rkx
        try:
            f = _rkx.field()
            f.name       = fname
            f.type       = ftype
            f.accessType = faccess
        except Exception as e:
            print(f'Error creating user-defined field: {e}', flush=True)
            return
        if self._undo_push_fn:
            self._undo_push_fn()
        if not isinstance(getattr(self._node, 'field', None), list):
            self._node.field = []
        self._node.field.append(f)
        if self._graph_refresh_fn:
            self._graph_refresh_fn(self._node)
        self.set_node(self._node)

    def _remove_user_field(self, field_obj):
        if self._node is None:
            return
        existing = list(getattr(self._node, 'field', None) or [])
        if field_obj not in existing:
            return
        if self._undo_push_fn:
            self._undo_push_fn()
        existing.remove(field_obj)
        self._node.field = existing
        if self._graph_refresh_fn:
            self._graph_refresh_fn(self._node)
        self.set_node(self._node)

    # ── shared index ──────────────────────────────────────────────────────────

    def _on_shared_idx(self, idx):
        for row in self._mf_rows.values():
            row.set_index(idx)

    # ── MF commit ─────────────────────────────────────────────────────────────

    def _mf_committed(self, fname, new_list):
        if self._node is None:
            return
        if self._field_undo_fn:
            try:    old = getattr(self._node, fname)
            except: old = None
            self._field_undo_fn(self._node, fname, old)
        elif self._undo_push_fn:
            self._undo_push_fn()
        try:
            setattr(self._node, fname, new_list)
        except Exception:
            return
        ftype = ''
        try:
            for decl in type(self._node).FIELD_DECLARATIONS():
                if decl[0] == fname:
                    ftype = decl[2]()
                    break
        except Exception:
            pass
        self._push_sai(fname, new_list, ftype)

    # ── SF widget factory ─────────────────────────────────────────────────────

    def _make_sf_widget(self, fname, ftype, val, ro):
        if ftype == 'SFBool':
            w = QCheckBox()
            w.setChecked(bool(val))
            w.setEnabled(not ro)
            if not ro:
                w.toggled.connect(lambda _v, fn=fname: self._changed(fn))
            return w
        if ftype == 'MFString':
            text = ', '.join(f'"{v}"' for v in (val or []))
        else:
            text = self._val_to_str(val)
        if ro:
            w = QLineEdit(text)
            w.setReadOnly(True)
            w.setStyleSheet('color:#888;')
        else:
            w = _RKFieldLineEdit(text)
            w.committed.connect(lambda _t, fn=fname: self._changed(fn))
        return w

    # kept for SAI / undo helpers that call _val_to_str
    def _val_to_str(self, val):
        if isinstance(val, bool):   return 'true' if val else 'false'
        if isinstance(val, tuple):  return ' '.join(str(v) for v in val)
        if isinstance(val, list):
            if not val: return ''
            if isinstance(val[0], tuple):
                return '  '.join(' '.join(str(x) for x in t) for t in val)
            return ' '.join(str(v) for v in val)
        return str(val) if val is not None else ''

    # ── SF field change ───────────────────────────────────────────────────────

    def _changed(self, fname):
        if self._node is None:
            return
        entry = self._widgets.get(fname)
        if not entry:
            return
        w, ftype = entry
        try:
            parsed = self._parse(w, ftype)
        except Exception:
            if isinstance(w, QLineEdit): w.setStyleSheet('background:#5a1a1a;')
            return
        if isinstance(w, QLineEdit): w.setStyleSheet('')
        if self._field_undo_fn:
            try:    old_val = getattr(self._node, fname)
            except: old_val = None
            self._field_undo_fn(self._node, fname, old_val)
        elif self._undo_push_fn:
            self._undo_push_fn()
        try:
            setattr(self._node, fname, parsed)
        except Exception:
            if isinstance(w, QLineEdit): w.setStyleSheet('background:#5a1a1a;')
            return
        self._push_sai(fname, parsed, ftype)

    def _parse(self, w, ftype):
        if isinstance(w, QCheckBox):
            return w.isChecked()
        text = w.text().strip()
        if ftype == 'SFBool':   return text.lower() in ('true','1','yes')
        if ftype == 'SFString': return text
        if ftype == 'SFInt32':  return int(float(text))
        if ftype in ('SFFloat','SFDouble','SFTime'): return float(text)
        if ftype in self._SF_WIDTHS:
            return tuple(float(p) for p in text.split())
        if ftype == 'MFInt32':  return [int(float(p)) for p in text.split()] if text else []
        if ftype in ('MFFloat','MFDouble','MFTime'):
            return [float(p) for p in text.split()] if text else []
        if ftype == 'MFString':
            import re
            return re.findall(r'"([^"]*)"', text) if text else []
        if ftype == 'MFBool':
            return [p.lower() in ('true','1') for p in text.split()] if text else []
        if ftype in self._MF_WIDTHS:
            wid   = self._MF_WIDTHS[ftype]
            parts = [float(p) for p in text.split()]
            return [tuple(parts[i:i+wid]) for i in range(0, len(parts), wid)]
        return text

    # ── SAI push ──────────────────────────────────────────────────────────────

    def _push_sai(self, fname, value, ftype):
        if self._sai_runner is None:
            return
        def_ = getattr(self._node, 'DEF', '') or ''
        if not def_:
            def_ = self._node_def_map.get(id(self._node), '')
        if not def_:
            return
        js_val = self._to_js(value, ftype, fname)
        self._sai_runner(f'RK.setField({json.dumps(def_)},{json.dumps(fname)},{js_val})')

    def _to_js(self, value, ftype, fname):
        if ftype == 'SFBool':   return 'true' if value else 'false'
        if ftype == 'SFString': return json.dumps(value)
        if ftype == 'SFInt32':  return str(int(value) if value is not None else 0)
        if ftype in ('SFFloat','SFDouble','SFTime'):
            return str(float(value) if value is not None else 0.0)
        if isinstance(value, tuple):
            return '[' + ','.join(str(v) for v in value) + ']'
        if isinstance(value, list):
            if not value: return '[]'
            if isinstance(value[0], tuple):
                inner = ','.join('['+','.join(str(x) for x in t)+']' for t in value)
                return f'[{inner}]'
            return '[' + ','.join(str(v) for v in value) + ']'
        return json.dumps(str(value) if value is not None else '')


class _TabCompleteEdit(QLineEdit):
    """QLineEdit that completes on Tab instead of changing focus."""
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            c = self.completer()
            if c and c.completionCount() > 0:
                self.setText(c.currentCompletion())
            return
        super().keyPressEvent(event)


class _RKNodePickerDialog(QDialog):
    def __init__(self, node_names, field_resolver, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add Node')
        self.setMinimumWidth(340)
        layout = QVBoxLayout(self)

        self._field_resolver = field_resolver

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self._edit = _TabCompleteEdit()
        self._edit.setPlaceholderText('Type to search\u2026')
        completer = QCompleter(sorted(node_names, key=str.casefold), self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchStartsWith)
        self._edit.setCompleter(completer)
        form.addRow('X3D Node Type', self._edit)

        self._edit2 = _TabCompleteEdit()
        self._edit2.setPlaceholderText('Select parent node first\u2026')
        self._edit2.setEnabled(False)
        form.addRow('Container Field', self._edit2)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        # Prevent Ok button from swallowing Enter key globally
        btns.button(QDialogButtonBox.Ok).setDefault(False)
        btns.button(QDialogButtonBox.Ok).setAutoDefault(False)
        layout.addWidget(btns)
        # Enter/Tab handled entirely in eventFilter — no returnPressed connections
        QApplication.instance().installEventFilter(self)

    def _on_node_type_entered(self):
        node_name = self._edit.text().strip()
        fields = self._field_resolver(node_name) if self._field_resolver else []
        self._edit2.setEnabled(True)
        self._edit2.clear()
        self._edit2.setPlaceholderText('Type to search\u2026' if fields else 'No fields available')
        c2 = QCompleter(sorted(fields, key=str.casefold), self)
        c2.setCaseSensitivity(Qt.CaseInsensitive)
        c2.setFilterMode(Qt.MatchStartsWith)
        self._edit2.setCompleter(c2)
        self._edit2.setFocus()
        if fields:
            c2.setCompletionPrefix('')
            c2.complete()

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.KeyPress
                and event.key() in (Qt.Key_Tab, Qt.Key_Return, Qt.Key_Enter)
                and self.isActiveWindow()):
            focused = QApplication.focusWidget()
            for edit, on_confirm in ((self._edit, self._on_node_type_entered),
                                     (self._edit2, self.accept)):
                if focused is not edit:
                    continue
                c = edit.completer()
                top = c.currentCompletion() if (c and c.completionCount() > 0) else ''
                if top and edit.text().strip().casefold() != top.casefold():
                    edit.setText(top)
                    if c.popup() and c.popup().isVisible():
                        c.popup().hide()
                else:
                    if c and c.popup() and c.popup().isVisible():
                        c.popup().hide()
                    on_confirm()
                return True
        return super().eventFilter(obj, event)

    def done(self, result):
        QApplication.instance().removeEventFilter(self)
        super().done(result)

    def chosen_name(self):
        return self._edit.text().strip()

    def chosen_name2(self):
        return self._edit2.text().strip()


class RKSceneEditor(QMainWindow):
    
    OBJECT_NAME = "RKSceneEditor"
    
    @classmethod
    def scene_editor_control_name(cls):
        return "{0}WorkspaceControl".format(cls.OBJECT_NAME)
        
    @classmethod
    def workspace_ui_script(cls):
        return "from rawkee.editor.RKSceneEditor import RKSceneEditor\nrkSEWidget = RKSceneEditor()"
        
    @classmethod
    def workplace_close_command(cls):
        return "self.cleanUpOnEditorClose()"

    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("RawKee PE - X3D Interaction Editor")
        self.setMinimumSize(900, 600)

        self.node_editor_name = ""

        self.bkHost    = None
        self.httpd    = None
        self._x3dObj  = None  # full rkx.X3D object kept in memory
        self._ai_batch    = False  # suppress per-node tree rebuild and X_ITE reload
        self._ai_new_defs: set = set()  # DEF names created in the current AI turn
        self._node_def_map: dict = {}   # id(pynode) -> registered DEF (real or synthetic)
        self._auto_def_counter: int = 0
        self._undo_stack: list = []
        self._redo_stack: list = []
        import threading as _threading
        self._undo_lock = _threading.Lock()

        self.setURLPaths()
        self.create_actions()
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    _MAX_UNDO = 50


    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------
    def _serialize_scene(self):
        if self._x3dObj is None:
            return None
        import io
        from rawkee.io.RKSceneTraversal import RKSceneTraversal
        buf = io.StringIO()
        trv = RKSceneTraversal()
        trv.collectProfileFromScene(self._x3dObj)
        trv.startExport(self._x3dObj, buf, 'x3d')
        return buf.getvalue() or None

    def _push_field_undo(self, node, fname, old_val):
        """Lightweight undo entry for a single field change — no scene serialization."""
        if self._ai_batch:
            return
        entry = ('field', node, fname, old_val)
        with self._undo_lock:
            self._undo_stack.append(entry)
            if len(self._undo_stack) > self._MAX_UNDO:
                self._undo_stack.pop(0)
            self._redo_stack.clear()
        self._update_undo_actions()

    def _push_undo_snapshot(self):
        if self._ai_batch:
            return  # batch already pushed one snapshot at begin_ai_batch
        if self._x3dObj is None:
            return
        xml = self._serialize_scene()
        if xml:
            with self._undo_lock:
                self._undo_stack.append(xml)
                if len(self._undo_stack) > self._MAX_UNDO:
                    self._undo_stack.pop(0)
                self._redo_stack.clear()
            self._update_undo_actions()

    def _apply_field_entry(self, entry):
        """Apply a lightweight field undo/redo entry and return the reverse entry."""
        _, node, fname, old_val = entry
        try:
            cur_val = getattr(node, fname)
            setattr(node, fname, old_val)
        except Exception:
            return None
        self._sync_xite_via_sai()
        return ('field', node, fname, cur_val)

    def _restore_snapshot(self, xml_str: str):
        from rawkee.io.RKLoadSceneFromFile import RKLoadSceneFromFile
        loader  = RKLoadSceneFromFile()
        x3d_obj = loader.from_xml_string(xml_str)
        if x3d_obj is None:
            return
        self._x3dObj = x3d_obj
        scene = getattr(x3d_obj, 'Scene', None)
        if scene is not None:
            self.setX3DScene(scene)
        self.field_editor.set_node(None)
        self._sync_xite_via_sai()
        self._bind_first_nodes()
        # Re-sync any Script nodes already in the graph so their sockets match restored state
        self._refresh_script_nodes_after_restore()

    def _refresh_script_nodes_after_restore(self):
        """After snapshot restore, update Script eNodes in the graph with new Python objects."""
        # The tree registry was rebuilt by setX3DScene; map DEF → new Script node
        new_by_def = {}
        for node in self.tree_widget._node_registry.values():
            if hasattr(type(node), 'NAME') and type(node).NAME() == 'Script':
                def_ = getattr(node, 'DEF', '') or ''
                if def_:
                    new_by_def[def_] = node
        if not new_by_def:
            return
        for enode in list(self.node_editor_widget.scene.eNodes):
            old_x3d = enode.x3d_node
            if old_x3d is None:
                continue
            if not (hasattr(type(old_x3d), 'NAME') and type(old_x3d).NAME() == 'Script'):
                continue
            def_ = getattr(old_x3d, 'DEF', '') or ''
            new_x3d = new_by_def.get(def_)
            if new_x3d is None:
                continue
            enode.x3d_node = new_x3d
            self.node_editor_widget.refreshScriptNodeSockets(new_x3d)

    def undo(self):
        if not self._undo_stack:
            return
        with self._undo_lock:
            entry = self._undo_stack.pop()
        if isinstance(entry, tuple) and entry[0] == 'field':
            reverse = self._apply_field_entry(entry)
            if reverse:
                with self._undo_lock:
                    self._redo_stack.append(reverse)
        else:
            current = self._serialize_scene()
            if current:
                with self._undo_lock:
                    self._redo_stack.append(current)
            self._restore_snapshot(entry)
        self._update_undo_actions()

    def redo(self):
        if not self._redo_stack:
            return
        with self._undo_lock:
            entry = self._redo_stack.pop()
        if isinstance(entry, tuple) and entry[0] == 'field':
            reverse = self._apply_field_entry(entry)
            if reverse:
                with self._undo_lock:
                    self._undo_stack.append(reverse)
        else:
            current = self._serialize_scene()
            if current:
                with self._undo_lock:
                    self._undo_stack.append(current)
            self._restore_snapshot(entry)
        self._update_undo_actions()

    @Slot()
    def _update_undo_actions(self):
        self.undoAction.setEnabled(bool(self._undo_stack))
        self.redoAction.setEnabled(bool(self._redo_stack))

    def begin_ai_batch(self):
        """Suppress per-node tree rebuilds and X_ITE reloads while AI is editing."""
        self._push_undo_snapshot()  # async snapshot before AI modifies the scene
        self._ai_batch = True
        self._ai_new_defs.clear()

    def end_ai_batch(self):
        """Re-enable updates and do one final tree rebuild + X_ITE reload."""
        self._ai_batch = False
        self._ai_new_defs.clear()
        scene = getattr(self, "_x3dScene", None)
        if scene is not None:
            expanded = self._capture_tree_expanded()
            self.setX3DScene(scene)
            self._restore_tree_expanded(expanded)
        self._sync_xite_via_sai()

    def setX3DScene(self, x3dScene):
        """Populate the tree widget from an rkx.Scene object produced by maya2x3d()."""
        self._x3dScene = x3dScene
        self._build_scene_tree(x3dScene)
        self.node_editor_widget.set_x3d_scene(x3dScene)

    def _build_scene_tree(self, scene):
        self.tree_widget.clearRegistry()
        self.tree_widget.clear()
        if scene is None:
            return
        for node in scene.children:
            try:
                item = self._make_tree_item(node)
                if item:
                    self.tree_widget.addTopLevelItem(item)
            except Exception as e:
                self.console_widget.appendPlainText(
                    f'[ERROR] scene tree root {type(node).__name__}: {e}')

    def _make_tree_item(self, node):
        try:
            return self._make_tree_item_inner(node)
        except Exception as e:
            import traceback
            self.console_widget.appendPlainText(
                f'[ERROR] scene tree {type(node).__name__}: {e}\n'
                + traceback.format_exc().strip())
            return None

    def _make_tree_item_inner(self, node):
        # Skip ROUTE statements — they are not displayed in the tree
        if isinstance(node, rkx.ROUTE):
            return None

        # USE reference — register for drag so addNodeFromX3D can resolve it to the DEF node
        use_val = getattr(node, 'USE', '')
        if use_val:
            node_type = type(node).NAME()
            item = QTreeWidgetItem(["USE '{}' ({})".format(use_val, node_type)])
            item.setData(0, Qt.UserRole, self.tree_widget.registerNode(node))
            return item

        # Regular node — register it so it can be dragged into the node editor
        node_type = type(node).NAME()
        def_name  = getattr(node, 'DEF', '')
        label = "{} DEF='{}'".format(node_type, def_name) if def_name else node_type
        item  = QTreeWidgetItem([label])
        item.setData(0, Qt.UserRole, self.tree_widget.registerNode(node))

        # Recurse into child node fields using FIELD_DECLARATIONS
        if hasattr(type(node), 'FIELD_DECLARATIONS'):
            # Skip Script.field — its UDF entries are shown directly by the block below
            _SKIP = {'class_', 'id_', 'style_', 'IS'} | (
                {'field'} if node_type == 'Script' else set()
            )
            for decl in type(node).FIELD_DECLARATIONS():
                field_name = decl[0]
                if field_name in _SKIP:
                    continue
                # decl[2] is FieldType.<Type> — call it to get the type string
                try:
                    field_type = decl[2]()
                except Exception:
                    field_type = ''
                if field_type not in ('SFNode', 'MFNode'):
                    continue
                try:
                    value = getattr(node, field_name, None)
                except Exception:
                    continue
                if value is None:
                    continue
                if isinstance(value, list):
                    child_nodes = [v for v in value if hasattr(v, 'NAME')]
                    if child_nodes:
                        field_item = QTreeWidgetItem([field_name])
                        for child_node in child_nodes:
                            child_item = self._make_tree_item(child_node)
                            if child_item:
                                field_item.addChild(child_item)
                        item.addChild(field_item)
                elif hasattr(value, 'NAME'):
                    field_item = QTreeWidgetItem([field_name])
                    child_item = self._make_tree_item(value)
                    if child_item:
                        field_item.addChild(child_item)
                    item.addChild(field_item)

        # Show SFNode/MFNode user-defined fields as persistent tree children
        if node_type == 'Script':
            for fobj in list(getattr(node, 'field', None) or []):
                if getattr(fobj, 'type', '') not in ('SFNode', 'MFNode'):
                    continue
                fname   = getattr(fobj, 'name',       '') or ''
                faccess = getattr(fobj, 'accessType', '') or ''
                ftype   = getattr(fobj, 'type', '') or ''
                udf_item = QTreeWidgetItem([f'{fname}  [{ftype}  {faccess}]'])
                udf_item.setForeground(0, QBrush(QColor('#7a7a7a')))
                udf_item.setData(0, Qt.UserRole + 1, fname)  # real field name for insertion
                for child_node in list(getattr(fobj, 'children', None) or []):
                    if hasattr(child_node, 'NAME'):
                        child_item = self._make_tree_item(child_node)
                        if child_item:
                            udf_item.addChild(child_item)
                item.addChild(udf_item)

        return item

    def centerNodeEditor(self, qpoint=QPointF(0,0)):
        self.node_editor_widget.centerViewOn(qpoint)

        
    def setRKWeb3D(self, rkWeb3D):
        # Reserved for future DCC-host integration.
        pass

    def cleanUpOnEditorClose(self):
        if self.bkHost:
            self.bkHost.stop()
            self.bkHost = None

    def _sync_ai_panel_action(self, visible: bool):
        """Sync the menu action check state without re-triggering setVisible (avoids minimize hiding the dock)."""
        self.toggleAIPanel.blockSignals(True)
        self.toggleAIPanel.setChecked(visible)
        self.toggleAIPanel.blockSignals(False)

    def closeEvent(self, event):
        s = QSettings("RawKee", "RKSceneEditor")
        s.setValue("ai_dock_visible", self._ai_dock.isVisible())
        self.ai_panel.save_settings()
        self.cleanUpOnEditorClose()
        super().closeEvent(event)

    _SERVER_PORT = 8765

    def _local_url(self, abs_path):
        """Convert an absolute local path to http://localhost URL."""
        abs_path = os.path.abspath(abs_path)
        if sys.platform == 'win32':
            _, tail = os.path.splitdrive(abs_path)
            url_path = tail.replace('\\', '/').lstrip('/')
        else:
            url_path = abs_path.lstrip('/')
        return f'http://localhost:{self._SERVER_PORT}/{url_path}'

    def setURLPaths(self):
        # Use this file's directory so examples/ always resolves to rawkee/examples/
        self.basePath = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")

        # Serve the entire drive so any local X3D file and its textures are reachable
        if sys.platform == 'win32':
            drive_root = os.path.splitdrive(os.path.abspath(self.basePath))[0] + os.sep
        else:
            drive_root = '/'
        self.bkHost = RKBackgroundHost(directory=drive_root, port=self._SERVER_PORT)
        self.bkHost.start()
        import atexit
        atexit.register(self.cleanUpOnEditorClose)

        xite_abs = os.path.normpath(os.path.join(self.basePath, 'x_ite.html'))
        self.x_itePath = self._local_url(xite_abs) + '?v=20260803'
        
        
    def create_actions(self):
        self.undoAction = QAction("   Undo")
        self.undoAction.setShortcut(QKeySequence.StandardKey.Undo)
        self.undoAction.setEnabled(False)
        self.undoAction.triggered.connect(self.undo)
        self.redoAction = QAction("   Redo")
        self.redoAction.setShortcut(QKeySequence.StandardKey.Redo)
        self.redoAction.setEnabled(False)
        self.redoAction.triggered.connect(self.redo)
        self.newX3DScene    = QAction("   New X3D Scene")
        self.openX3DFile    = QAction("   Open X3D")
        self.exportX3DAs    = QAction("   Save X3D As...")
        self.copySceneMaya  = QAction("   Copy Entire Maya Scene")
        self.copySelectMaya = QAction("   Copy Selected Maya Nodes")
        self.pasteSGToMaya  = QAction("   Paste Entire X3D Scenegraph")
        self.pasteSubToMaya = QAction("   Paste Selected X3D Subgraph")
        
        self.sendToSunrise  = QAction("   Sunrize X3D Editor")
        self.sendToCastle   = QAction("   Castle Game Engine")
        self.closeEditor    = QAction("   Close Editor")

        self.toggleAIPanel  = QAction("   AI Assistant")
        self.toggleAIPanel.setCheckable(True)
#        self.testMenu       = QMenu()
#        self.qtBut          = QtWidgets.QPushButton()
#        self.qIcon          = QtGui.QIcon(":menu_options.png")
#        self.qIcon.setFixedSize(20, 20)
#        self.qtBut.setIcon(self.qIcon)
#        self.qtBut.setText("Push my button")
        
    def create_widgets(self):
        file_menu   = self.menuBar().addMenu("File")
        edit_menu   = self.menuBar().addMenu("Edit")
        edit_menu.addAction(self.undoAction)
        edit_menu.addAction(self.redoAction)
        node_menu   = self.menuBar().addMenu("X3D Nodes")
        tools_menu  = self.menuBar().addMenu("Tools")
        tools_menu.addAction(self.toggleAIPanel)
        help_menu = self.menuBar().addMenu("Help")
        about_action = help_menu.addAction("About RawKee X3D Interaction Editor")
        about_action.triggered.connect(self._on_about)

        file_menu.addAction(self.newX3DScene)
        file_menu.addAction(self.openX3DFile)
        file_menu.addAction(self.exportX3DAs)
        file_menu.addSection("Maya Copy/Paste")
        file_menu.addAction(self.copySceneMaya)
        file_menu.addAction(self.copySelectMaya)
        file_menu.addSection(" ")
        file_menu.addAction(self.pasteSGToMaya)
        file_menu.addAction(self.pasteSubToMaya)
        file_menu.addSection("Send to External")
        file_menu.addAction(self.sendToSunrise)
        file_menu.addAction(self.sendToCastle)
        file_menu.addSeparator()
        file_menu.addAction(self.closeEditor)

        # Build one submenu per X3D component, each listing the nodes in that component
        _EXCLUDE = frozenset({'ROUTE', 'field', 'X3D', 'Scene'})
        comp_map = self._build_x3d_component_map()
        for comp_name in sorted(comp_map):
            nodes = [n for n in sorted(comp_map[comp_name]) if n not in _EXCLUDE]
            if not nodes:
                continue
            sub = node_menu.addMenu(comp_name)
            for node_name in nodes:
                action = sub.addAction(node_name)
                action.triggered.connect(partial(self._add_node_to_editor, node_name))

        self.tree_widget = RKX3DTreeWidget()
        self.tree_widget.setHeaderLabels(['X3D Scenegraph'])

        self.field_editor = RKNodeFieldEditor()

        self.browser = QWebEngineView()
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        self.custom_page = RKCustomWebEnginePage(self.browser)
        self.browser.setPage(self.custom_page)
        self.browser.page().setBackgroundColor(QColor(0, 0, 0))

        self.node_editor_widget = RKCustomNodeEditor(self.tree_widget, parent=self)

        self.console_widget = QPlainTextEdit()
        self.console_widget.setReadOnly(True)
        self.console_widget.setMaximumHeight(180)
        self.console_widget.setMinimumHeight(60)
        self.console_widget.setPlaceholderText("Output / Errors")
        self.custom_page.set_console(self.console_widget)

        self.ai_panel = RKAIAssistantPanel()
        self.ai_panel.set_editor(self)
        self._ai_dock = QtWidgets.QDockWidget("AI Assistant", self)
        self._ai_dock.setObjectName("RKAIDock")
        self._ai_dock.setWidget(self.ai_panel)
        self._ai_dock.setMinimumWidth(320)
        self._ai_dock.hide()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._ai_dock)
        if QSettings("RawKee", "RKSceneEditor").value("ai_dock_visible") in (True, "true"):
            self._ai_dock.show()

        self.console_container = QWidget()
        _cc_layout = QtWidgets.QVBoxLayout(self.console_container)
        _cc_layout.setContentsMargins(0, 0, 0, 0)
        _cc_layout.setSpacing(2)
        _cc_layout.addWidget(self.console_widget)

        # Disabled in standalone mode — require a DCC host
        for action in (self.copySceneMaya, self.copySelectMaya,
                       self.pasteSGToMaya, self.pasteSubToMaya):
            action.setEnabled(False)

    def create_layout(self):
        # Left vertical splitter: X_ITE browser on top, graph editor on bottom
        self.left_splitter = QSplitter(QtCore.Qt.Orientation.Vertical)
        self.left_splitter.addWidget(self.browser)
        self.left_splitter.addWidget(self.node_editor_widget)
        self.left_splitter.setSizes([500, 500])

        # Right panel: scenegraph tree on top, field editor on bottom
        self.tree_panel_splitter = QSplitter(QtCore.Qt.Orientation.Vertical)
        self.tree_panel_splitter.addWidget(self.tree_widget)
        self.tree_panel_splitter.addWidget(self.field_editor)
        self.tree_panel_splitter.setSizes([300, 200])
        self.tree_panel_splitter.setMaximumWidth(400)
        self.tree_panel_splitter.setMinimumWidth(250)

        # Top horizontal splitter: left panels | tree+field panel
        self.top_splitter = QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.top_splitter.addWidget(self.left_splitter)
        self.top_splitter.addWidget(self.tree_panel_splitter)
        self.top_splitter.setSizes([900, 300])

        # Main vertical splitter: top panels | console
        self.main_splitter = QSplitter(QtCore.Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.top_splitter)
        self.main_splitter.addWidget(self.console_container)
        self.main_splitter.setSizes([800, 160])

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_splitter)

        self.browser.setUrl(QUrl(self.x_itePath))
        
    def create_connections(self):
        self.newX3DScene.triggered.connect(self.on_new_scene)
        self.openX3DFile.triggered.connect(self.on_open_file)
        self.exportX3DAs.triggered.connect(self.on_export_as)
        self.closeEditor.triggered.connect(self.close)
        self.node_editor_widget.scene.set_sai_runner(
            lambda js: self.browser.page().runJavaScript(js))
        self.browser.loadFinished.connect(self._on_page_load_finished)
        self.tree_widget.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.node_editor_widget.scene.grScene.selectionChanged.connect(self._on_graph_selection_changed)
        self.node_editor_widget.view.set_add_node_callback(self._add_node_from_graph)
        self.tree_widget.set_reparent_callback(self._reparent_node)
        self.tree_widget.set_insert_key_callback(self._run_node_picker)
        self.tree_widget.set_bind_key_callback(self._bind_selected_node)
        self.field_editor.set_sai_runner(lambda js: self.browser.page().runJavaScript(js))
        self.field_editor.set_undo_push_fn(self._push_undo_snapshot)
        self.field_editor.set_field_undo_fn(self._push_field_undo)
        self.field_editor.set_graph_refresh_fn(
            lambda node: (
                self.node_editor_widget.refreshScriptNodeSockets(node),
                self._sync_xite_via_sai(),
            )
        )
        self.toggleAIPanel.toggled.connect(self._ai_dock.setVisible)
        # Block toggleAIPanel signals when syncing check state to prevent minimize from hiding the dock
        self._ai_dock.visibilityChanged.connect(self._sync_ai_panel_action)


    def _on_tree_selection_changed(self):
        selected = self.tree_widget.selectedItems()
        if len(selected) != 1:
            self.field_editor.set_node(None)
            return

        key  = selected[0].data(0, Qt.UserRole)
        node = self.tree_widget.nodeForKey(key) if key else None

        if node is None:
            self.field_editor.set_node(None)
            return

        use_val = getattr(node, 'USE', '')
        if use_val:
            # Resolve USE reference to its DEF counterpart in the registry
            node_type = type(node)
            node = next(
                (c for c in self.tree_widget._node_registry.values()
                 if type(c) is node_type and getattr(c, 'DEF', '') == use_val),
                None)

        # Show: DEF node, anonymous node (no DEF and no USE), or resolved DEF node
        self.field_editor.set_node(node)


    def _reparent_node(self, source_nodes, target_node):
        if self._x3dScene is None:
            return
        self._push_undo_snapshot()
        for source_node in source_nodes:
            if source_node is target_node:
                continue
            if any(n is target_node for n in self._collect_subtree(source_node)):
                self.console_widget.appendPlainText(
                    f'[WARN] Cannot reparent {type(source_node).NAME()} onto its own descendant — skipped.')
                continue
            field_name, _is_mf, err = self._best_field_for_child(target_node, source_node)
            if err:
                self.console_widget.appendPlainText(f'[WARN] {err} — skipped.')
                continue
            self._remove_node_from_scenegraph(source_node)
            node_name = type(source_node).NAME() if hasattr(type(source_node), 'NAME') else type(source_node).__name__
            ok, msg = self._insert_into_field(target_node, field_name, source_node, node_name)
            if not ok:
                self.console_widget.appendPlainText(f'[WARN] {msg} — skipped.')
        expanded = self._capture_tree_expanded()
        self.setX3DScene(self._x3dScene)
        self._restore_tree_expanded(expanded)
        if source_nodes:
            self._reveal_tree_node(source_nodes[-1])
        self._sync_xite_via_sai()

    def _add_node_from_graph(self, scene_pos):
        new_node = self._run_node_picker()
        if new_node is not None:
            self.node_editor_widget.addNodeFromX3D(new_node, scene_pos)

    def _run_node_picker(self):
        _EXCLUDE = frozenset({'ROUTE', 'field', 'X3D', 'Scene'})
        comp_map = self._build_x3d_component_map()
        all_names = sorted(n for nodes in comp_map.values() for n in nodes if n not in _EXCLUDE)
        dialog = _RKNodePickerDialog(all_names, self._get_container_fields_for, self)
        if dialog.exec() != QDialog.Accepted:
            return None
        node_name       = dialog.chosen_name()
        container_field = dialog.chosen_name2() or None
        if not node_name:
            return None
        return self._add_node_to_editor(node_name, override_field=container_field)

    # Fields whose base-class setters have a broken isinstance(x, object) check;
    # map to the abstract class that must actually be satisfied.
    _BROKEN_SETTER_FIELDS = {
        'metadata': '_X3DMetadataObject',
    }

    def _get_container_fields_for(self, node_name):
        """Return sorted SFNode/MFNode fields of the selected parent that actually accept node_name."""
        selected = self.tree_widget.selectedItems()
        if not selected:
            return ['children']
        sel_item = selected[0]
        key = sel_item.data(0, Qt.UserRole)
        parent_node = self.tree_widget.nodeForKey(key) if key else None
        if parent_node is None:
            # Field-group item selected — walk up to the owning node item
            parent_item = sel_item.parent()
            if parent_item is not None:
                pk = parent_item.data(0, Qt.UserRole)
                parent_node = self.tree_widget.nodeForKey(pk) if pk else None
        if parent_node is None:
            return []

        node_cls = getattr(rkx, node_name, None)
        try:
            test_child = node_cls() if node_cls else None
        except Exception:
            test_child = None

        try:
            test_parent = type(parent_node)()
        except Exception:
            test_parent = None

        fields = []
        if hasattr(type(parent_node), 'FIELD_DECLARATIONS'):
            for decl in type(parent_node).FIELD_DECLARATIONS():
                fname = decl[0]
                if fname == 'IS':
                    continue
                try:
                    ftype = decl[2]()
                except Exception:
                    continue
                if ftype not in ('SFNode', 'MFNode'):
                    continue
                try:
                    access = decl[3]()
                except Exception:
                    access = ''
                if access in ('inputOnly', 'outputOnly'):
                    continue
                # For fields with known broken setters, check abstract type directly
                if fname in self._BROKEN_SETTER_FIELDS:
                    abs_name = self._BROKEN_SETTER_FIELDS[fname]
                    abs_cls = getattr(rkx, abs_name, None)
                    if node_cls is None or abs_cls is None:
                        continue
                    if not issubclass(node_cls, abs_cls):
                        continue
                    fields.append(fname)
                    continue
                if test_child is None or test_parent is None:
                    fields.append(fname)
                    continue
                # Validate by attempting a test assignment on a throwaway parent
                try:
                    if ftype == 'MFNode':
                        setattr(test_parent, fname, [test_child])
                    else:
                        setattr(test_parent, fname, test_child)
                    fields.append(fname)
                except Exception:
                    pass

        # Include user-defined SFNode/MFNode fields on Script nodes
        # Only inputOutput/initializeOnly fields can carry child-node values
        _CAN_HOLD_NODES = frozenset({'inputOutput', 'initializeOnly'})
        if hasattr(type(parent_node), 'NAME') and type(parent_node).NAME() == 'Script':
            for fobj in list(getattr(parent_node, 'field', None) or []):
                if getattr(fobj, 'type', '') in ('SFNode', 'MFNode'):
                    if getattr(fobj, 'accessType', '') not in _CAN_HOLD_NODES:
                        continue
                    fn = getattr(fobj, 'name', '') or ''
                    if fn and fn not in fields:
                        fields.append(fn)

        return sorted(fields)

    def _on_graph_selection_changed(self):
        from rawkee.editor.RKXGraphicsNode import RKXGraphicsNode as _GrNode
        items = self.node_editor_widget.scene.grScene.selectedItems()
        gr_nodes = [it for it in items if isinstance(it, _GrNode)]
        if len(gr_nodes) != 1:
            return
        x3d_node = getattr(gr_nodes[0].eNode, 'x3d_node', None)
        if x3d_node is not None:
            self._reveal_tree_node(x3d_node)

    def _on_tree_context_menu(self, pos):
        _SEP_STYLE = "QMenu::separator { background: #39FF14; height: 2px; margin: 2px 4px; }"
        menu = QMenu(self.tree_widget)
        menu.setStyleSheet(_SEP_STYLE)
        add_action = menu.addAction("Add Node")

        # "Delete Node" submenu only available when hovering over the currently selected item
        del_now_action = None
        hovered  = self.tree_widget.itemAt(pos)
        selected = self.tree_widget.selectedItems()
        del_node = None
        if hovered is not None and selected and hovered is selected[0]:
            key = hovered.data(0, Qt.UserRole)
            candidate = self.tree_widget.nodeForKey(key) if key else None
            if candidate is not None and not getattr(candidate, 'USE', ''):
                del_node = candidate
                menu.addSeparator()
                del_sub = menu.addMenu("Delete Node")
                del_sub.setStyleSheet(_SEP_STYLE)
                del_now_action = del_sub.addAction("Delete Now!")

        # User-defined node-field management for Script nodes
        add_sfnode_act = add_mfnode_act = None
        remove_udf_acts = {}  # action → fobj
        if (del_node is not None
                and hasattr(type(del_node), 'NAME')
                and type(del_node).NAME() == 'Script'):
            menu.addSeparator()
            udf_sub = menu.addMenu("User-Defined Node Fields")
            udf_sub.setStyleSheet(_SEP_STYLE)
            add_sfnode_act = udf_sub.addAction("Add SFNode field\u2026")
            add_mfnode_act = udf_sub.addAction("Add MFNode field\u2026")
            node_udfs = [
                fo for fo in list(getattr(del_node, 'field', None) or [])
                if getattr(fo, 'type', '') in ('SFNode', 'MFNode')
            ]
            if node_udfs:
                udf_sub.addSeparator()
                for fo in node_udfs:
                    lbl = f"Remove '{fo.name}'  [{fo.type}  {fo.accessType}]"
                    act = udf_sub.addAction(lbl)
                    remove_udf_acts[act] = fo

        chosen = menu.exec(self.tree_widget.viewport().mapToGlobal(pos))
        if chosen is add_action:
            self._run_node_picker()
        elif del_now_action is not None and chosen is del_now_action:
            self._delete_node(del_node)
        elif add_sfnode_act is not None and chosen is add_sfnode_act:
            self._add_node_udf(del_node, 'SFNode')
        elif add_mfnode_act is not None and chosen is add_mfnode_act:
            self._add_node_udf(del_node, 'MFNode')
        elif chosen in remove_udf_acts:
            self._remove_node_udf(del_node, remove_udf_acts[chosen])

    def _add_node_udf(self, script_node, field_type):
        """Prompt for name/access-type and add an SFNode/MFNode UDF to a Script node."""
        name, ok = QInputDialog.getText(
            self, f'Add {field_type} Field', 'Field name:'
        )
        if not ok or not (name := name.strip()):
            return
        taken = RKNodeFieldEditor._script_field_names(script_node)
        if name in taken:
            QMessageBox.warning(
                self, 'Duplicate Field Name',
                f'"{name}" is already defined on this Script node.\n'
                'Please choose a unique field name.'
            )
            return
        access, ok = QInputDialog.getItem(
            self, f'Add {field_type} Field', 'Access type:',
            ['inputOnly', 'outputOnly', 'inputOutput', 'initializeOnly'], 0, False
        )
        if not ok:
            return
        import rawkee.io.RKx3d as _rkx
        try:
            f = _rkx.field()
            f.name       = name
            f.type       = field_type
            f.accessType = access
        except Exception as e:
            print(f'Error creating user-defined field: {e}', flush=True)
            return
        self._push_undo_snapshot()
        if not isinstance(getattr(script_node, 'field', None), list):
            script_node.field = []
        script_node.field.append(f)
        self.node_editor_widget.refreshScriptNodeSockets(script_node)
        self._sync_xite_via_sai()
        expanded = self._capture_tree_expanded()
        self.setX3DScene(self._x3dScene)
        self._restore_tree_expanded(expanded)
        self.field_editor.set_node(script_node)

    def _remove_node_udf(self, script_node, field_obj):
        """Remove an SFNode/MFNode UDF from a Script node."""
        existing = list(getattr(script_node, 'field', None) or [])
        if field_obj not in existing:
            return
        self._push_undo_snapshot()

        # Collect all descendant nodes so routes and graph canvas entries can be cleaned up
        subtree = []
        for child in list(getattr(field_obj, 'children', None) or []):
            RKSceneEditor._collect_subtree(child, subtree)
        if subtree and self._x3dScene is not None:
            subtree_defs = {getattr(n, 'DEF', '') for n in subtree} - {''}
            if subtree_defs:
                self._x3dScene.children = [
                    c for c in self._x3dScene.children
                    if not (hasattr(c, 'fromNode')
                            and (c.fromNode in subtree_defs or c.toNode in subtree_defs))
                ]
            subtree_ids = {id(n) for n in subtree}
            scene = self.node_editor_widget.scene
            dead_ens = [en for en in scene.eNodes
                        if id(getattr(en, 'x3d_node', None)) in subtree_ids]
            if dead_ens:
                dead_set = {id(en) for en in dead_ens}
                for edge in list(scene.eEdges):
                    ss, es = edge.start_socket, edge.end_socket
                    if ((ss and id(ss.eNode) in dead_set)
                            or (es and id(es.eNode) in dead_set)):
                        if edge.grEdge is not None:
                            scene.grScene.removeItem(edge.grEdge)
                        scene.eEdges.remove(edge)
                for en in dead_ens:
                    if en.grNode is not None:
                        scene.grScene.removeItem(en.grNode)
                    scene.eNodes.remove(en)

        existing.remove(field_obj)
        script_node.field = existing
        self.node_editor_widget.refreshScriptNodeSockets(script_node)
        self._sync_xite_via_sai()
        expanded = self._capture_tree_expanded()
        self.setX3DScene(self._x3dScene)
        self._restore_tree_expanded(expanded)
        self.field_editor.set_node(script_node)

    @staticmethod
    def _collect_subtree(node, out=None):
        if out is None:
            out = []
        if not hasattr(node, 'NAME'):
            return out
        out.append(node)
        if hasattr(type(node), 'FIELD_DECLARATIONS'):
            for decl in type(node).FIELD_DECLARATIONS():
                try:
                    ftype = decl[2]()
                except Exception:
                    continue
                if ftype not in ('SFNode', 'MFNode'):
                    continue
                try:
                    val = getattr(node, decl[0], None)
                except Exception:
                    continue
                if val is None:
                    continue
                for child in (val if isinstance(val, list) else [val]):
                    RKSceneEditor._collect_subtree(child, out)
        return out

    def _delete_node(self, node):
        """Remove node and all its descendants from scenegraph, ROUTEs, and graph editor."""
        self._push_undo_snapshot()
        if self._x3dScene is None:
            return

        subtree = self._collect_subtree(node)
        subtree_defs = {getattr(n, 'DEF', '') for n in subtree} - {''}
        subtree_ids  = {id(n) for n in subtree}

        # Remove all ROUTEs referencing any node in the subtree
        if subtree_defs:
            self._x3dScene.children = [
                c for c in self._x3dScene.children
                if not (hasattr(c, 'fromNode')
                        and (c.fromNode in subtree_defs or c.toNode in subtree_defs))
            ]

        # Remove all matching eNodes and their edges from the graph editor canvas
        scene = self.node_editor_widget.scene
        target_ens = [en for en in scene.eNodes
                      if id(getattr(en, 'x3d_node', None)) in subtree_ids]
        if target_ens:
            target_en_set = set(id(en) for en in target_ens)
            for edge in list(scene.eEdges):
                ss, es = edge.start_socket, edge.end_socket
                if ((ss and id(ss.eNode) in target_en_set)
                        or (es and id(es.eNode) in target_en_set)):
                    if edge.grEdge is not None:
                        scene.grScene.removeItem(edge.grEdge)
                    scene.eEdges.remove(edge)
            for en in target_ens:
                if en.grNode is not None:
                    scene.grScene.removeItem(en.grNode)
                scene.eNodes.remove(en)

        # Detach the root node from its parent (descendants go with it)
        self._remove_node_from_scenegraph(node)

        expanded = self._capture_tree_expanded()
        self.setX3DScene(self._x3dScene)
        self._restore_tree_expanded(expanded)
        self.field_editor.set_node(None)
        self._sync_xite_via_sai()

    def _remove_node_from_scenegraph(self, target):
        """Detach target from whichever parent field holds it."""
        if self._x3dScene is None:
            return
        if any(x is target for x in self._x3dScene.children):
            self._x3dScene.children = [x for x in self._x3dScene.children if x is not target]
            return

        def _strip(parent, tgt):
            if not hasattr(type(parent), 'FIELD_DECLARATIONS'):
                return False
            for decl in type(parent).FIELD_DECLARATIONS():
                try:
                    ftype = decl[2]()
                except Exception:
                    continue
                if ftype not in ('SFNode', 'MFNode'):
                    continue
                fname = decl[0]
                try:
                    val = getattr(parent, fname, None)
                except Exception:
                    continue
                if ftype == 'MFNode' and isinstance(val, list):
                    if any(x is tgt for x in val):
                        setattr(parent, fname, [x for x in val if x is not tgt])
                        return True
                    for child in val:
                        if hasattr(child, 'NAME') and _strip(child, tgt):
                            return True
                elif ftype == 'SFNode':
                    if val is tgt:
                        setattr(parent, fname, None)
                        return True
                    if val is not None and hasattr(val, 'NAME') and _strip(val, tgt):
                        return True
            return False

        for child in list(self._x3dScene.children):
            if hasattr(child, 'NAME') and _strip(child, target):
                return

    def _on_test_routes(self):
        self.browser.page().runJavaScript(
            "(function(){"
            " var b=document.querySelector('x3d-canvas').browser;"
            " if(!b){console.log('No browser');return;}"
            " var s=b.currentScene;"
            " try{"
            "  var n=s.getNamedNode('myTransform');"
            "  n.translation=new n.translation.constructor(0,0,0);"
            "  console.log('myTransform translation reset to origin');"
            " }catch(e){console.log('Error: '+e);}"
            "})()"
        )
    def _on_page_load_finished(self, ok):
        pass  # src is never changed after initial load; SAI manages the scene

    def on_item_viewer_selection(self, index):
        pass  # player control dropdown removed

    def on_new_scene(self):
        self._x3dObj = None
        self._ai_new_defs.clear()
        with self._undo_lock:
            self._undo_stack.clear()
            self._redo_stack.clear()
        self._update_undo_actions()
        self.node_editor_widget.clearGraph()
        self.setX3DScene(None)
        self.ai_panel.reset_for_new_scene()
        self.browser.page().runJavaScript('RK.clearScene();')
        self.setWindowTitle("RawKee PE - X3D Interaction Editor")

    def _bind_first_nodes(self):
        """Bind the first of each bindable node type in X_ITE after a scene load or restore."""
        self.browser.page().runJavaScript(
            f'(async function(){{try{{'
            f'const b=document.querySelector("x3d-canvas").browser;'
            f'await b.nextFrame();'
            f'const s=b.currentScene;'
            f'var bindVp=true,bindNav=true,bindBg=true,bindFog=true;'
            f'for(let i=0;i<s.rootNodes.length;i++){{'
            f'const n=s.rootNodes[i];try{{const t=n&&n.getNodeTypeName();'
            f'if(bindVp&&(t=="Viewpoint"||t=="OrthoViewpoint"||t=="GeoViewpoint")){{n.set_bind=true;bindVp=false;}}'
            f'if(bindNav&&t=="NavigationInfo"){{n.set_bind=true;bindNav=false;}}'
            f'if(bindBg&&(t=="Background"||t=="TextureBackground")){{n.set_bind=true;bindBg=false;}}'
            f'if(bindFog&&t=="Fog"){{n.set_bind=true;bindFog=false;}}'
            f'}}catch(_){{}}'
            f'}}'
            f'}}catch(e){{console.log("bind:"+e)}}}})();'
        )

    def on_open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open X3D File", "",
            "X3D Files (*.x3d *.x3dj *.x3dv);;All Files (*)")
        if not file_path:
            return
        loader = RKLoadSceneFromFile()
        x3d = loader.disk2x3d(file_path)
        if x3d is None:
            QMessageBox.warning(self, "Open Failed", f"Could not load:\n{file_path}")
            return
        self._x3dObj = x3d
        self.node_editor_widget.clearGraph()
        scene_node = getattr(x3d, 'Scene', None)
        self.setX3DScene(scene_node)
        self.ai_panel.reset_for_new_scene()
        self._sync_xite_via_sai()
        self._bind_first_nodes()

    def on_export_as(self):
        if self._x3dObj is None:
            QMessageBox.warning(self, "Export X3D", "No X3D scene to export.")
            return
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save X3D As...", "",
            "X3D XML (*.x3d);;X3D Classic VRML (*.x3dv);;X3D JSON (*.x3dj)")
        if not file_path:
            return
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".x3dv" or "x3dv" in selected_filter:
            encoding = "x3dv"
            if not file_path.lower().endswith(".x3dv"):
                file_path += ".x3dv"
        elif ext == ".x3dj" or "x3dj" in selected_filter:
            encoding = "x3dj"
            if not file_path.lower().endswith(".x3dj"):
                file_path += ".x3dj"
        else:
            encoding = "x3d"
            if not file_path.lower().endswith(".x3d"):
                file_path += ".x3d"
        try:
            trv = RKSceneTraversal()
            trv.collectProfileFromScene(self._x3dObj)
            trv.x3d2disk(self._x3dObj, file_path, encoding)
            #self.setWindowTitle(f"RawKee PE - {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def on_clear_graph(self):
        self.node_editor_widget.clearGraph()

    def _on_about(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("About RawKee X3D Interaction Editor")
        dlg.setText(
            "Created by Aaron Bergstrom\n"
            "Advanced Cyberinfrastructure Manager\n"
            "University of North Dakota\n"
            "Computational Research Center\n"
            "Laboratory for Digital Realism in Engineering and the Applied Metaverse\n(UND DREAM Lab - http://dream.und.edu)\n\n"
            "In loving memory of his brother Eric (AwKie \u2013 Rocky) Bergstrom\n\n"
            "X3D Rendering using X_ITE (https://x-ite.github.io/)\n"
            "X_ITE is created by Holger Seelig\n"
        )
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        from PySide6.QtGui import QColor, QIcon
        _ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'x3d_interaction_editor3.ico')
        dlg.setIconPixmap(QIcon(_ico).pixmap(64, 64))
        # Swap only the highlight/glow color from green to icon-matching cyan-blue
        btn = dlg.button(QMessageBox.StandardButton.Ok)
        p = btn.palette()
        p.setColor(p.ColorRole.Highlight,      QColor('#29b6f6'))
        p.setColor(p.ColorRole.HighlightedText, QColor('#ffffff'))
        p.setColor(p.ColorRole.Button,          QColor('#29b6f6').darker(300))
        btn.setPalette(p)
        dlg.exec()

    @staticmethod
    def _build_x3d_component_map():
        """Parse component->{node_names} from instantiateNodeFromString source without instantiating."""
        import inspect, re
        try:
            src = inspect.getsource(rkx.instantiateNodeFromString)
        except Exception:
            return {}
        entry_pat = re.compile(r"'([A-Z]\w+)':\s*\([^{]+(\{[^}]+\})")
        comp_pat  = re.compile(r"'([A-Za-z0-9_]+)':\s*(\d+)")
        _GENERIC  = frozenset({'Core', 'Grouping', 'Rendering', 'Shape', 'Texturing',
                               'Time', 'EnvironmentalSensor', 'Navigation', 'Interpolation'})
        # Standard X3D spec components; anything outside this set is an extension component
        _STANDARD = frozenset({
            'CADGeometry', 'Core', 'CubeMapTexturing', 'DIS', 'EnvironmentalEffects',
            'EnvironmentalSensor', 'EventUtilities', 'Followers', 'Geometry2D', 'Geometry3D',
            'Geospatial', 'Grouping', 'HAnim', 'Interpolation', 'KeyDeviceSensor', 'Layering',
            'Layout', 'Lighting', 'Navigation', 'Networking', 'NURBS', 'ParticleSystems',
            'PickingSensor', 'PointingDeviceSensor', 'Rendering', 'RigidBodyPhysics',
            'Scripting', 'Shaders', 'Shape', 'Sound', 'Text', 'Texturing', 'Texturing3D',
            'Time', 'VolumeRendering',
        })
        comp_map = {}
        for m in entry_pat.finditer(src):
            node_name = m.group(1)
            comps = {cm.group(1): int(cm.group(2)) for cm in comp_pat.finditer(m.group(2))}
            if not comps:
                continue
            # Extension components (not in the X3D spec) always take priority
            ext = {c: l for c, l in comps.items() if c not in _STANDARD}
            if ext:
                primary = sorted(ext, key=lambda c: -ext[c])[0]
            else:
                non_core = {c: l for c, l in comps.items() if c != 'Core'}
                pool     = non_core if non_core else comps
                max_lvl  = max(pool.values())
                cands    = [c for c, l in pool.items() if l == max_lvl]
                specific = [c for c in cands if c not in _GENERIC]
                primary  = specific[0] if specific else sorted(cands)[0]
            comp_map.setdefault(primary, []).append(node_name)
        return comp_map

    def _add_node_to_editor(self, node_name, override_field=None, direct_parent=None):
        """Insert a new X3D node into the scenegraph, rebuild the tree, and sync X_ITE via temp file."""
        # Auto-create a minimal scene if none is loaded yet
        if self._x3dObj is None or getattr(self, '_x3dScene', None) is None:
            self._x3dObj = rkx.X3D()
            self._x3dObj.Scene = rkx.Scene()
            self.setX3DScene(self._x3dObj.Scene)

        if direct_parent is None:
            self._push_undo_snapshot()
            selected = self.tree_widget.selectedItems()
            if len(selected) > 1:
                QMessageBox.warning(self, "Multiple Selection",
                    "Select only one item in the scenegraph tree.")
                return
        else:
            selected = []

        node_cls = getattr(rkx, node_name, None)
        if node_cls is None or not callable(node_cls):
            self.console_widget.appendPlainText(f'[WARN] node class not found: {node_name}')
            return
        try:
            new_node = node_cls()
        except Exception as e:
            self.console_widget.appendPlainText(f'[ERROR] cannot create {node_name}: {e}')
            return

        try:
            new_node.DEF = self._next_unique_def(type(new_node).NAME())
        except Exception:
            pass

        _xite_parent = None  # resolved parent py-node for incremental SAI add
        _xite_field  = 'children'

        if direct_parent is not None:
            # Bypass tree selection: insert directly into the given parent node
            field_name = override_field
            if not field_name:
                field_name, _is_mf, err = self._best_field_for_child(direct_parent, new_node)
                if err:
                    self.console_widget.appendPlainText(f'[AI] Cannot add {node_name}: {err}')
                    return None
            ok, msg = self._insert_into_field(direct_parent, field_name, new_node, node_name)
            if not ok:
                self.console_widget.appendPlainText(f'[AI] Cannot add {node_name}: {msg}')
                return None
            _xite_parent, _xite_field = direct_parent, field_name
        elif not selected:
            # No selection: append directly to Scene.children
            try:
                self._x3dScene.children.append(new_node)
            except Exception as e:
                QMessageBox.warning(self, "Cannot Add Node",
                    f"Could not append {node_name} to Scene children:\n{e}")
                return
            _xite_parent, _xite_field = None, 'children'
        else:
            sel_item = selected[0]
            sel_key  = sel_item.data(0, Qt.UserRole)

            if sel_key:
                # Selection is a registered node → use override field or auto-detect best field
                parent_node = self.tree_widget.nodeForKey(sel_key)
                if parent_node is None:
                    QMessageBox.warning(self, "No Target", "Could not resolve selected node.")
                    return
                if override_field:
                    field_name = override_field
                else:
                    field_name, _is_mf, err = self._best_field_for_child(parent_node, new_node)
                    if err:
                        QMessageBox.warning(self, "Cannot Add Node", err)
                        return
            else:
                # Selection is a field-group header item — use that field explicitly
                parent_item = sel_item.parent()
                if parent_item is None:
                    QMessageBox.warning(self, "No Target",
                        "Select a node item, not a scene root field label.")
                    return
                parent_key  = parent_item.data(0, Qt.UserRole)
                parent_node = self.tree_widget.nodeForKey(parent_key) if parent_key else None
                if parent_node is None:
                    QMessageBox.warning(self, "No Target", "Could not resolve parent node.")
                    return
                # UserRole+1 holds the real field name on UDF items; fall back to display text
                stored = sel_item.data(0, Qt.UserRole + 1)
                field_name = stored if stored else sel_item.text(0)

            ok, msg = self._insert_into_field(parent_node, field_name, new_node, node_name)
            if not ok:
                QMessageBox.warning(self, "Cannot Add Node", msg)
                return
            _xite_parent, _xite_field = parent_node, field_name

        if not self._ai_batch:
            expanded = self._capture_tree_expanded()
            self.setX3DScene(self._x3dScene)
            self._restore_tree_expanded(expanded)
            self._reveal_tree_node(new_node)
            self._add_node_to_xite(new_node, _xite_parent, _xite_field)
        else:
            # Register so _find_node_by_def can locate this node for subsequent parent lookups
            self.tree_widget.registerNode(new_node)
            def_name = getattr(new_node, "DEF", "")
            if def_name:
                self._ai_new_defs.add(def_name)
        return new_node

    def _add_node_to_xite(self, node, parent_node, field_name):
        """Incremental SAI add for a single newly-created node without clearing the scene."""
        import rawkee.io.RKx3d as _rkx
        node_type = type(node)
        type_name = node_type.NAME() if hasattr(node_type, 'NAME') else node_type.__name__

        def_ = getattr(node, 'DEF', '') or ''
        if not def_:
            def_ = f'__rk_{self._auto_def_counter}__'
            self._auto_def_counter += 1
            self._node_def_map[id(node)] = def_

        scalar_fields = {}
        if hasattr(node_type, 'FIELD_DECLARATIONS'):
            for decl in node_type.FIELD_DECLARATIONS():
                fname, _, ftype_obj, access = decl[0], decl[1], decl[2], decl[3]
                if fname in self._SKIP_FIELDS:
                    continue
                if access == _rkx.AccessType.outputOnly:
                    continue
                if ftype_obj in (_rkx.FieldType.SFNode, _rkx.FieldType.MFNode):
                    continue
                try:
                    val = getattr(node, fname)
                except Exception:
                    continue
                if val is None:
                    continue
                js_val = self._scalar_to_json(val, ftype_obj)
                if js_val is not None:
                    scalar_fields[fname] = js_val

        parent_def = None
        if parent_node is not None:
            parent_def = getattr(parent_node, 'DEF', '') or ''
            if not parent_def:
                parent_def = self._node_def_map.get(id(parent_node), '')

        cmd = (
            f'RK.addNode({json.dumps(type_name)},{json.dumps(def_)},'
            f'{json.dumps(parent_def) if parent_def else "null"},'
            f'{json.dumps(field_name)},{json.dumps(scalar_fields)});'
        )
        self.browser.page().runJavaScript(cmd)

    def _collect_defs(self, node, out=None):
        """Recursively collect all DEF values in the scenegraph as a set."""
        if out is None:
            out = set()
        if not hasattr(node, 'NAME'):
            return out
        def_ = getattr(node, 'DEF', '')
        if def_:
            out.add(def_)
        if hasattr(type(node), 'FIELD_DECLARATIONS'):
            for decl in type(node).FIELD_DECLARATIONS():
                try:
                    ftype = decl[2]()
                except Exception:
                    continue
                if ftype not in ('SFNode', 'MFNode'):
                    continue
                try:
                    val = getattr(node, decl[0], None)
                except Exception:
                    continue
                if val is None:
                    continue
                for child in (val if isinstance(val, list) else [val]):
                    self._collect_defs(child, out)
        return out

    def _next_unique_def(self, prefix):
        """Return prefix+N where N is the lowest positive integer not already used as a DEF."""
        used = set()
        if self._x3dScene is not None:
            for child in self._x3dScene.children:
                self._collect_defs(child, used)
        n = 1
        while f'{prefix}{n}' in used:
            n += 1
        return f'{prefix}{n}'

    @staticmethod
    def _best_field_for_child(parent_node, new_node):
        """Return (field_name, is_mf, err) for the most appropriate field in parent_node."""
        from rawkee.io.RKLoadSceneFromFile import RKLoadSceneFromFile
        loader = RKLoadSceneFromFile()
        cf = loader._defaultContainerField(new_node, parent_node)
        if cf:
            for decl in type(parent_node).FIELD_DECLARATIONS():
                if decl[0] == cf:
                    try:    ftype = decl[2]()
                    except Exception: ftype = ''
                    return cf, ftype == 'MFNode', None

        # Fallback: prefer 'children' MFNode, then first SFNode, then first MFNode
        first_children = first_sf = first_mf = None
        for decl in type(parent_node).FIELD_DECLARATIONS():
            fname = decl[0]
            try:    ftype = decl[2]()
            except Exception: continue
            if ftype == 'MFNode' and fname == 'children' and first_children is None:
                first_children = fname
            elif ftype == 'SFNode' and first_sf is None:
                first_sf = fname
            elif ftype == 'MFNode' and first_mf is None:
                first_mf = fname

        for chosen in (first_children, first_sf, first_mf):
            if chosen:
                for decl in type(parent_node).FIELD_DECLARATIONS():
                    if decl[0] == chosen:
                        try:    ftype = decl[2]()
                        except Exception: ftype = ''
                        return chosen, ftype == 'MFNode', None

        pn = type(parent_node).NAME() if hasattr(type(parent_node), 'NAME') else type(parent_node).__name__
        cn = type(new_node).__name__
        return None, False, f"{pn} has no SFNode or MFNode field to receive {cn}."

    @staticmethod
    def _insert_into_field(parent_node, field_name, new_node, node_name):
        """Insert new_node into parent_node.field_name; return (ok, err_msg)."""
        # Script user-defined SFNode/MFNode fields store their values in rkx.field.children
        if hasattr(type(parent_node), 'NAME') and type(parent_node).NAME() == 'Script':
            for fobj in list(getattr(parent_node, 'field', None) or []):
                if (getattr(fobj, 'name', '') == field_name
                        and getattr(fobj, 'type', '') in ('SFNode', 'MFNode')):
                    if getattr(fobj, 'accessType', '') not in ('inputOutput', 'initializeOnly'):
                        return False, (
                            f"'{field_name}' has accessType '{fobj.accessType}' "
                            f"and cannot hold an initial node value."
                        )
                    existing = list(getattr(fobj, 'children', None) or [])
                    if getattr(fobj, 'type', '') == 'MFNode':
                        fobj.children = existing + [new_node]
                        return True, None
                    # SFNode — reject if already occupied
                    if existing:
                        occ     = existing[0]
                        occ_t   = type(occ).NAME() if hasattr(type(occ), 'NAME') else type(occ).__name__
                        occ_def = getattr(occ, 'DEF', '')
                        occ_ref = f"{occ_t} DEF='{occ_def}'" if occ_def else occ_t
                        return False, f"'{field_name}' is already occupied by {occ_ref}."
                    fobj.children = [new_node]
                    return True, None
        # Block inputOnly/outputOnly standard fields before attempting setattr
        if hasattr(type(parent_node), 'FIELD_DECLARATIONS'):
            for decl in type(parent_node).FIELD_DECLARATIONS():
                if decl[0] == field_name:
                    try:
                        access = decl[3]()
                    except Exception:
                        access = ''
                    if access in ('inputOnly', 'outputOnly'):
                        return False, (
                            f"'{field_name}' has accessType '{access}' "
                            f"and cannot hold an initial node value."
                        )
                    break
        try:
            current = getattr(parent_node, field_name)
        except AttributeError:
            pn = type(parent_node).NAME() if hasattr(type(parent_node), 'NAME') else type(parent_node).__name__
            return False, f"'{field_name}' is not a field of {pn}."

        if isinstance(current, list):
            # MFNode — append via setter to trigger any type validation
            try:
                setattr(parent_node, field_name, list(current) + [new_node])
            except Exception as e:
                return False, f"'{node_name}' is not allowed in '{field_name}':\n{e}"
            return True, None
        else:
            # SFNode — reject if already occupied
            if current is not None:
                pn      = type(parent_node).NAME() if hasattr(type(parent_node), 'NAME') else type(parent_node).__name__
                occ     = type(current).NAME() if hasattr(type(current), 'NAME') else type(current).__name__
                occ_def = getattr(current, 'DEF', '')
                occ_ref = f"{occ} DEF='{occ_def}'" if occ_def else occ
                parent_def = getattr(parent_node, 'DEF', '')
                parent_ref = f"{pn} DEF='{parent_def}'" if parent_def else pn
                return False, (f"'{field_name}' of {parent_ref} is already occupied by {occ_ref}. "
                               f"Do not create a new {occ} — use parent_def='{occ_def}' to add children to it.")
            try:
                setattr(parent_node, field_name, new_node)
            except Exception as e:
                return False, f"'{node_name}' is not allowed in '{field_name}':\n{e}"
            return True, None

    def _reveal_tree_node(self, node):
        """Expand ancestors of and scroll to the tree item that represents *node*."""
        key = str(id(node))
        def search(item):
            if item.data(0, Qt.UserRole) == key:
                return item
            for i in range(item.childCount()):
                result = search(item.child(i))
                if result:
                    return result
            return None
        target = None
        for i in range(self.tree_widget.topLevelItemCount()):
            target = search(self.tree_widget.topLevelItem(i))
            if target:
                break
        if target is None:
            return
        p = target.parent()
        while p:
            p.setExpanded(True)
            p = p.parent()
        self.tree_widget.scrollToItem(target)
        self.tree_widget.setCurrentItem(target)

    def _capture_tree_expanded(self):
        """Return a set of label-path tuples for every currently expanded tree item."""
        expanded = set()
        def visit(item, path):
            if item.isExpanded():
                expanded.add(path)
            for i in range(item.childCount()):
                child = item.child(i)
                visit(child, path + (child.text(0),))
        for i in range(self.tree_widget.topLevelItemCount()):
            top = self.tree_widget.topLevelItem(i)
            visit(top, (top.text(0),))
        return expanded

    def _restore_tree_expanded(self, expanded):
        """Re-expand items whose label-path tuple appears in *expanded*."""
        def visit(item, path):
            if path in expanded:
                item.setExpanded(True)
            for i in range(item.childCount()):
                child = item.child(i)
                visit(child, path + (child.text(0),))
        for i in range(self.tree_widget.topLevelItemCount()):
            top = self.tree_widget.topLevelItem(i)
            visit(top, (top.text(0),))

    # ── SAI scenegraph sync ───────────────────────────────────────────────────

    _BINDABLE_TYPES = frozenset({
        'Viewpoint', 'OrthoViewpoint', 'GeoViewpoint',
        'NavigationInfo', 'Background', 'TextureBackground', 'Fog',
    })

    def _bind_selected_node(self, node):
        type_name = type(node).NAME() if hasattr(type(node), 'NAME') else ''
        if type_name not in self._BINDABLE_TYPES:
            return
        def_ = getattr(node, 'DEF', '') or self._node_def_map.get(id(node), '')
        if not def_:
            return
        self.browser.page().runJavaScript(
            f'(function(){{var n=RK._node({json.dumps(def_)});if(n)n.set_bind=true;}})();'
        )

    _VIEWPOINT_TYPES = frozenset({'Viewpoint', 'OrthoViewpoint', 'GeoViewpoint'})

    def _find_first_node_def(self, scene_node, type_names):
        """Return the DEF of the first root node whose type name is in type_names, or None."""
        for child in (getattr(scene_node, 'children', None) or []):
            if child is None:
                continue
            if type(child).__name__ in type_names:
                def_ = getattr(child, 'DEF', '') or ''
                if def_:
                    return def_
        return None

    _SKIP_FIELDS = frozenset({'DEF', 'USE', 'IS', 'class_', 'id_', 'style_',
                              'metadata', 'bboxCenter', 'bboxSize', 'bboxDisplay'})

    def _sync_xite_via_sai(self):
        """Push the full Python X3D scenegraph into X_ITE via RK SAI calls."""
        if self._x3dObj is None or self._ai_batch:
            return
        scene = getattr(self._x3dObj, 'Scene', None)
        if scene is None:
            return
        # Script nodes with UDFs must be loaded from file; SAI cannot declare fields
        if self._scene_has_script_udfs(scene):
            self._sync_xite_via_file()
            return
        self._auto_def_counter = 0
        self._node_def_map.clear()
        self.field_editor.set_node_def_map(self._node_def_map)
        try:
            cmds = ['RK.clearScene();']
            deferred_uses = []  # [(use_def, parent_def, field_name)] — flushed after all addNode
            self._collect_sai_cmds(scene.children, None, 'children', cmds, deferred_uses)
            # Emit USE references now that every DEF node is registered
            for use_def, par_def, fld in deferred_uses:
                if par_def:
                    cmds.append(
                        f'(function(){{var p=RK._node({json.dumps(par_def)});'
                        f'var u=RK._node({json.dumps(use_def)});'
                        f'if(p&&u){{try{{p[{json.dumps(fld)}].push(u);}}catch(e){{p[{json.dumps(fld)}]=u;}}}};}})();'
                    )
                else:
                    cmds.append(
                        f'(function(){{var u=RK._node({json.dumps(use_def)});'
                        f'if(u){{document.querySelector("x3d-canvas").browser.currentScene.rootNodes.push(u);}}}})();'
                    )
            # Add ROUTEs last (they reference DEF names; all nodes are registered by now)
            for node in scene.children:
                self._collect_routes(node, cmds)
            self.console_widget.appendPlainText(f'[SAI] {len(cmds)} commands generated')
            js = '\n'.join(cmds)
            self.browser.page().runJavaScript(js)
        except Exception as e:
            self.console_widget.appendPlainText(f'[ERROR] SAI sync: {e}')

    @staticmethod
    def _scene_has_script_udfs(scene):
        """Return True if any Script node in the scene has user-defined fields."""
        def _walk(nodes):
            for n in (nodes or []):
                if not hasattr(type(n), 'NAME'):
                    continue
                if type(n).NAME() == 'Script' and list(getattr(n, 'field', None) or []):
                    return True
                if hasattr(type(n), 'FIELD_DECLARATIONS'):
                    for decl in type(n).FIELD_DECLARATIONS():
                        try:
                            if decl[2]() not in ('SFNode', 'MFNode'):
                                continue
                            val = getattr(n, decl[0], None)
                            children = val if isinstance(val, list) else ([val] if val else [])
                            if _walk(children):
                                return True
                        except Exception:
                            pass
            return False
        return _walk(getattr(scene, 'children', []))

    def _sync_xite_via_file(self):
        """Sync X_ITE by writing the current scene to a temp file and loading via URL."""
        import io, time as _time
        from rawkee.io.RKSceneTraversal import RKSceneTraversal as _Trv
        buf = io.StringIO()
        trv = _Trv()
        trv.collectProfileFromScene(self._x3dObj)
        trv.startExport(self._x3dObj, buf, 'x3d')
        xml = buf.getvalue()
        if not xml:
            return
        temp_path = os.path.normpath(os.path.join(self.basePath, '_rk_live.x3d'))
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(xml)
        url = self._local_url(temp_path) + f'?t={int(_time.time() * 1000)}'
        js = (
            f'(async function(){{'  
            f'  try {{'  
            f'    var b=document.querySelector("x3d-canvas").browser;'  
            f'    await b.loadURL(new X3D.MFString({json.dumps(url)}));'  
            f'  }} catch(e){{console.log("RK loadURL: "+e);}}'  
            f'}})();'
        )
        self.browser.page().runJavaScript(js)
        self._node_def_map.clear()
        self._auto_def_counter = 0
        QTimer.singleShot(600, self._bind_first_nodes)

    def _collect_sai_cmds(self, nodes, parent_def, field_name, cmds, deferred_uses):
        """Recursively emit RK.addNode() calls for a list of X3D Python nodes."""
        import rawkee.io.RKx3d as _rkx
        for node in (nodes or []):
            if node is None:
                continue
            node_type = type(node)
            type_name = node_type.NAME() if hasattr(node_type, 'NAME') else node_type.__name__
            if type_name in ('ROUTE', 'Scene', 'X3D'):
                continue
            # rkx.field is a statement object; X_ITE SAI has no addField API
            if type_name == 'field':
                continue
            def_ = getattr(node, 'DEF', '') or ''
            use_ = getattr(node, 'USE', '') or ''
            # Nodes without a DEF get a synthetic one so field edits can address them.
            if not def_ and not use_:
                def_ = f'__rk_{self._auto_def_counter}__'
                self._auto_def_counter += 1
                self._node_def_map[id(node)] = def_
            if use_:
                # Defer USE references until after all addNode calls so the DEF is guaranteed registered.
                deferred_uses.append((use_, parent_def, field_name))
                continue
            # Collect non-node scalar fields
            scalar_fields = {}
            child_fields  = []  # [(field_name, [child_nodes])]  for SFNode/MFNode
            if hasattr(node_type, 'FIELD_DECLARATIONS'):
                for decl in node_type.FIELD_DECLARATIONS():
                    fname    = decl[0]
                    ftype_obj = decl[2]
                    access   = decl[3]
                    if fname in self._SKIP_FIELDS:
                        continue
                    if access == _rkx.AccessType.outputOnly:
                        continue
                    if ftype_obj in (_rkx.FieldType.SFNode, _rkx.FieldType.MFNode):
                        try:
                            val = getattr(node, fname)
                        except Exception:
                            continue
                        if val is None:
                            continue
                        children = val if isinstance(val, list) else [val]
                        children = [c for c in children if c is not None]
                        if children:
                            child_fields.append((fname, children))
                        continue
                    # Scalar field — convert to JSON-safe value
                    try:
                        val = getattr(node, fname)
                    except Exception:
                        continue
                    if val is None:
                        continue
                    js_val = self._scalar_to_json(val, ftype_obj)
                    if js_val is not None:
                        scalar_fields[fname] = js_val
            def_js      = json.dumps(def_) if def_ else 'null'
            parent_js   = json.dumps(parent_def) if parent_def else 'null'
            field_js    = json.dumps(field_name)
            fields_json = json.dumps(scalar_fields)
            cmds.append(
                f'RK.addNode({json.dumps(type_name)},{def_js},{parent_js},{field_js},{fields_json});'
            )
            # Recurse into child node fields (skip Script.field — SAI can't declare fields)
            for cf_name, cf_nodes in child_fields:
                if type_name == 'Script' and cf_name == 'field':
                    continue
                self._collect_sai_cmds(cf_nodes, def_ or None, cf_name, cmds, deferred_uses)

    def _collect_routes(self, node, cmds):
        """Emit RK.addRoute() for any ROUTE objects found in this node's children."""
        import rawkee.io.RKx3d as _rkx
        node_type = type(node)
        if node_type.NAME() == 'ROUTE' if hasattr(node_type, 'NAME') else False:
            fn = getattr(node, 'fromNode',  '')
            ff = getattr(node, 'fromField', '')
            tn = getattr(node, 'toNode',    '')
            tf = getattr(node, 'toField',   '')
            if fn and ff and tn and tf:
                cmds.append(
                    f'RK.addRoute({json.dumps(fn)},{json.dumps(ff)},{json.dumps(tn)},{json.dumps(tf)});'
                )
            return
        if hasattr(node_type, 'FIELD_DECLARATIONS'):
            for decl in node_type.FIELD_DECLARATIONS():
                if decl[2] not in (_rkx.FieldType.SFNode, _rkx.FieldType.MFNode):
                    continue
                try:
                    val = getattr(node, decl[0])
                except Exception:
                    continue
                children = val if isinstance(val, list) else ([val] if val else [])
                for child in children:
                    if child is not None:
                        self._collect_routes(child, cmds)

    @staticmethod
    def _scalar_to_json(val, ftype_obj):
        """Convert a Python field value to a JSON-serialisable form for RK.addNode()."""
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, str):
            return val
        if isinstance(val, tuple):
            return list(val)
        if isinstance(val, list):
            if not val:
                return []
            if isinstance(val[0], tuple):
                # Flatten MF tuple arrays — X_ITE expects flat [x,y,z,x,y,z,...]
                return [x for t in val for x in t]
            return list(val)
        return None

    def stopWebserver(self):
        if self.httpd:
            print("Shutting down server...")
            # .shutdown() stops the serve_forever() loop
            self.httpd.shutdown() 
            # .server_close() closes the socket properly
            self.httpd.server_close()

    def getDataFromMaya(self, mayaData, selected_only=False):
        # Placeholder for future DCC-host integration.
        return None

    def sendDataToMaya(self, x3dData, selected_only=False):
        # Placeholder for future DCC-host integration.
        return None

    def getDataFromBlender(self, blenderData, selected_only=False):
        # Placeholder for future DCC-host integration.
        return None

    def sendDataToBlender(self, x3dData, selected_only=False):
        # Placeholder for future DCC-host integration.
        return None


class RKCustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._console = None

    def set_console(self, widget):
        self._console = widget

    def _log(self, text):
        print(text)
        if self._console is not None:
            self._console.appendPlainText(text)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceId):
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel:
            level_str = 'WARNING'
        elif level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            level_str = 'ERROR'
        else:
            level_str = 'INFO'
        # Script node Browser.println() arrives pre-tagged; show cleanly
        if message.startswith('[Script] '):
            self._log('[Script] ' + message[len('[Script] '):])
        else:
            self._log(f'[{level_str}] {sourceId}:{lineNumber}: {message}')


class RKBackgroundHost:
    def __init__(self, directory=".", port=8000):
        self.port = port
        self.directory = directory
        self.handler = partial(http.server.SimpleHTTPRequestHandler, directory=directory)
        # allow_reuse_address must be set before bind; subclass to ensure it
        class _Server(http.server.HTTPServer):
            allow_reuse_address = True
        self.httpd = _Server(("", port), self.handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def start(self):
        self.thread.start()
        print(f"Server started at http://localhost:{self.port} (Root: {self.directory})")

    def stop(self):
        # Shutdown blocks until serve_forever exits; run it off the main thread
        def _do_stop():
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass
        threading.Thread(target=_do_stop, daemon=True).start()
        print("Server shutting down.")    


#####################################################################
# Implemented by following the NodeEditor Tutorial of BlenderFreak
# https://www.blenderfreak.com/tutorials/node-editor-tutorial-series/
#####################################################################
class RKCustomNodeEditor(QWidget):
    
    def __init__(self, tree_widget=None, parent=None):
        super().__init__(parent)
        self._tree_widget = tree_widget
        
        #self.basePath = parent.basePath
        #self.stylesheet_filename = self.basePath + "/auxilary/rkNodeStyle.qss"
        #self.loadStyleSheet(self.stylesheet_filename)
        
        self.initUI()
        
    def initUI(self):
        self.layout = QVBoxLayout()
        self.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        self.scene = RKXScene()

        # Use the drop-enabled view if a tree widget was provided
        if self._tree_widget is not None:
            self.view = RKNodeEditorDropView(self.scene.grScene, self._tree_widget, self)
        else:
            self.view = RKGraphicsView(self.scene.grScene, self)
        self.layout.addWidget(self.view)

    def set_x3d_scene(self, x3d_scene):
        self.scene.set_x3d_scene(x3d_scene)

    def clearGraph(self):
        self.scene.clear_graph()

    def addNodeFromX3D(self, x3d_node, scene_pos):
        """Create an RKXNode in the editor canvas from a dropped rkx node object."""
        # USE nodes are just references — resolve to the actual DEF node
        use_val = getattr(x3d_node, 'USE', '')
        if use_val:
            node_type = type(x3d_node)
            for candidate in self._tree_widget._node_registry.values():
                if type(candidate) == node_type and getattr(candidate, 'DEF', '') == use_val:
                    x3d_node = candidate
                    break

        # Prevent duplicate: same DEF already in graph
        def_val = getattr(x3d_node, 'DEF', '')
        if def_val:
            for existing in self.scene.eNodes:
                if getattr(getattr(existing, 'x3d_node', None), 'DEF', '') == def_val:
                    return

        node_type = type(x3d_node).NAME()
        def_name  = getattr(x3d_node, 'DEF', '')
        use_name  = getattr(x3d_node, 'USE', '')
        title = use_name if use_name else def_name

        _NO_ROUTE_NAMES = frozenset({'DEF', 'USE', 'IS', 'class_', 'id_', 'style_'})
        inputs  = []
        outputs = []
        if hasattr(type(x3d_node), 'FIELD_DECLARATIONS'):
            for decl in type(x3d_node).FIELD_DECLARATIONS():
                field_name = decl[0]
                try:    field_type = decl[2]()
                except Exception: field_type = ''
                try:    access_str = decl[3]()
                except Exception: access_str = ''
                if field_name in _NO_ROUTE_NAMES:
                    continue
                if access_str in ('inputOnly', 'inputOutput'):
                    inputs.append((field_name, field_type))
                if access_str in ('outputOnly', 'inputOutput'):
                    outputs.append((field_name, field_type))

        # Merge spec event fields absent from FIELD_DECLARATIONS
        existing_in  = {fn for fn, _ in inputs}
        existing_out = {fn for fn, _ in outputs}
        for (fname, ftype, access) in _EXTRA_EVENT_FIELDS.get(node_type, []):
            if access == 'inputOnly' and fname not in existing_in:
                inputs.append((fname, ftype))
            elif access == 'outputOnly' and fname not in existing_out:
                outputs.append((fname, ftype))

        # User-defined fields on Script nodes
        if node_type == 'Script':
            for udf in list(getattr(x3d_node, 'field', None) or []):
                fn = getattr(udf, 'name', '') or ''
                ft = getattr(udf, 'type', '') or ''
                ac = getattr(udf, 'accessType', '') or ''
                if not fn:
                    continue
                if ac in ('inputOnly', 'inputOutput'):
                    inputs.append((fn, ft))
                if ac in ('outputOnly', 'inputOutput'):
                    outputs.append((fn, ft))

        new_node = RKXNode(self.scene, title, inputs=inputs, outputs=outputs, x3d_node=x3d_node, node_type=node_type)
        new_node.setPos(scene_pos.x(), scene_pos.y())
        self._sync_routes_to_edges()

    def _sync_routes_to_edges(self):
        if self.scene._x3d_scene is None:
            return

        def base(name):
            if name.endswith('_changed'): return name[:-8]
            if name.startswith('set_'):   return name[4:]
            return name

        def_map = {getattr(n.x3d_node, 'DEF', ''): n
                   for n in self.scene.eNodes
                   if getattr(n, 'x3d_node', None) and getattr(n.x3d_node, 'DEF', '')}
        existing_pairs = {(id(e.start_socket), id(e.end_socket))
                          for e in self.scene.eEdges if e.start_socket and e.end_socket}
        for child in self.scene._x3d_scene.children:
            if not hasattr(child, 'fromNode'):
                continue
            from_enode = def_map.get(child.fromNode)
            to_enode   = def_map.get(child.toNode)
            if from_enode is None or to_enode is None:
                continue
            rf = base(child.fromField)
            rt = base(child.toField)
            start_sock = next((from_enode.outputs[i]
                               for i, (fn, _) in enumerate(from_enode.output_fields)
                               if base(fn) == rf and i < len(from_enode.outputs)), None)
            end_sock   = next((to_enode.inputs[i]
                               for i, (fn, _) in enumerate(to_enode.input_fields)
                               if base(fn) == rt and i < len(to_enode.inputs)), None)

            # Field not in FIELD_DECLARATIONS (pure event field) — create a socket on the fly
            if start_sock is None:
                start_sock = self._add_dynamic_socket(from_enode, child.fromField, is_output=True)
            if end_sock is None:
                end_sock = self._add_dynamic_socket(to_enode, child.toField, is_output=False)

            if start_sock is None or end_sock is None:
                continue
            pair = (id(start_sock), id(end_sock))
            if pair in existing_pairs:
                continue
            from rawkee.editor.RKXEdge import RKXEdge
            RKXEdge(self.scene, start_sock, end_sock)
            existing_pairs.add(pair)

    def refreshScriptNodeSockets(self, x3d_node):
        """Rebuild all sockets for a Script node after user-defined fields changed."""
        from rawkee.editor.RKXSocket import RKXSocket, LEFT_BOTTOM, RIGHT_TOP

        target = None
        for en in self.scene.eNodes:
            if en.x3d_node is x3d_node:
                target = en
                break
        if target is None:
            return

        # Collect all still-valid field names to prune orphaned routes
        valid_names = set()
        if hasattr(type(x3d_node), 'FIELD_DECLARATIONS'):
            for decl in type(x3d_node).FIELD_DECLARATIONS():
                valid_names.add(decl[0])
        for udf in list(getattr(x3d_node, 'field', None) or []):
            fn = getattr(udf, 'name', '') or ''
            if fn:
                valid_names.add(fn)

        # Remove X3D routes that reference now-missing fields on this Script
        script_def = getattr(x3d_node, 'DEF', '') or ''
        if script_def and self.scene._x3d_scene is not None:
            dead = [
                c for c in self.scene._x3d_scene.children
                if hasattr(c, 'fromNode') and (
                    (c.fromNode == script_def and c.fromField not in valid_names) or
                    (c.toNode   == script_def and c.toField   not in valid_names)
                )
            ]
            for r in dead:
                self.scene._x3d_scene.children.remove(r)
                self.scene._run_sai(
                    f"(function(){{var b=document.querySelector('x3d-canvas').browser;"
                    f"var s=b.currentScene;"
                    f"var fn=s.getNamedNode({r.fromNode!r});"
                    f"var tn=s.getNamedNode({r.toNode!r});"
                    f"b.endUpdate();"
                    f"if(fn&&tn)b.deleteRoute(fn,{r.fromField!r},tn,{r.toField!r});"
                    f"b.beginUpdate();}})()")

        # Remove graph edges touching this node
        for edge in list(self.scene.eEdges):
            ss, es = edge.start_socket, edge.end_socket
            if (ss and ss.eNode is target) or (es and es.eNode is target):
                if edge.grEdge is not None:
                    self.scene.grScene.removeItem(edge.grEdge)
                self.scene.eEdges.remove(edge)

        # Remove existing socket graphics items
        for sock in target.inputs + target.outputs:
            if sock.grSocket is not None:
                self.scene.grScene.removeItem(sock.grSocket)

        # Rebuild field lists from scratch
        target.input_fields.clear()
        target.output_fields.clear()
        target.inputs.clear()
        target.outputs.clear()

        _NO = frozenset({'DEF', 'USE', 'IS', 'class_', 'id_', 'style_'})
        if hasattr(type(x3d_node), 'FIELD_DECLARATIONS'):
            for decl in type(x3d_node).FIELD_DECLARATIONS():
                fn = decl[0]
                try:  ft = decl[2]()
                except Exception:  ft = ''
                try:  ac = decl[3]()
                except Exception:  ac = ''
                if fn in _NO:
                    continue
                if ac in ('inputOnly', 'inputOutput'):
                    target.input_fields.append((fn, ft))
                if ac in ('outputOnly', 'inputOutput'):
                    target.output_fields.append((fn, ft))

        node_type = type(x3d_node).NAME()
        for udf in list(getattr(x3d_node, 'field', None) or []):
            fn = getattr(udf, 'name', '') or ''
            ft = getattr(udf, 'type', '') or ''
            ac = getattr(udf, 'accessType', '') or ''
            if not fn:
                continue
            if ac in ('inputOnly', 'inputOutput'):
                target.input_fields.append((fn, ft))
            if ac in ('outputOnly', 'inputOutput'):
                target.output_fields.append((fn, ft))

        existing_in  = {fn for fn, _ in target.input_fields}
        existing_out = {fn for fn, _ in target.output_fields}
        for (fn, ft, ac) in _EXTRA_EVENT_FIELDS.get(node_type, []):
            if ac == 'inputOnly' and fn not in existing_in:
                target.input_fields.append((fn, ft))
            elif ac == 'outputOnly' and fn not in existing_out:
                target.output_fields.append((fn, ft))

        # Resize node to fit new socket count
        n = max(len(target.input_fields), len(target.output_fields), 1)
        top_start = int(target.grNode.title_height * target.grNode._padding) + target.grNode.edge_size
        bot_start = target.grNode.edge_size + int(target.grNode._padding)
        new_h = max(top_start + (n - 1) * target.socket_spacing + bot_start, 100)
        target.grNode.prepareGeometryChange()
        target.grNode.height = new_h
        target.grNode.width  = target._min_width_for_fields()
        target.grNode.initContent()

        for i, (fn, ft) in enumerate(target.input_fields):
            s = RKXSocket(eNode=target, index=i, position=LEFT_BOTTOM,
                          isOutput=False, field_type=ft, field_name=fn)
            target.inputs.append(s)

        for i, (fn, ft) in enumerate(target.output_fields):
            s = RKXSocket(eNode=target, index=i, position=RIGHT_TOP,
                          isOutput=True, field_type=ft, field_name=fn)
            target.outputs.append(s)

        target.grNode.update()
        self._sync_routes_to_edges()

    def _add_dynamic_socket(self, enode, field_name, is_output):
        """Create a socket for a field not present in FIELD_DECLARATIONS (pure event field)."""
        from rawkee.editor.RKXSocket import RKXSocket, LEFT_BOTTOM, RIGHT_TOP
        if is_output:
            idx = len(enode.outputs)
            enode.output_fields.append((field_name, ''))
            enode._resize_for_sockets()
            sock = RKXSocket(eNode=enode, index=idx, position=RIGHT_TOP,
                             isOutput=True, field_name=field_name)
            enode.outputs.append(sock)
        else:
            idx = len(enode.inputs)
            enode.input_fields.append((field_name, ''))
            enode._resize_for_sockets()
            sock = RKXSocket(eNode=enode, index=idx, position=LEFT_BOTTOM,
                             isOutput=False, field_name=field_name)
            enode.inputs.append(sock)
        return sock

    def centerViewOn(self, qpoint=QPointF(0,0)):
        self.view.centerOn(qpoint)
        
        
    def addDebugContent(self):
        greenBrush = QBrush(Qt.green)
        outlinePen = QPen(Qt.black)
        outlinePen.setWidth(2)
        
        myRect = self.grScene.addRect(-100, -100, 80, 100, outlinePen, greenBrush)
        myRect.setFlag(rkgItem.ItemIsMovable)
        
        myText = self.grScene.addText("This is my Text!", QFont("Broadway"))
        myText.setFlag(rkgItem.ItemIsSelectable)
        myText.setFlag(rkgItem.ItemIsMovable)
        myText.setDefaultTextColor(QColor.fromRgbF(1.0, 1.0, 1.0))
        
        widget1 = QPushButton("Don't Push!")
        proxy1  = self.grScene.addWidget(widget1)
        proxy1.setFlag(rkgItem.ItemIsMovable)
        proxy1.setPos(0, 30)
        
        widget2 = QTextEdit()
        proxy2  = self.grScene.addWidget(widget2)
        proxy2.setFlag(rkgItem.ItemIsSelectable)
        proxy2.setPos(0, 60)
        
        myLine = self.grScene.addLine(-200, -200, 400, -100, outlinePen)
        myLine.setFlag(rkgItem.ItemIsSelectable)
        myLine.setFlag(rkgItem.ItemIsMovable)
        
    #def loadStyleSheet(self, filename):
    #    print('STYLE loading', filename)
    #    
    #    file = QFile(filename)
    #    file.open(QFile.ReadOnly | QFile.Text)
    #    stylesheet = file.readAll()
    #    
    #    #self.setStyleSheet(str(stylesheet, encoding='utf-8'))
    #    QApplication.instance().setStyleSheet(str(stylesheet, encoding='utf-8'))
        

'''
if __name__ == "__main__":

    sceneEditorControlName = RKSceneEditor.scene_editor_control_name()

    if cmds.workspaceControl(sceneEditorControlName, exists=True):
        #Must Close before Delete
        cmds.workspaceControl(sceneEditorControlName, e=True, close=True)
        cmds.deleteUI(sceneEditorControlName)
    
    rkSEditor = RKSceneEditor()
    rkSEditor.show(dockable=True, uiScript=RKSceneEditor.workspace_ui_script())
'''
