"""
RawKee Blender Addon Uninstaller
---------------------------------
Open this file in Blender's Text Editor (Text > Open) and click
'Run Script' to uninstall the RawKee addon.

The script will:
  1. Disable the addon and save user preferences.
  2. Delete the 'rawkee' and 'rawkee4blender' packages from Blender's user
     modules directory.
  3. Delete Blender_RawKee_Python_X3D.py from Blender's user addons directory.
  4. Drop RawKee modules from the running session so a reinstall imports
     fresh copies.

The cloned repo and pip-installed dependencies are left untouched.
Restart Blender afterwards.
"""

import bpy
import os
import shutil
import sys

_ADDON_MODULE   = "Blender_RawKee_Python_X3D"
_PACKAGES       = ["rawkee", "rawkee4blender"]
_MODULE_PREFIXES = tuple(_PACKAGES) + (_ADDON_MODULE,)


def _show_result(title, lines):
    """Print a summary to the console and show a Blender popup."""
    separator = "=" * 60
    print(f"\n{separator}\n{title}\n{separator}")
    for line in lines:
        print(line)
    print(separator + "\n")

    def draw(self, _context):
        for line in lines:
            self.layout.label(text=line)

    bpy.context.window_manager.popup_menu(draw, title=title, icon="INFO")


def _disable_addon():
    try:
        bpy.ops.preferences.addon_disable(module=_ADDON_MODULE)
        bpy.ops.wm.save_userpref()
        return f"Addon '{_ADDON_MODULE}' disabled and preferences saved."
    except Exception as exc:
        return f"Could not disable addon: {exc}"


def _remove(path, removed, problems):
    if not os.path.exists(path):
        return
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        removed.append(path)
    except OSError as exc:
        problems.append(f"Could not delete {path}: {exc}")


def uninstall():
    scripts_root = bpy.utils.script_path_user()
    modules_dir  = os.path.join(scripts_root, "modules")
    addons_dir   = os.path.join(scripts_root, "addons")

    targets = [os.path.join(modules_dir, pkg) for pkg in _PACKAGES]
    targets.append(os.path.join(addons_dir, _ADDON_MODULE + ".py"))

    if not any(os.path.exists(t) for t in targets):
        _show_result(
            "RawKee Uninstall",
            ["RawKee is not installed in:", f"  {scripts_root}"],
        )
        return

    # Disable first so the addon's unregister() runs before its files go away.
    status_msg = _disable_addon()

    for name in [m for m in sys.modules if m == _ADDON_MODULE or m.split(".")[0] in _MODULE_PREFIXES]:
        del sys.modules[name]

    removed, problems = [], []
    for path in targets:
        _remove(path, removed, problems)

    lines = [status_msg, ""]
    if removed:
        lines += ["Removed:"] + [f"  {p}" for p in removed] + [""]
    if problems:
        lines += problems + ["", "Restart Blender and run the uninstaller again.", ""]
    lines.append("Please restart Blender to finish.")
    _show_result(
        "RawKee Uninstall — " + ("Finished with problems" if problems else "Done"),
        lines,
    )


uninstall()
