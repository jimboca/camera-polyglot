
from polyglot.nodeserver_api import Node

def myint(value):
    """ round and convert to int """
    return int(round(float(value)))

class Motion(Node):
    """ Node that monitors motion """

    def __init__(self, parent, primary, manifest=None):
        full_name    = primary.name    + "-Motion"
        full_address = primary.address + "m";
        super(Motion, self).__init__(parent, full_address, full_name, primary, manifest)
        self.motion_st  = 0
        self.query()

    def query(self, **kwargs):
        """ query the motion status camera """
        # pylint: disable=unused-argument
        self.parent.logger.debug("Motion:query:%s" % (self.name))
        cm = self.primary.get_motion_status()
        if cm != self.motion_st:
            self.motion_st = cm
            self.set_driver('ST', self.motion_st, uom=25, report=True)
        self.parent.logger.debug("Motion:query:%s: ST=%s" % (self.name,self.motion_st))
        if cm == 3:
            return False
        return True

    def motion(self, value):
        """ motion detected on the camera, set the status so we start poling """
        self.motion_st = int(value)
        self.parent.logger.debug("Motion:motion:%s: Motion==%s" % (self.name,self.motion_st))
        self.primary.set_motion_status(self.motion_st)
        return self.set_driver('ST', self.motion_st, uom=25, report=True)

    def poll(self):
        """ 
        poll called by polyglot 
        - If motion is on then query the camera to see if it's still on
        """
        #self.parent.logger.debug("Motion:poll:%s: Motion=%d" % (self.name,self.motion_st))
        if self.motion_st == 1:
            self.parent.logger.info("Motion:poll:%s: Check Motion" % (self.name))
            return self.query()
        return True

    _drivers = {
        'ST': [0, 25, myint],
    }
    """ Driver Details:
    ST: Motion on/off
    """
    _commands = {
        'QUERY': query,
    }
    # The nodeDef id of this camers.
    node_def_id = 'CamMotion'
