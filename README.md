# RawKee X3D Plugin 1.2.0 for Maya 2019+

For the latest version of the RawKee X3D Plugin, visit the [GitHub repository](https://github.com/und-dream-lab/rawkee).

For older versions of the plugin (1.1.0) supporting Maya 6.0 - Maya 2008, please refer to the [SourceForge page](https://sourceforge.net/projects/rawkee/).

## Build Tools for RawKee 1.2.0 on Windows 10
- Maya SDK 2019-2025 (Tested with Maya 2023) <br> [Autodesk Maya SDK - https://aps.autodesk.com/developer/overview/maya](https://aps.autodesk.com/developer/overview/maya)- Visual Studio 17 2022
- CMake 3.30
- PowerShell

## Build Instructions

Before you start building RawKee, ensure that the following environment variables are set:

- `RAWKEE_GIT_REPO`: Path to your RawKee Git repository (e.g., `C:\path\to\your\rawkee\repo\`)
- `DEVKIT_LOCATION`: Location of the devkit base (e.g., `C:\path\to\devkitBase\`)
- `MAYA_LOCATION`: Location of the Maya installation (e.g., `C:\path\to\Autodesk\Maya2023\`)

### Steps:
1. **Open PowerShell:**
   Launch PowerShell on your system.

2. **Navigate to your RawKee Git repository:**
   Use the `cd` command to change your directory to the RawKee Git repository location.

3. **Run Build Commands:**
   Execute the following commands in sequence:
   ```shell
   clear
   cmake -Bbuild -G "Visual Studio 17 2022"
   cmake --build build
   ```
   **Note:** Ensure to delete the "build" directory before attempting to re-compile/build.

4. **Copy Build Files:**
   Transfer the compiled plugin and other necessary files to your Maya Plugins folder:
    - `build\Debug\x3d.mll` to `plug-ins\x3d.mll`
    - `mel\*.mel` to `scripts\*.mel`
    - `icons\*.bmp` to `icons\*.bmp`

This will complete the setup of the RawKee X3D Plugin 1.2.0 for Maya 2019+. Happy modeling!

## Contact Information
For further assistance, contact Aaron:
- **Email:** aaron.bergstrom@und.edu
- **Organization:** UND Computational Research Center - DREAM Lab
- **Website:** [DREAM Lab](https://dream.crc.und.edu/)