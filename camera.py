#!/usr/bin/python
#
# Install:
#  sudo pip install ipaddr
# Issues:
#  - Once the node is registered, it's name will not change.
#
# Auth Issues:
#  - Needs basic auth:  11.37.2.52
#  - Uses digest auth:  11.37.2.59
#
""" Camera Node Server for ISY """

try:
    from httplib import BadStatusLine  # Python 2.x
except ImportError:
    from http.client import BadStatusLine  # Python 3.x
from polyglot.nodeserver_api import SimpleNodeServer, PolyglotConnector
from collections import defaultdict, OrderedDict
import os, json, logging, requests, threading, SocketServer, re, socket, yaml
from requests.auth import HTTPDigestAuth,HTTPBasicAuth
# Is there a better way to import these?  I'd rather import just this:
import camera_nodes
# And have all camera_nodes defined at the current level?  But have to import them all?
from camera_nodes import CameraServer

from camera_polyglot_version import VERSION

global _REST_HANDLER

class CameraNodeServer(SimpleNodeServer):
    """ ISY Helper Camera Node Server """
    global _REST_HANDLER
    
    def setup(self):
        """ Initial node setup. """
        super(SimpleNodeServer, self).setup()
        self.logger.info('CameraNodeServer: Version=%s starting up.' % (VERSION))
        self.logger.info("CameraNodeServer: Sandbox=%s" % (self.poly.sandbox))
        self.logger.info("CameraNodeServer: Config=%s" % (self.config))
        # Setup the config data.
        self.get_cam_config()
        # define nodes for settings
        # Start a simple server for cameras to ping
        self.server = start_server(self)
        self.manifest = self.config.get('manifest', {})
        # Add the top level camera server node.
        CameraServer(self, "cams", "Camera Server", self.manifest)
        self.update_config()

    def get_cam_config(self):
        """
        Read the sandbox/config.yaml.
        If it does not exist, create a blank template
        Make sure necessary settings are set
        """
        # The config file.
        self.config_file = self.poly.sandbox + "/config.yaml"
        # Default configuration paramaters.
        default_config = dict(
            user = 'YourCameraUserName',
            password = 'YourCameraPassword'
        )
        if not os.path.isfile(self.config_file):
            with open(self.config_file, 'w') as outfile:
                outfile.write( yaml.dump(default_config, default_flow_style=False) )
                msg = 'Created default config file, please edit and set the proper values "%s"' % (self.config_file)
                self.logger.error(msg)
                raise IOError(msg)
        try:
            config_h = open(self.config_file, 'r')
        except IOError as e:
            # Does not exist OR no read permissions, so show error in both logs.
            msg = 'Error Unable to open config file "%s"' % (self.config_file)
            self.logger.error(msg)
            raise IOError(msg)
        # TODO: Ok to just let load errors throw an exception?
        self.cam_config = yaml.load(config_h)
        config_h.close
        # Check that user and password are defined.
        errors = 0
        for param in ('user', 'password'):
            if not param in self.cam_config:
                self.logger.error("%s not defined in %s" % (param,self.config_file))
                errors += 1
            elif self.cam_config[param] is None:
                self.logger.error("%s is %s in %s" % (param,self.cam_config[param],self.config_file))
                errors += 1
        if errors > 0:
            raise ValueError('Error in config file "%s", see log "%s"' % (self.config_file, self.poly.log_filename))
        
    def poll(self):
        """ Poll Camera's  """
        for node_addr, node in self.nodes.items():
            node.poll()
        return True

    def long_poll(self):
        """ Call long_poll on all nodes and Save configuration every 30 seconds. """
        self.logger.debug("CameraNodeServer:long_poll")
        self.update_config()
        for node_addr, node in self.nodes.items():
            node.long_poll()
        return True

    def on_exit(self, **kwargs):
        self.server.socket.close()
        return True

    def send_error(self,error_str):
        self.logger.error(error_str)
        self.poly.send_error(error_str);
        
    def motion(self,address,value):
        """ Poll Camera's  """
        self.logger.info("Got Motion for node %s '%s'" % (address, value) )
        if address in self.nodes:
            return self.nodes[address].motion(value)
        else:
            self.send_error("No node for motion on address %s" % (address));
        return False
    
    def http_get(self,ip,port,user,password,path,payload,auth_mode=0):
        url = "http://{}:{}/{}".format(ip,port,path)
        self.logger.debug("http_get: Sending: %s %s auth_mode=%d" % (url, payload, auth_mode) )
        if auth_mode == 0:
            auth = HTTPBasicAuth(user,password)
        elif auth_mode == 1:
            auth = HTTPDigestAuth(user,password)
        else:
            self.send_error("Unknown auth_mode '%s' for request '%s'.  Must be 0 for 'digest' or 1 for 'basic'." % (auth_mode, url) )
            return False
            
        try:
            response = requests.get(
                url,
                auth=auth,
                params=payload,
                timeout=10
            )
        # This is supposed to catch all request excpetions.
        except requests.exceptions.RequestException as e:
            self.send_error("Connection error for %s: %s" % (url, e))
            return False
        self.logger.debug("http_get: Got: code=%s", response.status_code)
        if response.status_code == 200:
            #self.logger.debug("http_get: Got: text=%s", response.text)
            return response.text
        elif response.status_code == 400:
            self.send_error("Bad request: %s" % (url) )
        elif response.status_code == 404:
            self.send_error("Not Found: %s" % (url) )
        elif response.status_code == 401:
            # Authentication error
            self.send_error(
                "Failed to authenticate, please check your username and password")
        else:
            self.send_error("Unknown response %s: %s" % (response.status_code, url) )
        return False

class EchoRequestHandler(SocketServer.BaseRequestHandler):
    
    def handle(self):
        # Echo the back to the client
        data = self.request.recv(1024)
        # Don't worry about a status for now, just echo back.
        self.request.sendall(data)
        # Then parse it.
        myhandler(data)
        return

def get_network_ip(rhost):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((rhost, 0))
        return s.getsockname()[0]
    except:
        _SERVER.poly.send_error("get_network_ip: Failed to open socket to " + rhost)
        return False

def start_server(handler):
    global _REST_HANDLER
    myip = get_network_ip('8.8.8.8')
    address = (myip, 0) # let the kernel give us a port
    _REST_HANDLER = handler;
    server = SocketServer.TCPServer(address, EchoRequestHandler)
    #print "Running on: %s:%s" % server.server_address
    t = threading.Thread(target=server.serve_forever)
    #t.setDaemon(True) # don't hang on exit
    t.start()
    return server

def myhandler(data):
    #print "got: {}".format(data.strip())
    match = re.match( r'GET /motion/(.*) ', data, re.I)
    if match:
        address = match.group(1)
        _REST_HANDLER.motion(address,1)
    else:
        _REST_HANDLER.poly.send_error("Unrecognized socket server command: " + data)

def main():
    """ setup connection, node server, and nodes """
    poly = PolyglotConnector()
    nserver = CameraNodeServer(poly)
    poly.connect()
    poly.wait_for_config()
    nserver.setup()
    nserver.run()


if __name__ == "__main__":
    main()
