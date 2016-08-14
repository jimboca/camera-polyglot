#!/usr/bin/python
#
# Basic script to send UDP requests looking for foscam cameras.
#

import os
import socket
import sys
import time
import select
from struct import unpack,pack

TIMEOUT = 6 # Run for 30 seconds max.
PING_INTERVAL    = 2  # Once every 5 seconds
PING_PORT_NUMBER = 10000
PING_MSG_SIZE    = 130

# ftp://109.108.88.53/Nadzor/FOSCAM/SDK%20CGI/MJPEG%20CGI%20SDK/MJPEG%20CGI%20SDK/Ipcamera%20device%20search%20protocol.pdf
SEARCH_REQUEST = pack(">4sH?8sll4s", "MO_I", 0, 0, "", 67108864, 0, "")

def foscam_poll(logger=None,verbose=False):

    clients = []
    clients_by_addr = {}

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Ask operating system to let us do broadcasts from socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Bind UDP socket to local port so we can receive pings
    sock.bind(('',0)) # Was, PING_PORT_NUMBER, but sender can be any open port.
    # Use timeout
    sock.settimeout(PING_INTERVAL)

    main_timeout = time.time() + TIMEOUT
    responses = {}
    while time.time() < main_timeout:

        # Broadcast our beacon
        if logger is not None:
            logger.info("Pinging for Foscam's")
        sock.sendto(SEARCH_REQUEST, 0, ("255.255.255.255", PING_PORT_NUMBER))
            
        ping_timeout = time.time() + PING_INTERVAL

        while time.time() < ping_timeout:

            # Listen for a response with timeout
            addr = None
            try:
                msg, (addr, uport) = sock.recvfrom(PING_MSG_SIZE)
                # Someone answered our ping, store it.
                if addr not in responses:
                    if logger is not None:
                        logger.info("Saving response from %s:%s" % (addr,uport))
                    responses[addr] = msg
            except socket.timeout:
                if logger is not None:
                    logger.debug("No more reponses")
    sock.close()
    if logger is not None:
        logger.debug("All done looking")

    for addr, msg in responses.iteritems():

        if logger is not None:
            logger.debug("Response from: %s" % (addr))
            if verbose:
                logger.debug("msg=%s" % msg)
            
        if msg == SEARCH_REQUEST:
            if logger is not None:
                logger.debug("ignore my echo")
        elif len(msg) == 88 or len(msg) == 121 or len(msg) == 129:
            if len(msg) == 88:
                upk = unpack('>23s13s21s4I4b4b4bH?',msg)
                (header, id, name, ip_i, mask_i, gateway_i, dns_i, r1, r2, r3, r4, s1, s2, s3, s4, a1, a2, a3, a4, port, dhcp) = upk
                type = ""
            elif len(msg) == 121:
                # I can't find documentation for the last 19 and 14 bytes, but the 14 seems to
                # be a string that indicates what type of camera A=HD and b=H.264
                # I see this for my FI9828P V2
                upk = unpack('>23s13s21s4I4b4b4bH?19s14s',msg)
                (header, id, name, ip_i, mask_i, gateway_i, dns_i, r1, r2, r3, r4, s1, s2, s3, s4, a1, a2, a3, a4, port, dhcp, unknown, type) = upk
            elif len(msg) == 129:
                # And this has has another 8 bytes at the end?  I see this on my FI9826P V2
                upk = unpack('>23s13s21s4I4b4b4bH?19s14s8s',msg)
                (header, id, name, ip_i, mask_i, gateway_i, dns_i, r1, r2, r3, r4, s1, s2, s3, s4, a1, a2, a3, a4, port, dhcp, unknown1, type, unknown2) = upk
            if verbose and logger is not None:
                logger.debug(upk)
            client = {
                'type':      type.rstrip('\x00'),
                'id':        id.rstrip('\x00'),
                'name':      name.rstrip('\x00'),
                'ip':        socket.inet_ntoa(pack('!I',ip_i)),
                'port':      port,
                'mask':      socket.inet_ntoa(pack('!I',mask_i)), 
                'gateway':   socket.inet_ntoa(pack('!I',gateway_i)), 
                'dns':       socket.inet_ntoa(pack('!I',dns_i)), 
                'reserve':   "%d.%d.%d.%d" % (r1, r2, r3, r4),
                'sys':       "%d.%d.%d.%d" % (s1, s2, s3, s4),
                'app':       "%d.%d.%d.%d" % (a1, a2, a3, a4), 
                'dhcp':      dhcp,
                'reserve_a': (r1, r2, r3, r4),
                'sys_a':     (s1, s2, s3, s4),
                'app_a':     (a1, a2, a3, a4),
            }
            if logger is not None:
                logger.info("Foscam Info: %s" % (client))
            clients.append(client)
        else:
            if logger is not None:
                logger.debug("Ignoring message of size " + str(len(msg)))

    return clients

if __name__ == '__main__':
    import logging
    import sys
    # Create our logger
    logger = logging.getLogger('foscam_poll')
    logger.setLevel(logging.DEBUG)
    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)
    verbose = False
    if (len(sys.argv) > 1 and sys.argv[1] == "-v"):
        verbose = True
    foscam_poll(logger,verbose)

    
