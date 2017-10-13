#!/usr/bin/python

import os,sys
from functools import partial
sys.path.insert(0,"../foscam-python-lib")
from foscam import FoscamCamera

ip   = "192.168.1.115"
port = "88"
user = "admin"
password = "somepassword"

camobj = FoscamCamera(ip, port, user, password)

def print_keys(name, rc, params):
    print name
    if rc == 0:
        for k,v in params.items():
            print "  ",k,":",v
    print "\n"
    
camobj.get_ip_info(partial(print_keys,"get_ip_config"));
camobj.get_dev_info(partial(print_keys,"get_dev_info"));
camobj.get_dev_state(partial(print_keys,"get_dev_state"));
camobj.get_infra_led_config(partial(print_keys,"get_infra_led_config"));
camobj.get_product_all_info(partial(print_keys,"get_product_all_info"));
camobj.get_alarm_record_config(partial(print_keys,"get_alarm_record_config"));
camobj.get_local_alarm_record_config(partial(print_keys,"get_local_alarm_record_config"));
camobj.get_h264_frm_ref_mode(partial(print_keys,"get_h264_frm_ref_mode"));
camobj.get_schedule_record_config(partial(print_keys,"get_schedule_record_config"));
camobj.get_ptz_preset_point_list(partial(print_keys,"get_ptz_preset_point_list"));
camobj.ptz_goto_preset("1");

