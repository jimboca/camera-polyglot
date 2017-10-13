
import os,socket,struct

def myint(value):
    """ round and convert to int """
    return int(round(float(value)))

def myfloat(value, prec=4):
    """ round and return float """
    return round(float(value), prec)

# from http://commandline.org.uk/python/how-to-find-out-ip-address-in-python/
def get_network_ip(rhost):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((rhost, 0))
    return s.getsockname()[0]

def ip2long(ip):
    """ Convert an IP string to long """
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]

def long2ip(value):
    return socket.inet_ntoa(struct.pack('!L', value))


# isBit() returns True or False if bit at offset is set or not
def isBit(int_type, offset):
    mask = 1 << offset
    if (int_type & mask) == 0:
        return False
    return True

# isBit() returns 1 or 0 if bit at offset is set or not
def isBitI(int_type, offset):
    mask = 1 << offset
    if (int_type & mask) == 0:
        return 0
    return 1

# testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
def testBit(int_type, offset):
    mask = 1 << offset
    return(int_type & mask)

# setBit() returns an integer with the bit at 'offset' set to 1.
def setBit(int_type, offset):
    mask = 1 << offset
    return(int_type | mask)

# clearBit() returns an integer with the bit at 'offset' cleared.
def clearBit(int_type, offset):
    mask = ~(1 << offset)
    return(int_type & mask)

# toggleBit() returns an integer with the bit at 'offset' inverted, 0 -> 1 and 1 -> 0.
def toggleBit(int_type, offset):
    mask = 1 << offset
    return(int_type ^ mask)

def str2bool(value):
    """
    Args:
        value - text to be converted to boolean
         True values: y, yes, true, t, on, 1
         False values: n, no, false, off, 0
    """
    try:
        if isinstance(value, (str, unicode)):
            return bool(util.strtobool(value))
    except NameError:  # python 3
        if isinstance(value, str):
            return bool(util.strtobool(value))
    return bool(value)

def bool2int(value):
    if value:
        return 1
    else:
        return 0

def int2str(value):
    if int(value) == 0:
        return "false"
    else:
        return "true"

def str2int(value):
    return bool2int(str2bool(value))
