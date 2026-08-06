from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from rawkee.editor.RKSceneEditor import RKSceneEditor


class RKSceneEditorMaya(MayaQWidgetDockableMixin, RKSceneEditor):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    @classmethod
    def workspace_ui_script(cls):
        return (
            "from rawkee4maya.maya.RKSceneEditorMaya import RKSceneEditorMaya\n"
            "rkSEWidget = RKSceneEditorMaya()\n"
            "rkSEWidget.show(dockable=True)"
        )
