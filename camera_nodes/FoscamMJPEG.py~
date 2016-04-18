
# TODO:
#  - Set var alarm_http_url='http://192.168.1.66:25066/foscam/set.php';
#    To set device status on ISY.
#  - And var alarm_http=1;
#  - Can't use ping for "responding" since it needs root?  So now it is always the same as "connected"

VERSION = 0.1

import os
from polyglot.nodeserver_api import Node
from Motion import Motion
from functools import partial
from camera_funcs import myint,myfloat,ip2long,long2ip

class FoscamMJPEG(Node):
    """ 
    Node that contains the Hub connection settings 
    """
    def __init__(self, parent, primary, ip_address, port, user, password, manifest=None, name=None, address=None):
        self.parent      = parent
        self.ip          = ip_address
        self.port        = port
        self.user        = user
        self.password    = password
        self.connected   = 0
        self.parent.logger.info("FoscamMJPEG: Adding %s:%s" % (self.ip,self.port))
        #
        # Get status which contains the camera id and alias, and we need it to add Motion node.
        self._get_status()
        if not self.status:
            return None
        if name is None:
            name     = self.status['alias']
        if address is None:
            address  = self.status['id']
        # Address must be lower case?
        address = address.lower()
        # Add the Camera
        super(FoscamMJPEG, self).__init__(parent, address, name, primary, manifest)
        self.set_driver('GV1', VERSION, report=False)
        self.set_driver('GV2', ip2long(ip_address), report=False)
        self.set_driver('GV3', port, report=False)
        self._get_params();
        # Add my motion node.
        self.motion = Motion(parent, self, manifest)
        # Tell the camera to ping the parent server on motion.
        self._set_alarm_params({
            'motion_armed': 1,
            'http':         1,
            'http_url':     "http://%s:%s/motion/%s" % (parent.server.server_address[0], parent.server.server_address[1], self.motion.address)
        });
        # Call query to pull in the params.
        self.query();
        self.parent.logger.info("FoscamMJPEG: Added camera at %s:%s '%s' %s" % (self.ip,self.port,name,address))

    def query(self, **kwargs):
        """ query the camera """
        # pylint: disable=unused-argument
        self.parent.logger.info("FoscamMJPEG:query:start: camera '%s'" % (self.name))
        self._get_params();
        self.set_driver('GV4', self.connected, report=False)
        self.set_driver('GV5', self.connected, report=False)
        if self.params:
            self.set_driver('GV6', self.params['alarm_motion_armed'], report=False) # ,uom=int, report=False ?
            self.set_driver('GV7', self.params['alarm_mail'], report=False)
            self.set_driver('GV8', self.params['alarm_motion_sensitivity'], report=False)
            self.set_driver('GV9', self.params['alarm_motion_compensation'], report=False)
        self.report_driver()
        self.parent.logger.info("FoscamMJPEG:query:done: camera '%s'" % (self.name))
        return True

    def _http_get(self, path, payload = {}):
        """ Call http_get on this camera for the specified path and payload """
        return self.parent.http_get(self.ip,self.port,self.user,self.password,path,payload)
        
    def _http_get_and_parse(self, path, payload = {}):
        """ 
        Call http_get and parse the returned Foscam data into a hash.  The data 
        is all looks like:  var id='000C5DDC9D6C';
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
        """ Call get_params on the camera and store in params """
        self.params = self._http_get_and_parse("get_params.cgi")
        if self.params:
            self.connected = 1
        else:
            self.connected = 0

    def poll(self):
        """ Nothing to poll?  """
        #response = os.system("ping -c 1 -w2 " + self.ip + " > /dev/null 2>&1")
        return

    def long_poll(self):
        self._get_status()
        connected = 0
        if self.status:
            connected = 1
        if connected != self.connected:
            self.set_driver('GV3', connected, report=True)
            self.set_driver('GV4', connected, report=True)
    
    def _set_alarm_params(self,params):
        """ 
        Set the sepecified params on the camera
        """
        return self._http_get("set_alarm.cgi",params)

    def _decoder_control(self,params):
        """ 
        Pass in decoder command
        """
        return self._http_get("decoder_control.cgi",params)

    def _get_status(self,report=True):
        """ 
        Call get_status on the camera and store in status
        """
        self.status = self._http_get_and_parse("get_status.cgi")
        if self.status:
            self.connected = 1
        else:
            self.connected = 0
            self.parent.send_error("Failed to get_status of camera %s:%s" % (self.ip,self.port))

    def _set_alarm_param(self, driver=None, param=None, **kwargs):
        value = kwargs.get("value")
        if value is None:
            self.parent.send_error("_set_alarm_param not passed a value: %s" % (value) )
            return False
        # TODO: Should use the _driver specified function instead of int.
        if not self._set_alarm_params({ param: int(value)}):
            self.parent.send_error("_set_alarm_param failed to set %s=%s" % (param,value) )
        # TODO: Dont' think I should be setting the driver?
        self.set_driver(driver, value, report=True)
        # The set_alarm param is without the '_alarm' prefix
        self.params['alarm_'+param] = int(value)
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
        'GV4': [0, 56, myint],
        'GV5': [0, 56, myint],
        'GV6': [0, 56, myint],
        'GV7': [0, 56, myint],
        'GV8': [0, 56, myint],
        'GV9': [0, 56, myint],
    }
    """ Driver Details:
    GV1:  float:   Version of this code.
    GV2:  integer: IP Address
    GV3:  integer: Port
    GV4:  integer: Responding
    GV5:  integer: Connected
    GV6:  integer: Alarm Motion Armed
    GV7:  integer: Alarm Send Mail
    GV8:  integer: Motion Sensitivity
    GV9:  integer: Motion Compenstation
    """
    _commands = {
        'QUERY': query,
        'SET_ALMOA': partial(_set_alarm_param, driver="GV6", param='motion_armed'),
        'SET_ALML':  partial(_set_alarm_param, driver="GV7", param='motion_mail'),
        'SET_ALMOS': partial(_set_alarm_param, driver="GV8", param='motion_sensitivity'),
        'SET_ALMOC': partial(_set_alarm_param, driver="GV9", param='motion_compensation'),
        'SET_POS':   _goto_preset,
    }
    # The nodeDef id of this camers.
    node_def_id = 'FoscamMJPEG'

