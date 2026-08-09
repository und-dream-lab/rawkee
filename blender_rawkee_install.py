"""
RawKee Blender Addon Installer
--------------------------------
Open this file in Blender's Text Editor (Text > Open) and click
'Run Script' to install the RawKee addon.

The script will:
  1. Detect the repo root from this file's location.
  2. Copy the 'rawkee' package to Blender's user modules directory so
     that it is importable on every Blender launch.
  3. Copy the 'rawkee4blender' package to Blender's user modules directory.
  4. Copy Blender_RawKee_Python_X3D.py to Blender's user addons directory.
  5. Enable the addon and save user preferences.

Restart Blender after running to confirm the installation is fully active.

NOTE: Open this file from disk (Text > Open) rather than pasting it into
a new text block so that __file__ is defined and the repo root can be
detected automatically.
"""

import bpy
import os
import sys
import shutil


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_repo_root():
    """
    Return the absolute path to the repo root (the folder that contains
    both this installer and the 'rawkee' / 'rawkee4blender' packages).

    Blender's Text Editor sets __file__ to only the bare filename when
    the script is opened from disk, so os.path.abspath(__file__) resolves
    against Blender's working directory (often C:\\) rather than the actual
    file location.  We therefore prefer the Blender API path and only fall
    back to __file__ when it resolves to a real file.
    """
    # 1. Ask Blender for the on-disk path of the active text block.
    try:
        text = bpy.context.space_data.text
        if text and text.filepath:
            p = os.path.abspath(bpy.path.abspath(text.filepath))
            if os.path.isfile(p):
                return os.path.dirname(p)
    except Exception:
        pass

    # 2. Fall back to __file__ when it resolves to an actual file.
    try:
        p = os.path.abspath(__file__)
        if os.path.isfile(p):
            return os.path.dirname(p)
    except NameError:
        pass

    # 3. No reliable path found — the user pasted the script into a new,
    #    unsaved text block.  Return None so the caller can show an error.
    return None


def _get_user_scripts_root():
    """Return Blender's user scripts root (guaranteed to exist)."""
    return bpy.utils.script_path_user()


def _get_modules_dir():
    """
    Return Blender's user modules directory, creating it when necessary.
    Blender automatically adds this directory to sys.path, making any
    package placed here importable without extra sys.path manipulation.
    """
    modules_dir = os.path.join(_get_user_scripts_root(), "modules")
    os.makedirs(modules_dir, exist_ok=True)
    return modules_dir


def _get_addons_dir():
    """Return Blender's user addons directory, creating it when necessary."""
    addons_dir = os.path.join(_get_user_scripts_root(), "addons")
    os.makedirs(addons_dir, exist_ok=True)
    return addons_dir


def _copy_package(repo_root, modules_dir, package_name):
    """
    Copy a Python package from the repo into Blender's modules directory.
    Any previous installation is removed first so the copy is always clean.
    """
    src = os.path.join(repo_root, package_name)
    dst = os.path.join(modules_dir, package_name)

    if os.path.exists(dst):
        shutil.rmtree(dst)

    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dst


def _copy_addon_entry_point(repo_root, addons_dir):
    """
    Copy Blender_RawKee_Python_X3D.py into Blender's user addons directory.
    """
    src = os.path.join(repo_root, "Blender_RawKee_Python_X3D.py")
    dst = os.path.join(addons_dir, "Blender_RawKee_Python_X3D.py")
    shutil.copy2(src, dst)
    return dst


def _enable_addon(modules_dir):
    """
    Add modules_dir to sys.path for the current session and enable the addon.
    """
    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)

    addon_module = "Blender_RawKee_Python_X3D"
    try:
        bpy.ops.preferences.addon_enable(module=addon_module)
        bpy.ops.wm.save_userpref()
        return f"Addon '{addon_module}' enabled and preferences saved."
    except Exception as exc:
        return (
            f"Could not auto-enable addon: {exc}\n"
            "Enable it manually via Edit > Preferences > Add-ons."
        )


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


