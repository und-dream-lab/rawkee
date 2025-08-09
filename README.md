# RawKee Python Edition - X3D Plugin 2.x.x for Maya 2025+

For the latest version of the RawKee Python X3D Plugin, visit the [GitHub repository](https://github.com/und-dream-lab/rawkee).

For C++ versions of the plugin (1.2.0) supporting Maya 2019 - Maya 2024, please refer to the [GitHub page](https://github.com/und-dream-lab/rawkee/tree/v1.2.0).

For C++ versions of the plugin (1.1.0) supporting Maya 6.0 - Maya 2008, please refer to the [SourceForge page](https://sourceforge.net/projects/rawkee/).

Some tutorials for RawKee C++ Edition (v 1.1.0/1.2.0) can be found at the Internet Wayback Machine. Unfortunately, the old video tutorials were not archived by IWM.

- [https://web.archive.org/web/20100105142454/http://rawkee.sourceforge.net/tutorials/](https://web.archive.org/web/20100105142454/http://rawkee.sourceforge.net/tutorials/)


## RawKee Python Edition requires the use of 'pip' with 'mayapy'.
1. Most likely, the version of Python for Maya (aka the mayapy executable) is already installed.

2. If for some reason it is not, you can follow the instruction on how to install 'pip' found here:
   [Python.org page](https://pip.pypa.io/en/stable/installation/)
   

## Required Python Packages in addition to standard Maya Python API 1.0/2.0 packages (mayapy).
Some of the packages listed may require a pip install regarless of what the list below explicitly states.
- pillow        (pip install required)
- ffmpeg-python (pip install required)
- xmltodict     (pip install required)
- typing
- numpy
- math
- os
- sys
- base64
- mimetypes
- ctypes
- json 


## Installing from GitHub

1. PIP install the Python packages listed above for your version of Maya and OS.<br>
    a. On Windows use PowerShell to run:          mayapy.exe<br>
    b. On OSX/Linux use the terminal to run:      mayapy<br>
    c. Command line for installing using 'pip': ./mayapy -m pip install some_module

2. Clone the RawKee GitHub main branch using PowerShell or Terminal:<br>
    a. Create a directory somewhere on your computer's hard drive where you<br>
       want to install RawKee. We will use the Linux/OSX style psuedo path of:<br>
       /path/to/your/install/directory<br>
    b. Change directory to:<br>
       /path/to/your/install/directory<br>
    c. Then run the following git command:<br>
       git clone https://github.com/und-dream-lab/rawkee.git

3. Update Maya Environment variables.<br>
    a. Edit your Maya version's Maya.env file adding the following evironment<br>
       variable entries.<br>
    b. Instructions on where to find and edit your Maya.env file can be found here:<br>
       [Autodesk Maya 2026 Environment Variables](https://help.autodesk.com/view/MAYAUL/2026/ENU/?guid=GUID-925EB3B5-1839-45ED-AA2E-3184E3A45AC7)<br>
    c. In the appropriate Maya.env file, make the following entries:<br>
       MAYA_PLUG_IN_PATH=/path/to/your/install/directory/rawkee<br>
       MAYA_SCRIPT_PATH=/path/to/your/install/directoryrawkee/mel

4. Load RawKee Plugin into Maya.<br>
    a. After you start Maya, open the Plug-in Manager through the Maya menu system:<br>
       Windows > Settings/Preferences > Plug-in Manager<br>
    b. Near the top of the Plug-in Manager option window you will see the something<br>
       similar to the following:<br>
       /path/to/your/install/directory/rawkee<br>
       RawKee_Python_X3D.py<br>
    c. Clicke the "Loaded" box to load RawKee, and then close the Plug-in Manager.<br>


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
