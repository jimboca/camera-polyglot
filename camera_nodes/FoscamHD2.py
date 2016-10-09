
# TODO:
#

import os,sys
sys.path.insert(0,"/home/pi/development/foscam-python-lib")
from polyglot.nodeserver_api import Node
from Motion import Motion
from functools import partial
from camera_funcs import myint,myfloat,ip2long,long2ip,isBitI,setBit,clearBit
from camera_polyglot_version import VERSION_MAJOR,VERSION_MINOR
from foscam import FoscamCamera
import xml.etree.ElementTree as ET

#linkage Motion alarm linkage
#( bit3 | bit2 | bit1 | bit0 )
#bit0:Ring
#bit1:Send mail
#bit2:Snap picture
#bit3:Record
linkage_bits = { "ring":0, "send_mail":1, "snap_picture":2, "record":3 }

class FoscamHD2(Node):
    """ 
    Node that contains the Hub connection settings 
    """

    def __init__(self, parent, primary, user, password, manifest=None, udp_data=None, address=None):
        self.parent      = parent
        self.user        = user
        self.password    = password
        self.connected   = 0
        self.parent.logger.info("FoscamHD2:init: Adding manifest=%s upd_data=%s" % (manifest,udp_data))
        self.status = {}
        # Use Basic authorization for all HD cameras?
        self.auth_mode   = 0
        # Use manifest values if passed in.
        if manifest is not None:
            self.name  = manifest['name']
            if address is None:
                self.parent.send_error("FoscamHD2:init:%s: address must be passed in when using manifest for: " % (name,manifest))
                return False
            self.address = address
            # TODO: It's ok to not have drivers?  Just let query fill out the info? 
            if not 'drivers' in manifest:
                self.parent.send_error("FoscamHD2:init:%s: no drivers in manifest: " % (name,manifest))
                return False
            drivers = manifest['drivers']
            # Get the things we need from the drivers, the rest will be queried.
            self.ip    = long2ip(drivers['GV2'])
            self.port  = drivers['GV3']
            self.sys_ver = drivers['GV11']
            self.full_sys_ver = self.sys_ver
        elif udp_data is not None:
            self.name      = udp_data['name']
            self.address   = udp_data['id'].lower()
            self.ip        = udp_data['ip']
            self.port      = udp_data['port']
            self.sys_ver   = self._parse_sys_ver(udp_data['sys'])
            self.full_sys_ver = str(udp_data['sys'])
        else:
            self.parent.send_error("FoscamHD2:init:%s: One of manifest or udp_data must be passed in." % (address))
            return False
        # Add the Camera
        self.parent.logger.info("FoscamHD2:init: Adding %s %s" % (self.name,self.address))
        super(FoscamHD2, self).__init__(parent, self.address, self.name, primary, manifest)
        # Initialize things that don't change.
        self.set_driver('GV1',  VERSION_MAJOR, uom=56, report=False)
        self.set_driver('GV12', VERSION_MINOR, uom=56, report=False)
        self.set_driver('GV2',  ip2long(self.ip), uom=56, report=False)
        self.set_driver('GV3',  self.port, uom=56, report=False)
        self.set_driver('GV11', self.sys_ver, uom=56, report=False)
        # Call query to pull in the params before adding the motion node.
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
        self.parent.logger.info("FoscamHD2:init: Added camera at %s:%s '%s' %s" % (self.ip,self.port,self.name,self.address))

    def query(self, **kwargs):
        """ query the camera """
        # pylint: disable=unused-argument
        self.parent.logger.info("FoscamHD2:query:start:%s" % (self.name))
        # Get current camera status.
        self._get_cam_all()
        self.parent.logger.info("FoscamHD2:query:done:%s" % (self.name))
        return True

    def poll(self):
        """ Nothing to poll?  """
        #response = os.system("ping -c 1 -w2 " + self.ip + " > /dev/null 2>&1")
        return

    def long_poll(self):
        self.parent.logger.info("FoscamHD2:long_poll:%s:" % (self.name))
        # get_status handles properly setting self.connected and the driver
        # so just call it.
        #self._get_status()
    
    def _parse_sys_ver(self,sys_ver):
        """ 
        Given the camera system version as a string, parse into what we 
        show, which is the last 2 digits
        """
        vnums = sys_ver.split(".")
        self.parent.logger.debug("FoscamHD2:parse_sys_ver: %s 0=%s 1=%s 2=%s 3=%s",sys_ver,vnums[0],vnums[1],vnums[2],vnums[3])
        ver = myfloat("%d.%d" % (int(vnums[2]),int(vnums[3])),2)
        self.parent.logger.debug("FoscamHD2:parse_sys_ver: ver=%f",ver)
        return ver
        
    def get_motion_status(self):
        """
        Called by motion node to return the current motion status.
        0 = Off
        1 = On
        2 = Unknown
        """
        return 0
        self._get_status()
        if not self.status or not 'alarm_status' in self.status:
            return 2
        return int(self.status['alarm_status'])

    def set_motion_status(self,value):
        """
        Called by motion node to set the current motion status.
        """
        self.status['alarm_status'] = value

    # **********************************************************************
    #
    # Camera Access Routines
    #
    def _http_get(self, cmd, payload = {}):
        """ Call http_get on this camera for the specified path and payload """
        # Doesn't accept a payload, so convert to arg
        # and neither basic or digest authmode works!?!? Must pass with command
        #path = "cgi-bin/CGIProxy.fcgi?cmd=%s&usr=%s&pwd=%s" % (cmd,self.user,self.password)
        #for key in payload:
        #    path += "&%s=%s" % (key,payload[key])
        path = "cgi-bin/CGIProxy.fcgi"
        payload['cmd'] = cmd
        payload['usr'] = self.user
        payload['pwd'] = self.password
        return self.parent.http_get(self.ip,self.port,self.user,self.password,path,payload,auth_mode=self.auth_mode)
        
    def _http_get_and_parse(self, cmd, payload = {}):
        """ 
        Call http_get and parse the returned Foscam data into a hash.  The data 
        all looks like:  var id='000C5DDC9D6C';
        """
        ret  = {}
        data = self._http_get(cmd,payload)
        self.parent.logger.debug("FoscamHD2:_http_get_and_parse:%s: data=%s" % (self.name,data))
        if data is False:
            code = -1
        else:
            # Return code is good, unless CGI result changes it later
            code = 0
            root = ET.fromstring(data)
            for child in root.iter():
                if child.tag == 'result':
                    code = int(child.text)
                elif child.tag != 'CGI_Result':
                    ret[child.tag] = child.text
        self.parent.logger.debug("FoscamHD2:_http_get_and_parse:%s: code=%d, ret=%s" % (self.name,code,ret))
        return code,ret

    def _save_keys(self, pfx, rc, params):
        """
        Stores the parsed data in the status dict.
        """
        self.parent.logger.debug("FoscamHD2:_save_keys:%s: pfx=%s rc=%d params=%s" % (self.name,pfx,rc,params))
        if pfx not in self.status:
            self.status[pfx] = dict()
        if rc == 0:
            for key in params.keys():
                self.parent.logger.debug("FoscamHD2:_save_keys:%s: %s:%s=%s" % (self.name,pfx,key,params[key]))
                self.status[pfx][key] = params[key]

    def _http_get_and_parse_keys(self, cmd, pfx = ""):
        """
        Calls http get, parses the keys and stores them in status dict
        """
        rc, data = self._http_get_and_parse(cmd)
        if rc == 0:
            self._save_keys(pfx,rc,data)
        return rc

    # **********************************************************************

    def _get_irled_state(self,report=True):
        """
        Set the status irled_status based on combination of
        irled->mode and infraLedState
          0 = Auto
          1 = Off
          2 = On
          3 = Unknown
        """
        if 'irled_state' in self.status:
            cstate = self.status['irled_state']
        else:
            cstate = -1
        if 'irled' in self.status and 'mode' in self.status['irled']:
            self.parent.logger.info("FoscamHD2:_get_irled_state:%s: irled_mode=%d" % (self.name,int(self.status['irled']['mode'])))
            if int(self.status['irled']['mode']) == 0:
                self.status['irled_state'] = 0
            elif 'devstate' in self.status and 'infraLedState' in self.status['devstate']:
                self.parent.logger.info("FoscamHD2:_get_irled_state:%s: infraLedState=%d" % (self.name,int(self.status['devstate']['infraLedState'])))
                if int(self.status['devstate']['infraLedState']) == 0:
                    self.status['irled_state'] = 1
                else:
                    self.status['irled_state'] = 2
            else:
                self.status['irled_state'] = 3
        else:
            self.status['irled_state'] = 3
        if cstate != self.status['irled_state']:
            self.set_driver('GV5', self.status['irled_state'], uom=25, report=report)
        self.parent.logger.info("FoscamHD2:_get_irled_state:%s: irled_state=%d" % (self.name,self.status['irled_state']))

    # **********************************************************************
    #
    # Functions to grab current state of camera.
    #
    def _get_cam_irled(self,report=True):
        rc = self._http_get_and_parse_keys('getInfraLedConfig',"irled")
        self._get_irled_state(report)
        return rc
    
    def _get_cam_dev_state(self,report=True):
        rc = self._http_get_and_parse_keys('getDevState',"devstate")
        self._get_irled_state(report)
        return rc

    def _get_cam_dev_info(self,report=True):
        rc = self._http_get_and_parse_keys('getDevInfo',"devinfo")
        # Update sys_ver if it's different
        if self.full_sys_ver != str(self.status['devinfo']['hardwareVer']):
            self.parent.logger.info("FoscamHD2:get_status:%s: New sys_ver %s != %s" % (self.name,self.full_sys_ver,str(self.status['devinfo']['hardwareVer'])))
            self.full_sys_ver = str(self.status['devinfo']['hardwareVer'])
            self.sys_ver = self._parse_sys_ver(self.status['devinfo']['hardwareVer'])
            self.set_driver('GV11', self.sys_ver, uom=56, report=False)
        return rc

    def _get_cam_motion_detect_config(self,report=True):
        mk = 'motion_detect'
        st = self._http_get_and_parse_keys('getMotionDetectConfig',mk)
        self.parent.logger.info("FoscamHD2:get_cam_motion_detect_config:%s: st=%d" % (self.name,st))
        if st == 0:
            self.set_driver('GV6', int(self.status[mk]['isEnable']), uom=2, report=report) # ,uom=int, report=False ?
            self.set_driver('GV8', int(self.status[mk]['sensitivity']), uom=25, report=report)
            self.set_driver('GV10', int(self.status[mk]['triggerInterval']), uom=25, report=report)
            self.set_driver('GV13', int(self.status[mk]['snapInterval']), uom=25, report=report)
            sl = int(self.status[mk]['linkage'])
            self.set_driver('GV7', isBitI(sl,linkage_bits['send_mail']), uom=2, report=report)
            self.set_driver('GV14', isBitI(sl,linkage_bits['snap_picture']), uom=2, report=report)
            self.set_driver('GV15', isBitI(sl,linkage_bits['record']), uom=2, report=report)
            self.set_driver('GV16', isBitI(sl,linkage_bits['ring']), uom=2, report=report)
        return st

    def _get_cam_all(self,report=True):
        """ 
        Call get_status on the camera and store in status
        """
        # Can't spit out the device name cause we might not know it yet.
        self.parent.logger.info("FoscamHD2:_get_cam_all: %s:%s" % (self.ip,self.port))
        # Get the led_mode since that is the simplest return status
        rc = self._get_cam_irled()
        self.parent.logger.info("FoscamHD2:_get_cam_all: rc=%d" % (rc))
        if rc == 0:
            connected = 1
            self._get_cam_dev_state(report=False)
            self._get_cam_dev_info(report=False)
            self._get_cam_motion_detect_config(report=False)
        else:
            self.parent.send_error("FoscamHD2:_get_all_params:%s: Failed to get_status: %d" % (self.name,rc))
            # inform the motion node there is an issue if we have a motion node
            #if hasattr(self,'motion'):
            #    self.motion.motion(2)
            #else:
                # TODO: Why was this done?
                #self.status['alarm_status'] = 2
            connected = 0
        if connected != self.connected:
            self.connected = connected
            self.set_driver('GV4', self.connected, uom=2, report=False)
        self.report_driver()
            

    # **********************************************************************
    #
    # Functions to set state of camera.
    #
    def _set_irled_state(self, driver=None, **kwargs):
        """
        irled_state is an interal value based on led auto, manual, on, off settings
        See _get_irled_state for full info.
        """
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_set_irled_state not passed a value: %s" % (value) )
            return False
        # TODO: Should use the _driver specified function instead of int.
        if int(value) == 0:
            # AUTO
            if not self._http_get("setInfraLedConfig",{"mode": int(value)}):
                self.parent.send_error("_set_irled_state failed to set %s=%s" % (param,value) )
        elif int(value) == 1:
            # Manual
            if not self._http_get("setInfraLedConfig",{"mode": 1}):
                self.parent.send_error("_set_irled_state failed to set %s=%s" % (param,1) )
            # Off
            if not self._http_get("closeInfraLed",{}):
                self.parent.send_error("_set_irled_state failed to set infraLedState=0")
        else:
            # Manual
            if not self._http_get("setInfraLedConfig",{"mode": 1}):
                self.parent.send_error("_set_irled_state failed to set %s=%s" % (param,1) )
            # On
            if not self._http_get("openInfraLed",{}):
                self.parent.send_error("_set_irled_state failed to set infraLedState=1")
        # TODO: Dont' think I should be setting the driver?
        self.set_driver(driver, myint(value), 56)
        # The set_alarm param is without the '_alarm' prefix
        self.status['irled_state'] = myint(value)
        return True

    def _set_motion_params(self):
        """ 
        Set all alarm motion params on the camera.  All need to be passed each time
        because if one is not passed it reverts to the default... dumb foscam api ...
        """
        self.parent.logger.info("FoscamMJPEG:set_motion_params:%s:" % (self.name))
        return self._http_get("setMotionDetectConfig",self.status['motion_detect'])

    def _set_motion_param(self, driver=None, param=None, **kwargs):
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_set_motion_param not passed a value: %s" % (value) )
            return False
        self.status['motion_detect'][param] = myint(value)
        if self._set_motion_params():
            # TODO: Need the proper uom from the driver?
            self.set_driver(driver, myint(value), 56)
            return True
        self.parent.send_error("_set_motion_param failed to set %s=%s" % (param,value) )
        return False


    def _set_motion_linkage(self, driver=None, param=None, **kwargs):
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_set_motion_linkage not passed a value: %s" % (value) )
            return False
        if param is None:
            self.parent.send_error("_set_motion_linkage not passed a param: %s" % (param) )
            return False
        if not param in linkage_bits:
            self.parent.send_error("_set_motion_linkage unknown param '%s'" % (param) )
            return False
        value = int(value)
        cval = int(self.status['motion_detect']['linkage'])
        self.parent.logger.debug("_set_motion_linkage: param=%s value=%s, bit=%d, motion_detect_linkage=%s" % (param,value,linkage_bits[param],cval))
        if value == 0:
            cval = clearBit(cval,linkage_bits[param])
        else:
            cval = setBit(cval,linkage_bits[param])
        # TODO: Should use the _driver specified function instead of int.
        self.status['motion_detect']['linkage'] = cval
        self.parent.logger.debug("_set_motion_linkage: %d" % (cval))
        if self._set_motion_params():
            self.set_driver(driver, myint(value), 56)
            return True
        self.parent.send_error("_set_motion_param failed to set %s=%s" % ("linkage",cval) )
        return False

    def _reboot(self, **kwargs):
        """ Reboot the Camera """
        return self._http_get("reboot.cgi",{})

    def _goto_preset(self, **kwargs):
        """ Goto the specified preset. """
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_goto_preset not passed a value: %s" % (value) )
            return False
        if not self._http_get("ptzGotoPresetPoint",{"name": int(value)}):
            self.parent.send_error("_goto_preset failed to set %s" % (int(value)) )
        return True

    _drivers = {
        'GV1': [0, 56, myfloat],
        'GV2': [0, 56, myint],
        'GV3': [0, 56, myint],
        'GV4': [0, 2,  myint],
        'GV5': [0, 25, myint],
        'GV6': [0, 2,  myint],
        'GV7': [0, 2,  myint],
        'GV8': [0, 25, myint],
        'GV9': [0, 2,  myint],
        'GV10': [0, 25,  myint], # Not used currently.
        'GV11': [0, 56,  myfloat],
        'GV12': [0, 56,  myfloat],
        'GV13': [0, 25,  myint],
        'GV14': [0, 2,  myint],
        'GV15': [0, 2,  myint],
        'GV16': [0, 2,  myint],
    }
    """ Driver Details:
    GV1:  float:   Version of this code (Major)
    GV2:  unsigned integer: IP Address
    GV3:  integer: Port
    GV4:  integer: Responding
    GV5:  integer: IR LED Mode
    GV6:  integer: Alarm Motion Armed
    GV7:  integer: Alarm Send Mail
    GV8:  integer: Motion Sensitivity
    GV9:  integer: Motion Compenstation (Not used?)
    GV10; integer: Motion Trigger Interval
    GV11: float:   Camera System Version
    GV12: float:   Version of this code (Minor)
    GV13; integer: Snap Interval
    GV14: integer: Motion Picture
    GV15: integer: Motion Record
    GV16: integer: Motion Ring
    """
    _commands = {
        'QUERY': query,
        'SET_IRLED':  partial(_set_irled_state,  driver="GV5" ),
        'SET_ALMOA': partial(_set_motion_param, driver="GV6", param='isEnable'),
        'SET_ALMOS': partial(_set_motion_param, driver="GV8", param='sensitivity'),
        'SET_MO_TRIG': partial(_set_motion_param, driver="GV10", param='triggerInterval'),
        'SET_MO_RING' : partial(_set_motion_linkage, driver="GV16", param='ring'),
        'SET_MO_MAIL' : partial(_set_motion_linkage, driver="GV7", param='send_mail'),
        'SET_MO_PIC'  : partial(_set_motion_linkage,  driver="GV14", param='snap_picture'),
        'SET_MO_REC'  : partial(_set_motion_linkage,  driver="GV15", param='record'),
        'SET_MO_PIC_INT': partial(_set_motion_param, driver="GV13", param='snapInterval'),
        'SET_POS':   _goto_preset,
        'REBOOT':    _reboot,
    }
    #'SET_ALML':  partial(_set_alarm_param, driver="GV7", param='motion_mail'),
    #'SET_ALMOC': partial(_set_alarm_param, driver="GV9", param='motion_compensation'),
    #'SET_UPINT': partial(_set_alarm_param, driver="GV13", param='triggerInterval'),
    # The nodeDef id of this camers.
    node_def_id = 'FoscamHD2'

