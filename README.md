
# RawKee Python Edition (PE) - X3D Plugin 2.x.x for Maya 2023-2027 and Blender 4.2-5.0+!

This GitHub site supports the latest version of the RawKee X3D exporter plugin for Autodesk Maya and Blender. RawKee PE is compatible with all versions of Maya newer than Maya 2023 and Blender 4.2 on Windows, Linux, and macOS.

### RawKee Python Editon for Maya can now be installed with a script.
- Simply clone the repo, and dragging the maya_rawkee_install.py file to your Maya viewport.
- Let me know if it doesn't work for you.

### New Major Features
## X3D Interaction Editor (Experimental)
- Integrated X_ITE Browser for visualizing X3D scene
- Graph Editor for adding/deleting ROUTEs
- AI Assitant GUI for local AI and remote AI with API Keys
- Supports DCC integration for Maya 2024+ and Blender 5.0+
- Standalone version included.

## HDRI Conversion Tool
- Converts HDR and OpenEXR High Dynamic Range Images to Khronos KTX2 format
- Converts *.hdr/*.exr to *.ktx2 at export time
- Standalone GUI version included.

### RawKee Python Edition - YouTube Tutorials Playlist
- [RawKee PE - YouTube Tutorials Playlist](https://www.youtube.com/@UND-DREAM-Lab/playlists)

### Special Thanks:
- Michalis Kamburelis - [Developer of Castle Game Engine](https://castle-engine.io/) for developer feedback and X3D consulting.
- Holger Seelig - [Developer of X_ITE - X3D/Web3D Viewer](https://create3000.github.io/x_ite/) and [Developer of Sunrize: Multi-Platform X3D Editor](https://create3000.github.io/sunrize/). Development of RawKee PE would have been nearly impossible without them.
- Members of the Web3D HAnim Working Group - John Carlson, Carol McDonald, Joe Williams, and Myeong Won Lee - For their guidance and feedback surrounding the X3D HAnim Spec.

### Early RawKee
Those interested in the deprecated C++ versions of RawKee should see the relevant section at the bottom of this page.

## Installing RawKee for Blender 4.2 and 5.0+

1. Clone the repository (same as the Maya steps above).

2. Open Blender and switch to the **Text Editor** workspace.

3. In the Text Editor header choose **Text > Open** and select
   `blender_rawkee_install.py` from the cloned repo root.
   > **Important:** use *Open* (not paste) so that `__file__` is defined
   > and the installer can locate the repo automatically.

4. Click **Run Script** (or press Alt+P).
   The installer will:
   - Copy the `rawkee` package to Blender's user `modules/` directory
     (Blender adds this directory to `sys.path` automatically).
   - Copy `Blender_RawKee_Python_X3D.py` to Blender's user `addons/`
     directory.
   - Enable the addon and save preferences.

5. Restart Blender. The **RawKee (.X3D)** entry will appear under
   **File > Export** and in the **N-panel** sidebar.

> **Do not install by dragging only `Blender_RawKee_Python_X3D.py` into
> Blender's Preferences.** That copies only the entry-point file and
> leaves the `rawkee` package behind, which causes the
> *"No module named 'rawkee'"* error.

## Contributing

To make contributions to the project, follow these steps:
1. Clone the repository
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Stage your Changes (`git add -A`)
4. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the Branch (`git push`)
6. Open a Pull Request

## Contact Information
For further assistance, contact Aaron:
- **Email:** aaron.bergstrom@und.edu
- **Organization:** UND Computational Research Center - DREAM Lab
- **Website:** [DREAM Lab](https://dream.crc.und.edu/)


## Deprecated C++ Versions of RawKee

C++ versions of the plugin (1.2.0) supporting Maya 2019 - Maya 2024, please refer to the [GitHub page](https://github.com/und-dream-lab/rawkee/tree/v1.2.0).

C++ versions of the plugin (1.1.0) supporting Maya 6.0 - Maya 2008, please refer to the [SourceForge page](https://sourceforge.net/projects/rawkee/).

Some tutorials for RawKee C++ Edition (v 1.1.0/1.2.0) can be found at the Internet Wayback Machine. Unfortunately, the old video tutorials were not archived by IWM.

- [https://web.archive.org/web/20100105142454/http://rawkee.sourceforge.net/tutorials/](https://web.archive.org/web/20100105142454/http://rawkee.sourceforge.net/tutorials/)