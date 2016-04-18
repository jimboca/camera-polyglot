""" Node classes used by the ISY Helper Camera Node Server. """

from polyglot.nodeserver_api import Node
from functools import partial
#import json
#import urllib2


def myint(value):
    """ round and convert to int """
    return int(round(float(value)))

def myfloat(value, prec=4):
    """ round and return float """
    return round(float(value), prec)


from .FoscamMJPEG import FoscamMJPEG
from .CameraServer import CameraServer
