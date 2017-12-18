from __future__ import print_function
import requests
import argparse
import time
import logging
import sys
import serial
import pynmea2


log = logging.getLogger()
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def set_position_master(url, latitude, longitude, orientation):
    payload = dict(lat=latitude, lon=longitude, orientation=orientation)
    r = requests.put(url, json=payload, timeout=10)
    if r.status_code != 200:
        log.error("Error setting position and orientation: {} {}".format(r.status_code, r.text))
        
        
def main():
    parser = argparse.ArgumentParser(description="Push position and orientation of master to Underwater GPS")
    parser.add_argument('-u', '--url', help='Base URL to use', type=str, default='http://demo.waterlinked.com')
    parser.add_argument('-d', '--source', help='Device to read nmea strings from', type=str, default='/dev/ttyUSB0')
    args = parser.parse_args()

    baseurl = args.url
    log.info("Using baseurl: %s source: %s", args.url, args.source)

    reader = pynmea2.NMEAStreamReader()
    com  = args.source

    try:
        com = serial.Serial(args.source, timeout=5.0)
    except serial.SerialException:
        log.warning('Could not connect to %s', args.source)
        log.warning("Exiting")
        sys.exit()

    lat = 0
    lon = 0
    orientation = 0
    gotUpdate = False
        
    while True:

        try:
          data = com.read()
          for msg in reader.next(data):
            if type(msg) == pynmea2.types.talker.GGA:
                lat = msg.latitude
                lon = msg.longitude
                gotUpdate = True
                
            elif type(msg) == pynmea2.types.talker.HDT:
                orientation = msg.heading
                gotUpdate = True
            
        except pynmea2.ParseError as e:
            log.warning("Error while parsing NMEA string: {}".format(e))

        if gotUpdate:
            log.info('Sending position and orientation')
            set_position_master('{}/api/v1/external/master'.format(baseurl), lat, lon, orientation)
            gotUpdate = False


if __name__ == "__main__":
    main()
