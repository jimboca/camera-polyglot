#!/usr/bin/python

import os,sys
from functools import partial
from amcrest import AmcrestCamera
from camera_funcs import myint,myfloat

camera = AmcrestCamera('192.168.86.120', 80, 'admin', 'thepassword').camera
#camera = AmcrestCamera('', 80, 'admin', 'none').camera

def str2bool(value):
    """
    Args:
        value - text to be converted to boolean
         True values: y, yes, true, t, on, 1
         False values: n, no, false, off, 0
    """
    try:
        if isinstance(value, (str, unicode)):
            return bool(util.strtobool(value))
    except NameError:  # python 3
        if isinstance(value, str):
            return bool(util.strtobool(value))
    return bool(value)


#print "Scanning..."
#scan_ips = camera.scan_devices("192.168.86.1.0");
#print "scan_ips={0}".format(scan_ips)


print "is_motion_detector_on: {0}".format(camera.is_motion_detector_on())
print "is_record_on_motion_detection: {0}".format(camera.is_record_on_motion_detection())
print "is_motion_detected: {0}".format(camera.is_motion_detected)

print "motion_detection=true"
camera.motion_detection = "true"
print "is_motion_detector_on: {0}".format(camera.is_motion_detector_on())
print "motion_detection=false"
camera.motion_detection = "false"
print "is_motion_detector_on: {0}".format(camera.is_motion_detector_on())

#table.MotionDetect[0].EventHandler.MailEnable=true
print "motion_detection={0}".format(camera.motion_detection)

#print camera.motion_detection

# Grab all motion detect params
ret = camera.motion_detection
for s in ret.split():
    if '=' in s:
        print "s={0}".format(s)
        a = s.split('=')
        name  = a[0]
        value = a[1]
        print "name='{0}' value={1}".format(name,value)

mail_enable = [s for s in ret.split() if '.MailEnable=' in s][0].split('=')[-1]
print "mail_enable=",str2bool(mail_enable)

record_enable = [s for s in ret.split() if '.RecordEnable=' in s][0].split('=')[-1]
print "record_enable=",str2bool(record_enable)

print "device_class: {0}".format(camera.device_class)
print "device_type: {0}".format(camera.device_type)
print "general_config: {0}".format(camera.general_config)
print "hardware_version: {0}".format(camera.hardware_version)
print "machine_name: {0}".format(camera.machine_name.split('=')[-1])
print "onvif_information: {0}".format(camera.onvif_information)
print "serial_number: {0}".format(camera.serial_number.split()[0])
print "software_information: {0}".format(camera.software_information)
print "system_information: {0}".format(camera.system_information)
print "vendor_information: {0}".format(camera.vendor_information)
print "version_http_api: {0}".format(camera.version_http_api.split('=')[-1])

print "ptz_presets_list:\n{0}".format(camera.ptz_presets_list())
rc = camera.go_to_preset(action='start', channel=0, preset_point_number=1)
print "go_to_preset={0}".format(rc)

rc = camera.command(
    'configManager.cgi?action='
    'setConfig&MotionDetect[0].Enable={0}'.format("true")
)
print "command={0}".format(rc)
if '[200]' in rc:
    print "command success"
else:
    print "command failed"

name         = camera.machine_name.decode('utf-8').split('=')[-1].rstrip()
node_address = camera.serial_number.decode('utf-8').split()[0][-14:].lower()
sys_ver_l    = camera.software_information[0].split('=')[1].decode('utf-8').split('.');
sys_ver      = myfloat("{0}.{1}".format(sys_ver_l[0],sys_ver_l[1]))

print "\nname=",name;
print "node_address=",node_address
print "version=",sys_ver
