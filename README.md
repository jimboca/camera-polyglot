# camera-polyglot

This is the Camera Poly for the ISY Polyglot interface.  
(c) JimBoCA aka Jim Searle
MIT license. 

This node server is intended to support any type of camera.  Currently the following are supported:

1.Foscam MJPEG
  This is any Foscam Camera whose model begins with F18.  This should be any camera that uses this interface http://www.foscam.es/descarga/ipcam_cgi_sdk.pdf which includes the non-HD Smarthome INSTEON cameras that are rebranded Foscam's.
  This uses UDP broadcasts to discover and add the cameras.  The same way the Foscam 'IP Camera Tool' finds your cameras.  So there is no need to setup ip address and port for each one.  It uses the Camera ID as the ISY device address, and Camera Alias as the ISY name.


# Requirements

1. Currently you must be running at least the unstable-rc version of polyglot.  You must grab the uncompiled version as instructed here:  https://github.com/UniversalDevicesInc/Polyglot/wiki/Polyglot-README#to-run-the-python-module-non-compiled-version Then also switch to the unstable-rc branch before running polyglot with `git checkout unstable-rc` when in the checked out Polyglot directory.
2. This has only been tested on the ISY 5.0.2 Firmware.

# Install

Install:

1. Pull the camera-polyglot into Polyglot
  * `cd polyglot/config/node_servers`
  * `git clone https://github.com/jimboca/camera-polyglot.git`
  * `cd camera-polyglot`
2. From the polyglot web page: http://your.pi.ip:8080
  * Refresh the page
  * Select 'Add Node Server'
  * Select 'IP Camera' as the 'Node Server Type'
  * Enter a name.
  * Enter a Node Server ID.  This MUST be the same 'Node Server' slot you intend to use from the ISY!!!
  * Click Add, and it should show up on the left hand side and show 'Running', at least for a few seconds.
3. If this is the first time, it will create a configuration file for you and will die with a message like `ERROR    [04-17-2016 20:06:07] polyglot.nodeserver_manager: camera: IOError: Created default config file, please edit and set the proper values "/home/pi/Polyglot/config/camera-polyglot/config.yaml"`
  * You can view the Polyglot log from the web page by clicking the 'View Log' icon.
  * Edit this config file on your Rpi and set the username and password for your camera(s).
4. Go back to the Polyglot web page:
  * Click on the camera node server on the left of the page
  * Click on the 'Restart Server'
  * The server should stay 'Running' now.
  * Click on the 'Download profile' icon.
  * Select and Copy the 'Base URL' from that page, which you will need for Pasting later.
5. Add as NodeServer in ISY by selecting the empty slot that matches 'Node Server ID' you used in Step 2.
  * Set 'Profile Name' to whatever you want, but might as well be the same as the name used in Step 2.
  * Set the Polyglot 'User Id' and Password.  Default: admin & admin.
  * Paste the 'Base URL' you copied in Step 4.
  * Set Host Name or IP of your machine running Polyglot
  * Set Port to the Polyglot port, default=8080
6. Click 'Upload Profile'
  * Browse to where the 'camera_profile.zip' from Step 4 is located and select it.
7. Reboot ISY
8. Upload Profile again in the node server (quirk of ISY)
9. Reboot ISY again (quirk of ISY)
10. Once ISY is back up, go to Polyglot and restart the Camera node server.
11. You should now have a 'Camera Server' node in the ISY.
  * Select the node
  * Set 'Foscam MJPEG Search' to '10s Query'
  * Set 'Debug' to 'Debug'
  * Click on 'Discover'
  * After about 30 seconds it should have found and added any camera.
12. Write programs and enjoy.

# Debugging

This node server creates a log file as Polyglot/config/camera-polyglot/camera.log, where 'camera' is what you called the node server in Polyglot.  If you have any issues, first review that file, and also look for Errors with 'grep ERROR camera.log'.