def _check_pip_dependencies():
    """Check all required pip packages and install any that are missing.
    Uses actual import attempts. After install, queries pip show for the exact
    install location and adds it to sys.path so packages are usable immediately
    in the current session — works across all Blender versions."""
    import subprocess, importlib

    # pip install-name → Python import-name
    PACKAGES = {
        "numpy":         "numpy",
        "imageio":       "imageio",
        "opencv-python": "cv2",
        "scipy":         "scipy",
        "PySide6":       "PySide6",
        "MaterialX":     "MaterialX",
    }

    def _importable(import_name):
        try:
            __import__(import_name)
            return True
        except Exception as e:
            print(f"[RawKee] Cannot import '{import_name}': {type(e).__name__}: {e}")
            return False

    def _add_pip_location(pip_name):
        """Query pip show to find install location and add it to sys.path."""
        show = subprocess.run(
            [sys.executable, "-m", "pip", "show", pip_name],
            capture_output=True, text=True,
        )
        for line in show.stdout.splitlines():
            if line.startswith("Location: "):
                loc = os.path.normpath(line[10:].strip())
                if loc not in [os.path.normpath(p) for p in sys.path]:
                    sys.path.insert(0, loc)
                break

    missing = [pip for pip, imp in PACKAGES.items() if not _importable(imp)]
    if not missing:
        return [f"Python dependencies OK: {', '.join(PACKAGES)}"]

    lines = [f"Missing: {', '.join(missing)}", "Installing via pip …"]

    import site as _site
    user_site = _site.getusersitepackages()
    os.makedirs(user_site, exist_ok=True)

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--target", user_site] + missing,
        capture_output=True, text=True,
    )

    # Find and register every installed package's location immediately
    for pip_name in missing:
        _add_pip_location(pip_name)
    importlib.invalidate_caches()

    if result.returncode == 0:
        lines.append(f"Installed: {', '.join(missing)}")
    else:
        lines.append("pip install FAILED — see system console for details.")
        print(result.stderr)
    return lines


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def install():
    repo_root = _get_repo_root()

    if repo_root is None:
        _show_result(
            "RawKee Install — Error",
            [
                "Could not determine the repo root path.",
                "",
                "Make sure you opened this script from disk using",
                "Text > Open in the Text Editor (do not paste it into",
                "a new unsaved text block), then click 'Run Script'.",
            ],
        )
        return

    # Validate required packages and addon entry point exist in repo.
    required_packages = ["rawkee", "rawkee4blender"]
    for pkg in required_packages:
        pkg_src = os.path.join(repo_root, pkg)
        if not os.path.isdir(pkg_src):
            _show_result(
                "RawKee Install — Error",
                [
                    f"'{pkg}' package not found in: {repo_root}",
                    "",
                    "Run this script from the cloned RawKee repository root.",
                ],
            )
            return

    addon_src = os.path.join(repo_root, "Blender_RawKee_Python_X3D.py")
    if not os.path.isfile(addon_src):
        _show_result(
            "RawKee Install — Error",
            [
                f"Blender_RawKee_Python_X3D.py not found in: {repo_root}",
                "",
                "Run this script from the cloned RawKee repository root.",
            ],
        )
        return

    modules_dir = _get_modules_dir()
    addons_dir  = _get_addons_dir()

    rawkee_dst          = _copy_package(repo_root, modules_dir, "rawkee")
    rawkee4blender_dst  = _copy_package(repo_root, modules_dir, "rawkee4blender")
    addon_dst           = _copy_addon_entry_point(repo_root, addons_dir)
    status_msg          = _enable_addon(modules_dir)
    dep_lines           = _check_pip_dependencies()

    _show_result(
        "RawKee Blender Installer — Done",
        [
            f"Repo root        : {repo_root}",
            f"rawkee           : {rawkee_dst}",
            f"rawkee4blender   : {rawkee4blender_dst}",
            f"Addon file       : {addon_dst}",
            "",
            status_msg,
            "",
        ] + dep_lines + [
            "",
            "Please restart Blender to confirm the installation.",
        ],
    )


install()
