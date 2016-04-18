
import os,socket,struct

def myint(value):
    """ round and convert to int """
    return int(round(float(value)))

def myfloat(value, prec=4):
    """ round and return float """
    return round(float(value), prec)

def ip2long(ip):
    """ Convert an IP string to long """
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]

def long2ip(value):
    return socket.inet_ntoa(struct.pack('!L', value))
    
