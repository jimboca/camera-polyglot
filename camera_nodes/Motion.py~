
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

    def query(self, **kwargs):
        """ query the camera """
        # pylint: disable=unused-argument
        self.parent.logger.info("Motion:query:start: '%s'" % (self.name))
        self.primary._get_status()
        # TODO: Should report only be true if it changes?
        self.set_driver('ST', self.primary.status['alarm_status'], report=True)
        self.parent.logger.info("Motion:query:done: '%s'" % (self.name))
        return True

    def motion(self, value):
        """ query the camera """
        self.parent.logger.info("Motion: Seting alarm status of '%s' to %s" % (self.name,value))
        self.primary.status['alarm_status'] = value
        return self.set_driver('ST', value, report=True)

    def poll(self):
        """ Poll Motion  """
        # TODO: This should get the driver status
        # TODO: This seems to bang on the camera twice per run?
        if int(self.primary.status['alarm_status']) > 0:
            self.parent.logger.info("Motion: Check alarm status of '%s'" % (self.name))
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
