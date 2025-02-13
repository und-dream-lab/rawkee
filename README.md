# RawKee Python - X3D Plugin 2.0.0 for Maya 2025+

For the latest version of the RawKee Python X3D Plugin, visit the [GitHub repository](https://github.com/und-dream-lab/rawkee).

For C++ versions of the plugin (1.2.0) supporting Maya 2019 - Maya 2024, please refer to the [GitHub page](https://github.com/und-dream-lab/rawkee/tree/v1.2.0).

For C++ versions of the plugin (1.1.0) supporting Maya 6.0 - Maya 2008, please refer to the [SourceForge page](https://sourceforge.net/projects/rawkee/).

## Usage of 'pip' with 'mayapy' requires installation of 'pip'.
1. Download the 'get-pip.py' installer file. More information about this can be found here:
   [Python.org page](https://packaging.python.org/en/latest/tutorials/installing-packages/)
   
2. Run the installer from the command line using:
   mayapy ./get-pip.py
   

## Required Python Packages in addition to standard Maya Python API 1.0/2.0 packages (mayapy).
Some of the packages listed may require a pip install regarless of what the list below explicitly states.
- x3d           (pip install required)
- pillow        (pip install required)
- ffmpeg-python (pip install required)
- nodejs-bin    (pip install required) -- Required by Sunrize Editor, Will be optional.
- screeninfo    (pip isntall required)
- subprocess - may be removed in the future
- signal     - may be removed in the future
- typing
- numpy
- math
- os
- sys
- base64
- mimetypes
- ctypes

<!--
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
-->

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
