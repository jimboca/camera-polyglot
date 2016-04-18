
#
# CameraServer
#
# This is the main Camera Node Server.  It was not really necessary to create
# this server but it will allow configuration params to be set and allow
# parsing the main config file or sending out upd requets to find cameras
# and automatically add them.
#
# TODO:
#  - Initialize cameras on started, Need a query for existing cameras, and discover for new cameras?
#  - Pass logger to foscam_poll
#  - Use GV3 to pass timeout to foscam_poll
#

from polyglot.nodeserver_api import Node
from Motion import Motion
from functools import partial
from foscam_poll import foscam_poll
from camera_nodes import *
from camera_funcs import myint,long2ip

CAMERA_SERVER_VERSION = 0.1

class CameraServer(Node):
    """ Node that contains the Main Camera Server settings """

    def __init__(self, parent, address, name, manifest=None):
        self.parent   = parent
        self.address  = address
        self.name     = name
        self.http_get = parent.http_get
        self.parent.logger.info("CameraServer:init: address=%s, name='%s'" % (self.address, self.name))
        # Number of Cameras we are managing
        self.num_cams   = 0
        self.debug_mode = 2
        self.foscam_mjpeg = 1
        # Our version number
        super(CameraServer, self).__init__(parent, self.address, self.name, True, manifest)
        self._add_manifest_cams(manifest)
        self.query();

    def _add_manifest_cams(self,manifest):
        # Add cameras in our manifest
        self.parent.logger.debug("CameraServer:add_manifest_cams: manifest=%s" % (manifest))
        for address in manifest:
            data = manifest[address]
            self.parent.logger.debug("CameraServer:add_manifest_cams: address=%s data=%s" % (address,data))
            drivers = data['drivers']
            if data['node_def_id'] == 'FoscamMJPEG':
                FoscamMJPEG(self.parent, True, long2ip(drivers['GV2']), drivers['GV3'], "polyglot", "poly*glot", manifest, data['name'], address)
                self.num_cams += 1
        
    def query(self, **kwargs):
        """ Look for cameras """
        self.parent.logger.debug("CameraServer:query:start")
        self.set_driver('GV1', CAMERA_SERVER_VERSION, report=False)
        self.set_driver('GV2', self.num_cams, report=False)
        self.set_driver('GV3', self.foscam_mjpeg, report=False)
        self.set_driver('GV4', self.debug_mode, report=False)
        self.report_driver()
        self.parent.logger.debug("CameraServer:query:done")
        return True

    def discover(self, **kwargs):
        """ Look for more cameras """
        manifest = self.parent.config.get('manifest', {})
        if self.foscam_mjpeg > 0:
            self._discover_foscam_m(manifest)
        else:
            self.parent.logger.info("CameraServer: Not Polling for Foscam MJPEG cameras %s" % (self.foscam_mjpeg))
            self.set_driver('GV2', self.num_cams, report=True)
        self.parent.logger.info("CameraServer: Done adding cameras")
        self.parent.update_config()
        return True

    def _discover_foscam_m(self,manifest):
        self.parent.logger.info("CameraServer: Polling for Foscam MJPEG cameras %s" % (self.foscam_mjpeg))
        cams = foscam_poll(self.parent.logger)
        self.parent.logger.info("CameraServer: Got cameras: " + str(cams))
        for cam in cams:
            cam['id'] = cam['id'].lower()
            self.parent.logger.info("CameraServer: Adding camera: %s:%s" % (cam['ip'], cam['port']))
            lnode = self.parent.get_node(cam['id'])
            if not lnode:
                FoscamMJPEG(self.parent, True, cam['ip'], cam['port'], "polyglot", "poly*glot", self.manifest, cam['name'], cam['id'])
                self.num_cams += 1
                self.set_driver('GV2', self.num_cams, report=True)
        
    def poll(self):
        """ Poll TODO: Ping the camera?  """
        return

    def _set_foscam_mjpeg(self, **kwargs):
        """ Enable/Disable Foscam MJPEG UDP Searching
              0 = Off
              0 = 10 second query
              0 = 20 second query
              0 = 30 second query
              0 = 60 second query
        """
        self.foscam_mjpeg = kwargs.get("value")
        self.parent.logger.info("CameraServer: Foscam Polling set to %s" % (self.foscam_mjpeg))
        self.set_driver('GV3', self.foscam_mjpeg, report=True)
        return True
    
    def _set_debug_mode(self, **kwargs):
        """ Enable/Disable Foscam MJPEG UDP Searching
              0 = Off
              1 = Error
              2 = Warning
              3 = Info
              4 = Debug
        """
        self.debug_mode = kwargs.get("value")
        self.parent.logger.info("CameraServer: Debug set to %s" % (self.debug_mode))
        self.set_driver('GV4', self.debug_mode, report=True)
        return True
    
    _drivers = {
        'GV1': [0, 56, float],
        'GV2': [0, 25, myint],
        'GV3': [0, 25, myint],
        'GV4': [0, 25, myint],
    }
    """ Driver Details:
    GV1: integer: This server version number
    GV2: integer: Number of the number of cameras we manage
    GV3: integer: foscam Polling
    GV4: integer: Log Mode
    """
    _commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'SET_FOSCAM_MJPEG': _set_foscam_mjpeg,
        'SET_DM': _set_debug_mode,
    }
    # The nodeDef id of this camers.
    node_def_id = 'CameraServer'

