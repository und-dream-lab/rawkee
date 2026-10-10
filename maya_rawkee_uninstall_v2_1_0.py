"""
RawKee Maya Plugin Uninstaller v2.1.0
--------------------------------------
Drag and drop this file into the Maya viewport to uninstall.

The script will:
  1. Unload the RawKee plugin if it is currently loaded (stops if it can't).
  2. Delete <modules>/RawKee.mod and the <modules>/RawKee folder created by
     maya_rawkee_install_v2_1_0.py.

The cloned repo is never touched. Restart Maya afterwards.
"""

import os
import shutil
import sys

_INSTALL_DIR_NAME = "RawKee"
_MOD_FILE_NAME    = "RawKee.mod"
_PLUGIN_FILE      = "Maya_RawKee_Python_X3D.py"


def _get_modules_dir():
    """Return Maya's user modules directory (same lookup as the installer)."""
    try:
        import maya.cmds as cmds
        maya_app_dir = cmds.internalVar(userAppDir=True).rstrip("/\\")
    except ImportError:
        if sys.platform == "win32":
            base = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            maya_app_dir = os.path.join(base, "Documents", "maya")
        elif sys.platform == "darwin":
            maya_app_dir = os.path.expanduser("~/Library/Preferences/Autodesk/maya")
        else:
            maya_app_dir = os.path.expanduser("~/maya")

    return os.path.join(maya_app_dir, "modules")


def _notify(title, message):
    """Show a Maya confirm dialog when inside Maya, otherwise just print."""
    print(message)
    try:
        import maya.cmds as cmds
        cmds.confirmDialog(title=title, message=message, button=["OK"])
    except Exception:
        pass


def _confirm(title, message):
    """Ask Yes/No inside Maya; outside Maya there is no UI, so proceed."""
    try:
        import maya.cmds as cmds
    except ImportError:
        return True
    answer = cmds.confirmDialog(
        title=title, message=message, button=["Yes", "No"],
        defaultButton="No", cancelButton="No", dismissString="No",
    )
    return answer == "Yes"


def _unload_plugin():
    """Unload RawKee if loaded (from any location); return an error string or ''."""
    try:
        import maya.cmds as cmds
    except ImportError:
        return ""

    for loaded in cmds.pluginInfo(query=True, listPlugins=True) or []:
        try:
            path = cmds.pluginInfo(loaded, query=True, path=True) or ""
        except RuntimeError:
            continue
        if os.path.basename(path).lower() == _PLUGIN_FILE.lower():
            try:
                cmds.flushUndo()
                cmds.unloadPlugin(loaded, force=True)
            except RuntimeError as exc:
                return "Could not unload plugin '{}': {}".format(loaded, exc)
    return ""


def uninstall():
    modules_dir = _get_modules_dir()
    install_dir = os.path.join(modules_dir, _INSTALL_DIR_NAME)
    mod_path    = os.path.join(modules_dir, _MOD_FILE_NAME)

    targets = [p for p in (mod_path, install_dir) if os.path.exists(p)]
    if not targets:
        _notify("RawKee Uninstaller", "RawKee is not installed in:\n  {}".format(modules_dir))
        return

    if not _confirm(
        "RawKee Uninstaller",
        "Delete the following?\n\n  {}".format("\n  ".join(targets)),
    ):
        return

    unload_error = _unload_plugin()
    if unload_error:
        _notify(
            "RawKee Uninstaller",
            unload_error + "\n\nNothing was deleted. Unload RawKee in the Plug-in Manager "
            "(or restart Maya) and run the uninstaller again.",
        )
        return

    problems = ""

    removed = []
    for path in targets:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            removed.append(path)
        except OSError as exc:
            problems += "Could not delete {}: {}\n".format(path, exc)

    message = "RawKee uninstall {}.\n\n".format("finished with problems" if problems else "complete")
    if removed:
        message += "Removed:\n  {}\n\n".format("\n  ".join(removed))
    if problems:
        message += problems + "\nRestart Maya and run the uninstaller again.\n\n"
    message += "Restart Maya to finish."
    _notify("RawKee Uninstaller", message)


def onMayaDroppedPythonFile(*args):
    """Entry point Maya calls when this file is dropped into the viewport."""
    uninstall()


if __name__ == "__main__":
    uninstall()
