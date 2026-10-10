"""
RawKee Maya Plugin Installer v2.1.0
------------------------------------
Drag and drop this file into the Maya viewport to install.

The script will:
  1. Detect the repo root from this file's location.
  2. Find Maya's user modules directory for the current OS.
  3. Copy the plugin files into <modules>/RawKee (replacing any previous copy).
  4. Write a RawKee.mod file in <modules> pointing at that folder.

The repo itself is left untouched, so it can be moved or deleted after installing.
Run maya_rawkee_uninstall_v2_1_0.py to remove the plugin.

No manual path editing required. Works on Windows, macOS, and Linux.
Restart Maya after running to load the plugin via the Plugin Manager.
"""

import os
import shutil
import sys

# Folder created inside Maya's user modules directory.
_INSTALL_DIR_NAME = "RawKee"

# Files and folders copied from the repo root into the install folder.
_PAYLOAD = [
    "rawkee",
    "rawkee4maya",
    "LICENSE",
    "Maya_RawKee_Python_X3D.py",
    "README.md",
]


def _get_repo_root():
    """Return the absolute path to the repo root (same folder as this script)."""
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # __file__ is not defined in some Maya drag-and-drop contexts.
        # Fall back to the current working directory as a best effort.
        return os.path.abspath(os.getcwd())


def _get_modules_dir():
    """
    Return the path to Maya's user modules directory.
    Uses Maya's own API when available (most reliable cross-platform method).
    Falls back to well-known OS-specific paths when run outside Maya.
    """
    try:
        import maya.cmds as cmds
        # internalVar(userAppDir=True) returns the Maya user directory
        # e.g. ~/maya/ on Linux, ~/Library/Preferences/Autodesk/maya/ on macOS,
        #      %USERPROFILE%\Documents\maya\ on Windows.
        maya_app_dir = cmds.internalVar(userAppDir=True).rstrip("/\\")
    except ImportError:
        platform = sys.platform
        if platform == "win32":
            base = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            maya_app_dir = os.path.join(base, "Documents", "maya")
        elif platform == "darwin":
            maya_app_dir = os.path.expanduser(
                "~/Library/Preferences/Autodesk/maya"
            )
        else:
            # Linux
            maya_app_dir = os.path.expanduser("~/maya")

    return os.path.join(maya_app_dir, "modules")


def _copy_payload(repo_root, install_dir):
    """Replace install_dir with a fresh copy of the plugin files from repo_root."""
    if os.path.isdir(install_dir):
        shutil.rmtree(install_dir)
    os.makedirs(install_dir)

    skip = shutil.ignore_patterns("__pycache__", "*.pyc")
    for name in _PAYLOAD:
        src = os.path.join(repo_root, name)
        dst = os.path.join(install_dir, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst, ignore=skip)
        else:
            shutil.copy2(src, dst)


def _write_mod_file(modules_dir, install_dir):
    """Write RawKee.mod into modules_dir, pointing at install_dir."""
    # .mod files accept forward slashes on all platforms.
    install_dir_fwd = install_dir.replace("\\", "/")

    mod_content = (
        "+ RawKee_PythonEdition_X3D 2.1.0 {root}\n"
        "PYTHONPATH+:=.\n"
        "MAYA_PLUG_IN_PATH+:=.\n"
        "MAYA_SCRIPT_PATH+:=rawkee4maya/maya/mel\n"
    ).format(root=install_dir_fwd)

    mod_path = os.path.join(modules_dir, "RawKee.mod")
    with open(mod_path, "w") as f:
        f.write(mod_content)

    return mod_path


def _notify(title, message):
    """Show a Maya confirm dialog when inside Maya, otherwise just print."""
    print(message)
    try:
        import maya.cmds as cmds
        cmds.confirmDialog(title=title, message=message, button=["OK"])
    except Exception:
        pass


