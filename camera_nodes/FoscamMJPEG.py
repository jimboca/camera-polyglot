
# TODO:
#  - Set var alarm_http_url='http://192.168.1.66:25066/foscam/set.php';
#    To set device status on ISY.
#  - And var alarm_http=1;
#  - Can't use ping for "responding" since it needs root?  So now it is always the same as "connected"

import os
from polyglot.nodeserver_api import Node
from Motion import Motion
from functools import partial
from camera_funcs import myint,myfloat,ip2long,long2ip
from camera_polyglot_version import VERSION_MAJOR,VERSION_MINOR

class FoscamMJPEG(Node):
    """ 
    Node that contains the Hub connection settings 
    """

    def __init__(self, parent, primary, user, password, manifest=None, udp_data=None, address=None):
        self.parent      = parent
        self.user        = user
        self.password    = password
        self.connected   = 0
        self.parent.logger.info("FoscamMJPEG:init: Adding manifest=%s upd_data=%s" % (manifest,udp_data))
        self.auth_mode   = 0
        # Use manifest values if passed in.
        if manifest is not None:
            self.name  = manifest['name']
            if address is None:
                self.parent.send_error("FoscamMJPEG:init:%s: address must be passed in when using manifest for: " % (name,manifest))
                return False
            self.address = address
            # TODO: It's ok to not have drivers?  Just let query fill out the info? 
            if not 'drivers' in manifest:
                self.parent.send_error("FoscamMJPEG:init:%s: no drivers in manifest: " % (name,manifest))
                return False
            drivers = manifest['drivers']
            # Get the things we need from the drivers, the rest will be queried.
            self.ip    = long2ip(drivers['GV2'])
            self.port  = drivers['GV3']
            # New in 0.3
            if 'GV10' in drivers:
                self.auth_mode = drivers['GV10']
            else:
                # Old default was digest
                self.auth_mode = 1
            if 'GV11' in drivers:
                self.sys_ver = drivers['GV11']
            else:
                # Old default was digest
                self.sys_ver = 0.0
            self.full_sys_ver = self.sys_ver
        elif udp_data is not None:
            self.name      = udp_data['name']
            self.address   = udp_data['id'].lower()
            self.auth_mode = self._get_auth_mode(udp_data['sys'])
            self.ip        = udp_data['ip']
            self.port      = udp_data['port']
            self.sys_ver   = self._parse_sys_ver(udp_data['sys'])
            self.full_sys_ver = str(udp_data['sys'])
        else:
            self.parent.send_error("FoscamMJPEG:init:%s: One of manifest or udp_data must be passed in." % (address))
            return False
        # Add the Camera
        self.parent.logger.info("FoscamMJPEG:init: Adding %s %s auth_mode=%d" % (self.name,self.address,self.auth_mode))
        super(FoscamMJPEG, self).__init__(parent, self.address, self.name, primary, manifest)
        self.set_driver('GV1',  VERSION_MAJOR, uom=56, report=False)
        self.set_driver('GV12', VERSION_MINOR, uom=56, report=False)
        self.set_driver('GV2',  ip2long(self.ip), uom=56, report=False)
        self.set_driver('GV3',  self.port, uom=56, report=False)
        self.set_driver('GV10', self.auth_mode, uom=25, report=False)
        self.set_driver('GV11', self.sys_ver, uom=56, report=False)
        # Init these in case we can't query.
        self.status = {}
        self.params = {}
        for param in ('led_mode', 'alarm_motion_armed', 'alarm_mail', 'alarm_motion_sensitivity', 'alarm_motion_compensation', 'alarm_upload_interval'):
            if not param in self.params:
                self.params[param] = 0
        # Call query to pull in the params before adding the motion node.
        self.query();
        # Add my motion node now that the camera is defined.
        self.motion = Motion(parent, self, manifest)
        # Tell the camera to ping the parent server on motion.
        self._set_alarm_params({
            'motion_armed': 1,
            'http':         1,
            'http_url':     "http://%s:%s/motion/%s" % (parent.server.server_address[0], parent.server.server_address[1], self.motion.address)
        });
        # Query again now that we have set paramaters
        self.query();
        self.parent.logger.info("FoscamMJPEG:init: Added camera at %s:%s '%s' %s" % (self.ip,self.port,self.name,self.address))

    def update_config(self, user, password, udp_data=None):
        self.parent.logger.info("FoscamMJPEG:update_config: upd_data=%s" % (udp_data))
        self.user        = user
        self.password    = password
        if udp_data is not None:
            self.name      = udp_data['name']
            self.auth_mode = self._get_auth_mode(udp_data['sys'])
            self.ip        = udp_data['ip']
            self.port      = udp_data['port']
            self.sys_ver   = self._parse_sys_ver(udp_data['sys'])
            self.full_sys_ver = str(udp_data['sys'])
        self.set_driver('GV2',  ip2long(self.ip), uom=56, report=False)
        self.set_driver('GV3',  self.port, uom=56, report=False)
        self.set_driver('GV10', self.auth_mode, uom=25, report=False)
        self.set_driver('GV11', self.sys_ver, uom=56, report=False)
        self.query()
        
    def query(self, **kwargs):
        """ query the camera """
        # pylint: disable=unused-argument
        self.parent.logger.info("FoscamMJPEG:query:start:%s" % (self.name))
        # Get current camera params.
        self._get_params();
        # Get current camera status.
        self._get_status();
        # Set GV4 Responding
        self.set_driver('GV4', self.connected, uom=2, report=False)
        if self.params:
            self.set_driver('GV5', self.params['led_mode'], uom=25, report=False) # ,uom=int, report=False ?
            self.set_driver('GV6', self.params['alarm_motion_armed'], uom=2, report=False) # ,uom=int, report=False ?
            self.set_driver('GV7', self.params['alarm_mail'], uom=2, report=False)
            self.set_driver('GV8', self.params['alarm_motion_sensitivity'], uom=25, report=False)
            self.set_driver('GV9', self.params['alarm_motion_compensation'], uom=2, report=False)
            self.set_driver('GV13', self.params['alarm_upload_interval'], uom=2, report=False)
        self.report_driver()
        self.parent.logger.info("FoscamMJPEG:query:done:%s" % (self.name))
        return True

    def _http_get(self, path, payload = {}):
        """ Call http_get on this camera for the specified path and payload """
        return self.parent.http_get(self.ip,self.port,self.user,self.password,path,payload,auth_mode=self.auth_mode)
        
    def _http_get_and_parse(self, path, payload = {}):
        """ 
        Call http_get and parse the returned Foscam data into a hash.  The data 
        all looks like:  var id='000C5DDC9D6C';
        """
        data = self._http_get(path,payload)
        if data is False:
            return False
        ret  = {}
        for item in data.splitlines():
            param = item.replace('var ','').replace("'",'').strip(';').split('=')
            ret[param[0]] = param[1]
        return ret
    
    def _get_params(self):
        """ Call get_params and get_misc on the camera and store in params """
        params = self._http_get_and_parse("get_params.cgi")
        if not params:
            self.parent.send_error("FoscamMJPEG:_get_params:%s: Unable to get_params" % (self.name))
            self.connected = 0
            return False
        self.connected = 1
        self.params = self._http_get_and_parse("get_params.cgi")
        misc = self._http_get_and_parse("get_misc.cgi")
        self.params['led_mode'] = misc['led_mode']

    def poll(self):
        """ Nothing to poll?  """
        #response = os.system("ping -c 1 -w2 " + self.ip + " > /dev/null 2>&1")
        return

    def long_poll(self):
        self.parent.logger.info("FoscamMJPEG:long_poll:%s:" % (self.name))
        # get_status handles properly setting self.connected and the driver
        # so just call it.
        self._get_status()
    
    def _parse_sys_ver(self,sys_ver):
        """ 
        Given the camera system version as a string, parse into what we 
        show, which is the last 2 digits
        """
        vnums = sys_ver.split(".")
        if len(vnums) == 4:
            self.parent.logger.debug("FoscamMJPEG:parse_sys_ver: %s 0=%s 1=%s 2=%s 3=%s",sys_ver,vnums[0],vnums[1],vnums[2],vnums[3])
            ver = myfloat("%d.%d" % (int(vnums[2]),int(vnums[3])),2)
            self.parent.logger.debug("FoscamMJPEG:parse_sys_ver: ver=%f",ver)
            return ver
        else:
            return None
        
    def _get_auth_mode(self,sys_ver):
        """ 
        Given the camera system version as a string, figure out the 
        authorization mode.  Default is 0 (Basic) but if last 2 
        digits of sys_ver are > 2.52 then use 1 (Digest)
        """
        auth_mode = 0
        vnums = sys_ver.split(".")
        if int(vnums[2]) >= 2 and int(vnums[3]) > 52:
            auth_mode = 1
        return auth_mode
        
    def _set_alarm_params(self,params):
        """ 
        Set the sepecified alarm params on the camera
        """
        self.parent.logger.info("FoscamMJPEG:set_alarm_params:%s: %s" % (self.name,params))
        return self._http_get("set_alarm.cgi",params)

    def _set_misc_params(self,params):
        """ 
        Set the sepecified misc params on the camera
        """
        self.parent.logger.info("FoscamMJPEG:set_misc_params:%s: %s" % (self.name,params))
        return self._http_get("set_misc.cgi",params)

    def _decoder_control(self,params):
        """ 
        Pass in decoder command
        """
        self.parent.logger.info("FoscamMJPEG:set_decoder_control:%s: %s" % (self.name,params))
        return self._http_get("decoder_control.cgi",params)

    def get_motion_status(self):
        """
        Called by motion node to return the current motion status.
        0 = Off
        1 = On
        2 = Unknown
        """
        self._get_status()
        if not self.status or not 'alarm_status' in self.status:
            return 2
        return int(self.status['alarm_status'])

    def set_motion_status(self,value):
        """
        Called by motion node to set the current motion status.
        """
        self.status['alarm_status'] = value

    def _get_status(self,report=True):
        """ 
        Call get_status on the camera and store in status
        """
        # Can't spit out the device name cause we might not know it yet.
        self.parent.logger.info("FoscamMJPEG:get_status: %s:%s" % (self.ip,self.port))
        # Get the status
        status = self._http_get_and_parse("get_status.cgi")
        if status:
            connected = 1
            self.status = status
            # Update sys_ver if it's different
            if self.full_sys_ver != str(self.status['sys_ver']):
                self.parent.logger.debug(self.status)
                self.parent.logger.info("FoscamMJPEG:get_status:%s: New sys_ver %s != %s" % (self.name,self.full_sys_ver,str(self.status['sys_ver'])))
                self.full_sys_ver = str(self.status['sys_ver'])
                new_ver = self._parse_sys_ver(self.status['sys_ver'])
                if new_ver is not None:
                    self.sys_ver = new_ver
                    self.set_driver('GV11', self.sys_ver, uom=56, report=True)
        else:
            self.parent.send_error("FoscamMJPEG:_get_params:%s: Failed to get_status" % (self.name))
            # inform the motion node there is an issue if we have a motion node
            if hasattr(self,'motion'):
                self.motion.motion(2)
            else:
                self.status['alarm_status'] = 2
            connected = 0
        if connected != self.connected:
            self.connected = connected
            self.set_driver('GV4', self.connected, uom=2, report=True)

    def _set_alarm_param(self, driver=None, param=None, **kwargs):
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_set_alarm_param not passed a value: %s" % (value) )
            return False
        # TODO: Should use the _driver specified function instead of int.
        if not self._set_alarm_params({ param: int(value)}):
            self.parent.send_error("_set_alarm_param failed to set %s=%s" % (param,value) )
        # TODO: Dont' think I should be setting the driver?
        self.set_driver(driver, myint(value), 56)
        # The set_alarm param is without the '_alarm' prefix
        self.params['alarm_'+param] = myint(value)
        return True

    def _set_misc_param(self, driver=None, param=None, **kwargs):
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_set_misc_param not passed a value for driver %s: %s" % (driver, value) )
            return False
        # TODO: Should use the _driver specified function instead of int.
        if not self._set_misc_params({ param: int(value)}):
            self.parent.send_error("_set_misc_param failed to set %s=%s" % (param,value) )
        # TODO: Dont' think I should be setting the driver?
        self.set_driver(driver, myint(value), 56)
        # The set_misc param
        self.params[param] = myint(value)
        return True

    def _reboot(self, **kwargs):
        """ Reboot the Camera """
        return self._http_get("reboot.cgi",{})

    def _set_irled(self, **kwargs):
        """ Set the irled off=94 on=95 """
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_set_irled not passed a value: %s" % (value) )
            return False
        if value == 0:
            dvalue = 94
        else:
            dvalue = 95
        if self._decoder_control( { 'command': dvalue} ):
            # TODO: Not storing this cause the camera doesn't allow us to query it.
            #self.set_driver("GVxx", myint(value), 56)
            return True
        self.parent.send_error("_set_irled failed to set %s" % (dvalue) )
        return False

    def _set_authm(self, **kwargs):
        """ Set the auth mode 0=Basic 1=Digest """
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_set_authm not passed a value: %s" % (value) )
            return False
        self.auth_mode = int(value)
        self.parent.logger.debug("FoscamMJPEG:set_authm: %s",self.auth_mode)
        self.set_driver("GV10", self.auth_mode, 25)
        # Since they changed auth mode, make sure it works.
        self.query()
        self.motion.query()
        return True

    def _goto_preset(self, **kwargs):
        """ Goto the specified preset. 
              Preset 1 = Command 31
              Preset 2 = Command 33
              Preset 3 = Command 35
              Preset 16 = Command 61
              Preset 32 = Command 93
            So command is ((value * 2) + 29)
        """
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_goto_preset not passed a value: %s" % (value) )
            return False
        value * 2 + 29
        value = myint((value * 2) + 29)
        if not self._decoder_control( { 'command': value} ):
            self.parent.send_error("_goto_preset failed to set %s" % (value) )
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
        'GV10': [0, 25,  myint],
        'GV11': [0, 56,  myfloat],
        'GV12': [0, 56,  myfloat],
        'GV13': [0, 25,  myint],
    }
    """ Driver Details:
    GV1:  float:   Version of this code (Major)
    GV2:  unsigned integer: IP Address
    GV3:  integer: Port
    GV4:  integer: Responding
    GV5:  integer: Network LED Mode
    GV6:  integer: Alarm Motion Armed
    GV7:  integer: Alarm Send Mail
    GV8:  integer: Motion Sensitivity
    GV9:  integer: Motion Compenstation
    GV10; integer: Authorization Mode
    GV11: float:   Camera System Version
    GV12: float:   Version of this code (Minor)
    GV13; integer: Upload Interval
    """
    _commands = {
        'QUERY': query,
        'SET_IRLED': _set_irled,
        'SET_LEDM':  partial(_set_misc_param,  driver="GV5", param='led_mode'),
        'SET_ALMOA': partial(_set_alarm_param, driver="GV6", param='motion_armed'),
        'SET_ALML':  partial(_set_alarm_param, driver="GV7", param='motion_mail'),
        'SET_ALMOS': partial(_set_alarm_param, driver="GV8", param='motion_sensitivity'),
        'SET_ALMOC': partial(_set_alarm_param, driver="GV9", param='motion_compensation'),
        'SET_UPINT': partial(_set_alarm_param, driver="GV13", param='upload_interval'),
        'SET_AUTHM': _set_authm,
        'SET_POS':   _goto_preset,
        'REBOOT':    _reboot,
    }
    # The nodeDef id of this camers.
    node_def_id = 'FoscamMJPEG'

