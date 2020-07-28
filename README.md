### AutoSharpness
---

#### About

AutoSharpness is a plugin application for Enigma2-based PVRs which allows you to set different picture sharpness values according to the resolution of the video content.  It was created for the purpose of improving the quality of low resolution TV broadcasts.  Please note the quality of the picture sharpening is dependent on the algorithm used by the chipset of your PVR.

#### System Requirements

AutoSharpness was written and tested on a Beyonwiz V2 PVR.  Theoretically it should also run on other Linux-based PVRs which use the Enigma2 system.

#### Installation

Installation consists of copying 2 files to the PVR which contain the application's uncompiled source code.  To do this you will need to connect your PC to the same local network as the PVR, such as by wifi or ethernet cable, and then copy the 2 files to the PVR using for example an FTP application.  The PVR should then automatically compile and run the application at the next restart.

Step by step instructions for Windows PCs:

1. Enable the PVR's network adapter in its system settings.

2. Connect a Windows PC to the same local network as the PVR,
   such as by enabling the PC's wifi adapter, or by connecting
   the PC directly to the rear of the PVR via ethernet cable. 
   
3. Determine the PVR's IP address on your local network,
   which should be listed in the PVR's network settings.
   
4. Determine the PVR's network username and password,
   which should be listed in the PVR's network settings
   (for Beyonwiz PVR's, the default username is "root").

5. Obtain an FTP application for Windows, eg. WinSCP.

6. Use the FTP application to connect to the PVR using the
   IP address, username and password in steps 3 and 4
   (for Beyonwiz PVR's, use encryption=none, port=21).
   
7. In the FTP application, browse to the PVR's folder
   where plugins are located.  On Beyonwiz PVR's this is
   /usr/lib/enigma2/python/Plugins/Extensions
   
8. Create the following folder for AutoSharpness:
   /usr/lib/enigma2/python/Plugins/Extensions/AutoSharpness
   (note: case sensitive).
   
9. Copy plugin.py and \_\_init\_\_.py to the folder created in
   previous step.

10. Restart the PVR.

If installation was successful, the AutoSharpness plugin should now appear in the PVR's plugins menu, and also in the quick access plugins menu (blue button on Beyonwiz PVRs).

To remove AutoSharpness, delete the folder you created in step 8, then restart the PVR.
   
 
#### Screenshots

![Alt text](https://bitbucket.org/CalibrationTools/images/downloads/screenshot_1.png)
![Alt text](https://bitbucket.org/CalibrationTools/images/downloads/screenshot_2.png)