def _find_mayapy():
    """
    Return the path to the mayapy executable.

    When running inside Maya, sys.executable already points at mayapy.
    Outside Maya, search common installation directories for the current OS.
    Returns None if mayapy cannot be located.
    """
    import subprocess

    # If we're already running inside mayapy, use the current interpreter.
    if "mayapy" in sys.executable.lower():
        return sys.executable

    # Build a list of candidate paths from well-known Maya install locations.
    candidates = []
    if sys.platform == "win32":
        for program_dir in [
            r"C:\Program Files\Autodesk",
            r"C:\Program Files (x86)\Autodesk",
        ]:
            if os.path.isdir(program_dir):
                for entry in sorted(os.listdir(program_dir), reverse=True):
                    if entry.lower().startswith("maya"):
                        candidates.append(
                            os.path.join(program_dir, entry, "bin", "mayapy.exe")
                        )
    elif sys.platform == "darwin":
        for year in range(2030, 2018, -1):
            candidates.append(
                "/Applications/Autodesk/maya{}/Maya.app/Contents/bin/mayapy".format(year)
            )
    else:
        for year in range(2030, 2018, -1):
            candidates.append("/usr/autodesk/maya{}/bin/mayapy".format(year))

    for path in candidates:
        if os.path.isfile(path):
            return path

    # Last resort: check PATH.
    try:
        result = subprocess.run(
            ["where" if sys.platform == "win32" else "which", "mayapy"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            first_line = result.stdout.strip().splitlines()[0].strip()
            if first_line:
                return first_line
    except Exception:
        pass

    return None


def _ensure_python_modules():
    """
    Verify that cv2, imageio.v3, ffmpeg, and PIL are importable by mayapy.
    Any module that cannot be imported is installed via mayapy's pip.

    Import names and their corresponding pip package names differ for some
    of these distributions, so both are tracked explicitly.

    Returns a dict mapping each import name to one of:
      'ok'        – already importable
      'installed' – was missing and installed successfully
      'failed'    – install attempt failed
      'no_mayapy' – mayapy could not be located
    """
    import subprocess

    # (import_name, pip_package_name)
    modules = [
        ("cv2",        "opencv-python"),
        ("imageio.v3", "imageio"),
        ("ffmpeg",     "ffmpeg-python"),
        ("PIL",        "Pillow"),
        ("scipy",      "scipy"),
    ]

    mayapy = _find_mayapy()
    if mayapy is None:
        print("RawKee: Could not locate mayapy — skipping module checks.")
        return {import_name: "no_mayapy" for import_name, _ in modules}

    results = {}
    for import_name, pip_package in modules:
        # Check whether the module is already importable.
        check = subprocess.run(
            [mayapy, "-c", "import {}".format(import_name)],
            capture_output=True,
        )
        if check.returncode == 0:
            print("RawKee: module '{}' is already available in mayapy.".format(import_name))
            results[import_name] = "ok"
            continue

        # Module is missing — attempt to install via pip.
        print("RawKee: module '{}' not found — installing '{}' via mayapy pip...".format(
            import_name, pip_package
        ))
        install_proc = subprocess.run(
            [mayapy, "-m", "pip", "install", pip_package],
            capture_output=True,
            text=True,
        )
        if install_proc.returncode == 0:
            print("RawKee: '{}' installed successfully.".format(pip_package))
            results[import_name] = "installed"
        else:
            print(
                "RawKee: Failed to install '{}'.\n{}".format(
                    pip_package, install_proc.stderr.strip()
                )
            )
            results[import_name] = "failed"

    return results


def install():
    _ensure_python_modules()

    repo_root   = _get_repo_root()
    modules_dir = _get_modules_dir()
    install_dir = os.path.join(modules_dir, _INSTALL_DIR_NAME)

    # Verify we're actually pointing at a RawKee repo before doing anything.
    missing = [n for n in _PAYLOAD if not os.path.exists(os.path.join(repo_root, n))]
    if missing:
        _notify(
            "RawKee Installer — Error",
            "Could not locate the following in:\n  {}\n\n  {}\n\n"
            "Make sure you are running this script from inside the cloned "
            "RawKee repository.".format(repo_root, "\n  ".join(missing)),
        )
        return

    # The install folder is deleted before copying, so never let it overlap the source.
    repo_norm = os.path.normcase(os.path.realpath(repo_root))
    inst_norm = os.path.normcase(os.path.realpath(install_dir))
    if repo_norm == inst_norm or repo_norm.startswith(inst_norm + os.sep):
        _notify(
            "RawKee Installer — Error",
            "This script is running from inside the install folder:\n  {}\n\n"
            "Run it from the cloned RawKee repository instead.".format(install_dir),
        )
        return

    os.makedirs(modules_dir, exist_ok=True)
    try:
        _copy_payload(repo_root, install_dir)
    except OSError as exc:
        _notify(
            "RawKee Installer — Error",
            "Could not copy files to:\n  {}\n\n{}\n\n"
            "If the RawKee plugin is loaded, unload it in the Plug-in Manager "
            "(or restart Maya) and try again.".format(install_dir, exc),
        )
        return
    mod_path = _write_mod_file(modules_dir, install_dir)

    _notify(
        "RawKee Installer — Success",
        (
            "RawKee installation complete.\n\n"
            "  Plugin files : {root}\n"
            "  Module file  : {mod}\n\n"
            "Please restart Maya, then load the plugin through:\n"
            "  Windows > Settings/Preferences > Plug-in Manager"
        ).format(root=install_dir, mod=mod_path),
    )


def onMayaDroppedPythonFile(*args):
    """Entry point Maya calls when this file is dropped into the viewport."""
    install()


if __name__ == "__main__":
    install()
