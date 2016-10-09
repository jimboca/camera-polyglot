# camera-polyglot

This is the Camera Poly for the ISY Polyglot interface.  
(c) JimBoCA aka Jim Searle
MIT license. 

This node server is intended to support any type of camera.  Currently the following are supported:

1. Foscam MJPEG
  This is any Foscam Camera MJPEG camera.  This should be any camera that uses this interface  [Foscam IP Camera CGI](docs/ipcam_cgi_sdk.pdf) which includes the non-HD Smarthome INSTEON cameras that are rebranded Foscam's.
  * See README_foscam.md for more information
  * All the params are documented in the pdf mentioned above, if you have questions about them, please read that document first.
  * The 'IR LED' only has a set option, and does not display the status because it seems there is no way to get the status of this from the camera that I can find.  If you know how, please tell me!
  * The 'Network LED Mode' is the led_mode from the camera which is defined as:
    * led_mode=0 : LED indicates network connection
    * led_mode=1 : LED indicates connected network type 
    * led_mode=2 : LED deactivated except during camera boot

2. FoscamHD2 (H.264)
   Any Camera that uses the interface [Foscam IPCamera CGI User Guide](docs/Foscam%20IPCamera%20CGI%20User%20Guide-V1.0.4.pdf)
   To use the Goto preset control you must defined presets named "1", "2", "3", ... on the camera.  I would like to support using the preset names defined on the camera but that would require creating the profile.zip on the fly which is possible, but hasn't been done yet.

   Tested with:
   
   Camera Model | System Version
   ------------ | --------------
   FI9828P V2   | 1.4.1.10
   FI9826P V2   | 1.5.3.19

# Requirements

1. Currently you must be running at least the unstable-rc version of polyglot.  You must grab the uncompiled version as instructed here:  https://github.com/UniversalDevicesInc/Polyglot/wiki/Polyglot-README#to-run-the-python-module-non-compiled-version Then also switch to the unstable-rc branch before running polyglot with `git checkout unstable-rc` when in the checked out Polyglot directory.  But, if you are using another node server you pulled down from github, it may not yet be compatible so check with the Author before switching to this version!
2. This has only been tested on the ISY 5.0.2 Firmware.
3. Install required python modules as instructed in Install Step #1

# Install

Install:

1. Pull the camera-polyglot into Polyglot
  * `cd polyglot/config/node_servers`
  * `git clone https://github.com/jimboca/camera-polyglot.git`
  * `cd camera-polyglot`
  * `sudo pip install -r requirements.txt`
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

# Update

To update, go to where you grabbed camera-polyglot and update:

1. `cd camera-polyglot`
2. `git pull`
3. Go to polyglot web page and Restart Server

If the update has profile changes, then download the new profile from the Polyglot web page, and upload the profile into your node server on the ISY.

# Debugging

This node server creates a log file as Polyglot/config/camera-polyglot/camera.log, where 'camera' is what you called the node server in Polyglot.  If you have any issues, first review that file, and also look for Errors with 'grep ERROR camera.log'.

# Programs

Create programs on the ISY to monitor the Camera Server.

1. First create a state variable s.Polyglot.CamServer, or whatever you want to call it.
2. Create all the following programs

   * I put them all in a subfolder:
```
    ===========================================
    Polyglot - [ID 025B][Parent 0001]

    Folder Conditions for 'Polyglot'

    If
       - No Conditions - (To add one, press 'Schedule' or 'Condition')
 
    Then
       Allow the programs in this folder to run.
```

   * Heartbeat Monitor
```
    -------------------------------------------
    CamS - [ID 025C][Parent 025B]

    If
        'Camera Server' is switched On
 
    Then
        $s.Polyglot.CamServer  = 1
        Wait  5 minutes 
        $s.Polyglot.CamServer  = 2
 
    Else
        $s.Polyglot.CamServer  = 2
 
    Watch for CamS DON, wait 5 minutes and set error if not seen.
```

  * Okay notification
```
    -------------------------------------------
    CamS Okay - [ID 0260][Parent 025B]

    If
        $s.Polyglot.CamServer is 1
 
    Then
        Send Notification to 'Pushover-P1' content 'Polyglot Status'
 
    This will be sent when CamS status is changed from anything to 1.
    Which means it will be sent when a problem is fixed, or ISY is starting up.
```

   * Problem Notification
```
    -------------------------------------------
    CamS Problem - [ID 025D][Parent 025B]

    If
        $s.Polyglot.CamServer is 2
 
    Then
        Send Notification to 'Pushover-P1' content 'Polyglot Status'
 
    CamS status 2 is a problem, send notification.
```

   * Daily Problem reminder
```
    -------------------------------------------
    CamS Problem Reminder - [ID 025F][Parent 025B]

    If
        $s.Polyglot.CamServer is 2
    And (
             Time is  8:00:00AM
          Or Time is  6:00:00PM
        )
 
    Then
        Send Notification to 'Pushover-P1' content 'Polyglot Status'
 
    CamS status 2 is a problem, send notification every day.
```

   * Startup action
```
    -------------------------------------------
    CamS Startup - [ID 025E][Parent 025B]

    If
        $s.Polyglot.CamServer is 0
 
    Then
        Run Program 'CamS' (Then Path)
 
    CamS init is zero, which only happens at startup, so start watching the CamS.
```

3. Create a custom notification 'Polyglot Status':
```
Subject: ISY: Polyglot Status
Body:
CameraServer Status: ${var.2.155}
0: Not initialized
1: Okay
2: Not responding
```

