
# TODO:
#

import os,sys
from polyglot.nodeserver_api import Node
from functools import partial
from camera_funcs import myint,myfloat,get_network_ip,ip2long,str2bool,bool2int,int2str,str2int
from camera_polyglot_version import VERSION_MAJOR,VERSION_MINOR
from amcrest import AmcrestCamera

class Amcrest1(Node):
    """ 
    Node that contains the Amcrest connection settings
    """

    def __init__(self, parent, primary, user, password, config=None, manifest=None, node_address=None):
        self.parent       = parent
        self.primary      = primary
        self.user         = user
        self.password     = password
        self.connected    = 0
        self.node_address = "none"
        self.l_info("init","config={0}".format(config))
        self.status = {}
        if manifest is not None:
            #
            # TODO: Get this working...
            #
            self.name  = manifest['name']
            if node_address is None:
                self.parent.send_error("Amcrest1:init:%s: node_address must be passed in when using manifest for: " % (name,manifest))
                return False
            self.node_address = node_address
            # TODO: It's ok to not have drivers?  Just let query fill out the info? 
            if not 'drivers' in manifest:
                self.parent.send_error("Amcrest1:init:%s: no drivers in manifest: " % (name,manifest))
                return False
            drivers = manifest['drivers']
            # Get the things we need from the drivers, the rest will be queried.
            self.ip    = long2ip(drivers['GV2'])
            self.port  = drivers['GV3']
            self.sys_ver = drivers['GV11']
            self.full_sys_ver = self.sys_ver
        elif config is not None:
            # Connect to the camera to get it's info.
            self.host      = config['host']
            self.port      = 80
            self.l_info("init","connecting to {0}".format(self.host))
            self.camera    = AmcrestCamera(self.host, self.port, self.user, self.password).camera
            self.l_info("init","got {0}".format(self.camera))
            # Name is the machine name
            self.name      = self.camera.machine_name.decode('utf-8').split('=')[-1].rstrip()
            # Node_Address is last 14 characters of the serial number
            self.node_address = self.camera.serial_number.decode('utf-8').split()[0][-14:].lower()
        else:
            self.parent.send_error("Amcrest1:init:%s: One of manifest or config must be passed in." % (node_address))
            return False
        # Add the Camera
        self.l_info("init","Adding %s %s" % (self.name,self.node_address))
        super(Amcrest1, self).__init__(parent, self.node_address, self.name, primary, manifest)
        # This tracks if _set_motion_params was successful
        self.set_motion_params_st = True
        # Call query to pull in the rest of the params.
        self.query();
        # Add my motion node now that the camera is defined.
        #self.motion = Motion(parent, self, manifest)
        # Tell the camera to ping the parent server on motion.
        #self._set_alarm_params({
        #    'motion_armed': 1,
        #    'http':         1,
        #    'http_url':     "http://%s:%s/motion/%s" % (parent.server.server_address[0], parent.server.server_address[1], self.motion.address)
        #});
        # Query again now that we have set paramaters
        #self.query();
        self.l_info("init","Done Adding camera at %s:%s '%s' %s" % (self.host,self.port,self.name,self.node_address))

    def query(self, **kwargs):
        """ query the camera """
        # pylint: disable=unused-argument
        self.l_info("query","start")
        self._get_status()
        if self.connected == 1:
            # Full System Version
            self.full_sys_ver = self.camera.software_information[0].split('=')[1].decode('utf-8');
            sys_ver_l = self.full_sys_ver.split('.')
            # Just the first part as a float
            self.sys_ver      = myfloat("{0}.{1}".format(sys_ver_l[0],sys_ver_l[1]))
            self.set_driver('GV1', self.sys_ver, uom=56)
            # Initialize network info
            self.ip_address = get_network_ip(self.host)
            self.set_driver('GV2',  ip2long(self.ip_address), uom=56, report=False)
            self.set_driver('GV3',  self.port, uom=56, report=False)
            # Motion
            self.set_driver('GV5', bool2int(self.camera.is_motion_detector_on()), uom=2)
            self._get_motion_params()
            self.set_driver('GV6', self.record_enable,   uom=2)
            self.set_driver('GV7', self.mail_enable,     uom=2)
            self.set_driver('GV8', self.snapshot_enable, uom=2)
            self.set_driver('GV9', self.snapshot_times,  uom=56)
            # All done.
            self.report_driver()
        self.l_info("query","done")
        return True

    def poll(self):
        """ Nothing to poll?  """
        #response = os.system("ping -c 1 -w2 " + self.ip + " > /dev/null 2>&1")
        # Fix the motion params if it failed the last time.
        #if not self.set_motion_params_st and self.connected == 1:
        #    self._set_motion_params()
        self.l_debug("poll","none")
        return

    def long_poll(self):
        self.l_info("long_poll","start")
        # get_status handles properly setting self.connected and the driver
        # so just call it.
        self._get_status()
        self.l_debug("long_poll","done")
        return
    
    def l_info(self, name, string):
        self.parent.logger.info("%s:%s:%s: %s" %  (self.node_def_id,self.node_address,name,string))
        
    def l_error(self, name, string):
        estr = "%s:%s:%s: %s" % (self.node_def_id,self.node_address,name,string)
        self.parent.logger.error(estr)
        self.parent.send_error(estr)
    
    def l_warning(self, name, string):
        self.parent.logger.warning("%s:%s:%s: %s" % (self.node_def_id,self.node_address,name,string))
        
    def l_debug(self, name, string):
        self.parent.logger.debug("%s:%s:%s: %s" % (self.node_def_id,self.node_address,name,string))
        
    # **********************************************************************
    #
    # Functions to grab current state of camera.
    #
    
    def _get_status(self):
        """
        Simple check if the camera is responding.
        """
        self.l_info("_get_status","%s:%s" % (self.host,self.port))
        # Get the led_mode since that is the simplest return status
        rc = self.camera.machine_name
        self.parent.logger.info("_get_status: {0}".format(rc))
        if rc == 0:
            connected = 0
            self.l_error("_get_status"," Failed to get_status: {0}".format(rc))
        else:
            connected = 1
        if connected != self.connected:
            self.connected = connected
            self.set_driver('GV4', self.connected, uom=2, report=True)
        return self.connected
        
    def _get_motion_params(self):
        self.l_info("_get_motion_params","start")
        self.mail_enable     = 0
        self.record_enable   = 0
        self.snapshot_enable = 0
        self.snapshot_times  = 0
        #
        # Grab all motion detect params in one call
        #
        ret = self.camera.motion_detection
        for s in ret.split():
            if '=' in s:
                a = s.split('=')
                name  = a[0]
                value = a[1]
                if '.MailEnable' in name:
                    self.l_info("_get_motion_params","name='{0}' value={1}".format(name,value))
                    self.mail_enable = str2int(value)
                elif '.RecordEnable' in name:
                    self.l_info("_get_motion_params","name='{0}' value={1}".format(name,value))
                    self.record_enable = str2int(value)
                elif '.SnapshotEnable' in name:
                    self.l_info("_get_motion_params","name='{0}' value={1}".format(name,value))
                    self.snapshot_enable = str2int(value)
                elif '.SnapshotTimes' in name:
                    self.l_info("_get_motion_params","name='{0}' value={1}".format(name,value))
                    self.snapshot_times = int(value)
        self.l_info("_get_motion_params","done")
        return

    # **********************************************************************
    #
    # Functions to set state of camera.
    #
    def _set_vmd_enable(self, driver=None, **kwargs):
        """
        Video Motion Detect
        """
        value = kwargs.get("value")
        if value is None:
            self.l_error("_set_vmd_enable","_set_vmd_enable not passed a value: %s" % (value))
            return False
        # TODO: Should use the _driver specified function instead of int.
        self.l_info("_set_vmd_enable","_set_vmd_enable %s" % (value))
        self.camera.motion_detection = int2str(value)
        self.l_info("_set_vmd_enable","is_motion_detector_on: {0}".format(self.camera.is_motion_detector_on()))
        self.set_driver(driver, bool2int(self.camera.is_motion_detector_on()), uom=2, report=True)
        return True

    def _set_motion_param(self, driver=None, param=None, convert=None, **kwargs):
        value = kwargs.get("value")
        if value is None:
            self.l_error("_set_motion_param","not passed a value: %s" % (value) )
            return False
        if convert is not None:
            if convert == "int2str":
                sval = int2str(value)
            elif convert == "int":
                sval = int(value)
            else:
                self.l_info("_set_motion_param","unknown convert={0}".format(convert))
        command = 'configManager.cgi?action=setConfig&MotionDetect[0].EventHandler.{0}={1}'.format(param,sval)
        self.l_info("_set_motion_param","comand={0}".format(command))
        rc = self.camera.command(command)
        self.l_info("_set_motion_param","return={0}".format(rc.content.decode('utf-8')))
        if "ok" in rc.content.decode('utf-8').lower():
            self.set_driver(driver, int(value)) #, 56
            return True
        self.parent.send_error("_set_motion_param failed to set {0}={1} return={2}".format(param,value,rc))
        return False

    def _goto_preset(self, **kwargs):
        """ Goto the specified preset. """
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_goto_preset not passed a value: %s" % (value) )
            return False
        rc = self.camera.go_to_preset(action='start', channel=0, preset_point_number=int(value))
        self.l_info("_goto_preset","return={0}".format(rc))
        if "ok" in rc.decode('utf-8').lower():
            return True
        self.parent.send_error("_goto_preset failed to set {0} message={1}".format(int(value),rc))
        return True

    _drivers = {
        # Camera System Version
        'GV1': [0, 56, myfloat],
        # IP Address
        'GV2': [0, 56, myint],
        # Port
        'GV3': [0, 56, myint],
        # Responding
        'GV4': [0, 2,  myint],
        # Video motion detect
        'GV5': [0, 2,  myint],
        'GV6': [0, 2,  myint],
        'GV7': [0, 2,  myint],
        'GV8': [0, 2,  myint],
        'GV9': [0, 56, myint],
    }
    _commands = {
        'QUERY': query,
        'SET_VMD_ENABLE':  partial(_set_vmd_enable,  driver="GV5" ),
        'SET_VMD_RECORD': partial(_set_motion_param, driver="GV6", param='MailEnable', convert="int2str"),
        'SET_VMD_EMAIL': partial(_set_motion_param, driver="GV7", param='RecordEnable', convert="int2str"),
        'SET_VMD_SNAPSHOT': partial(_set_motion_param, driver="GV8", param='SnapshotEnable', convert="int2str"),
        'SET_VMD_SNAPSHOT_COUNT': partial(_set_motion_param, driver="GV9", param='SnapshotTimes', convert="int"),
        'SET_POS':   _goto_preset,
#        'REBOOT':    _reboot,
    }
    # The nodeDef id of this camers.
    node_def_id = 'Amcrest1'

