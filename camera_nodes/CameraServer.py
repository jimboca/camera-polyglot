
#
# CameraServer
#
# This is the main Camera Node Server.  It was not really necessary to create
# this server but it will allow configuration params to be set and allow
# parsing the main config file or sending out upd requets to find cameras
# and automatically add them.
#
# TODO:
#  - Pass logger to foscam_poll
#  - Use GV3 to pass timeout to foscam_poll
#

from polyglot.nodeserver_api import Node
from Motion import Motion
from functools import partial
from foscam_poll import foscam_poll
from camera_nodes import *
from camera_funcs import myint,long2ip
from camera_polyglot_version import VERSION_MAJOR,VERSION_MINOR
import time

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
        self.debug_mode = 10
        self.foscam_mjpeg = 1
        self._next_beat_t = 0
        if address in manifest:
            drivers = manifest[address]['drivers']
            if 'GV4' in drivers:
                self.debug_mode = drivers['GV4']
            if 'GV3' in drivers:
                self.foscam_mjpeg = drivers['GV3']
        super(CameraServer, self).__init__(parent, self.address, self.name, True, manifest)
        self._add_manifest_cams(manifest)
        self.query();

    def _add_manifest_cams(self,manifest):
        # Add cameras in our manifest
        self.parent.logger.debug("CameraServer:add_manifest_cams: manifest=%s" % (manifest))
        for address in manifest:
            data = manifest[address]
            self.parent.logger.debug("CameraServer:add_manifest_cams: address=%s data=%s" % (address,data))
            if data['node_def_id'] == 'FoscamMJPEG':
                # TODO: Don't pass drivers, let FoscamMJPEG figure it out.
                FoscamMJPEG(self.parent, True,
                            self.parent.cam_config['user'], self.parent.cam_config['password'],
                            manifest=data, address=address)
                self.num_cams += 1
            elif data['node_def_id'] == 'FoscamHD2':
                # TODO: Don't pass drivers, let FoscamMJPEG figure it out.
                FoscamHD2(self.parent, True,
                          self.parent.cam_config['user'], self.parent.cam_config['password'],
                          manifest=data, address=address)
                self.num_cams += 1
        
    def _st(self, **kwargs):
        return self.set_driver('ST', time.time(), report=True)

    def query(self, **kwargs):
        """ Look for cameras """
        self.parent.logger.info("CameraServer:query:")
        self.set_driver('GV1', VERSION_MAJOR, report=False)
        self.set_driver('GV5', VERSION_MINOR, report=False)
        self.set_driver('GV2', self.num_cams, uom=56, report=False)
        self.set_driver('GV3', self.foscam_mjpeg, uom=25, report=False)
        self.set_driver('GV4', self.debug_mode, uom=25, report=False)
        self.report_driver()
        self.parent.logger.debug("CameraServer:query:done")
        return True

    def discover(self, **kwargs):
        """ Look for more cameras """
        manifest = self.parent.config.get('manifest', {})
        if self.foscam_mjpeg > 0:
            self._discover_foscam(manifest)
        else:
            self.parent.logger.info("CameraServer: Not Polling for Foscam MJPEG cameras %s" % (self.foscam_mjpeg))
            self.set_driver('GV2', self.num_cams, uom=56, report=True)
        self.parent.logger.info("CameraServer: Done adding cameras")
        self.parent.update_config()
        return True

    def _discover_foscam(self,manifest):
        self.parent.logger.info("CameraServer:discover_foscam: Polling for Foscam MJPEG cameras %s" % (self.foscam_mjpeg))
        cams = foscam_poll(self.parent.logger)
        self.parent.logger.info("CameraServer: Got cameras: " + str(cams))
        for cam in cams:
            cam['id'] = cam['id'].lower()
            self.parent.logger.info("CameraServer:discover_foscam: Checking to add camera: %s %s" % (cam['id'], cam['name']))
            lnode = self.parent.get_node(cam['id'])
            if lnode:
                self.parent.logger.info("CameraServer:discover_foscam: Already exists, updating %s %s" % (cam['id'], cam['name']))
                lnode.update_config(self.parent.cam_config['user'], self.parent.cam_config['password'], udp_data=cam)
            else:
                if cam['mtype'] == "MJPEG":
                    self.parent.logger.info("CameraServer:discover_foscam: Adding FoscamMJPEG camera: %s" % (cam['name']))
                    FoscamMJPEG(self.parent, True, self.parent.cam_config['user'], self.parent.cam_config['password'], udp_data=cam)
                    self.num_cams += 1
                    self.set_driver('GV2', self.num_cams, uom=56, report=True)
                elif cam['mtype'] == "HD2":
                    self.parent.logger.info("CameraServer:discover_foscam: Adding FoscamHD camera: %s" % (cam['name']))
                    FoscamHD2(self.parent, True, self.parent.cam_config['user'], self.parent.cam_config['password'], udp_data=cam)
                    self.num_cams += 1
                    self.set_driver('GV2', self.num_cams, uom=56, report=True)
                else:
                    self.parent.logger.error("CameraServer:discover_foscam: Unknown type %s for Foscam Camera %s" % (cam['type'],cam['name']))
            self.parent.logger.info("CameraServer:discover_foscam: Done")
        
    def poll(self):
        """ Poll Send DON every 60 seconds or so  """
        now = time.time()
        if now > self._next_beat_t:
            self._next_beat_t = now + 60
            self.set_driver('ST', now, report=True)
            self.report_isycmd('DON')
        return True

    def long_poll(self):
        """ Long Poll Nothing  """
        return

    def _set_foscam_mjpeg(self, **kwargs):
        """ Enable/Disable Foscam MJPEG UDP Searching
              0 = Off
              1 = 10 second query
              2 = 20 second query
              3 = 30 second query
              4 = 60 second query
        """
        self.foscam_mjpeg = kwargs.get("value")
        self.parent.logger.info("CameraServer: Foscam Polling set to %s" % (self.foscam_mjpeg))
        self.set_driver('GV3', self.foscam_mjpeg, uom=25, report=True)
        return True
    
    def _set_debug_mode(self, **kwargs):
        """ Enable/Disable Foscam MJPEG UDP Searching
              0  = All
              10 = Debug
              20 = Info
              30 = Warning
              40 = Error
              50 = Critical
        """
        self.debug_mode = myint(kwargs.get("value"))
        self.parent.logger.info("CameraServer:set_debug_mode: %d" % (self.debug_mode))
        self.set_driver('GV4', self.debug_mode, uom=25, report=True)
        self.logger.setLevel(self.debug_mode)
        return True
    
    _drivers = {
        'ST':  [0, 56, int, False],        
        'GV1': [0, 56, float],
        'GV2': [0, 56, myint],
        'GV3': [0, 25, myint],
        'GV4': [0, 25, myint],
        'GV5': [0, 56, float],
    }
    """ Driver Details:
    GV1:   float:   Version of this code (Major)
    GV2: integer: Number of the number of cameras we manage
    GV3: integer: foscam Polling
    GV4: integer: Log Mode
    GV5:   float:   Version of this code (Major)
    """
    _commands = {
        'ST': _st,
        'QUERY': query,
        'DISCOVER': discover,
        'SET_FOSCAM_MJPEG': _set_foscam_mjpeg,
        'SET_DM': _set_debug_mode,
    }

    _sends = {
        'DON': [None, None, None]
    }
    
    # The nodeDef id of this camers.
    node_def_id = 'CameraServer'

