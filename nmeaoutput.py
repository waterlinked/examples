"""
Read position from Water Linked Underwater GPS convert to NMEA and send to serial
port or on UDP socket
"""
from __future__ import print_function
import requests
import argparse
import json
import time
from math import floor
import socket
import serial
import sys

def get_data(url):
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as exc:
        print("Exception occured {}".format(exc))
        return None

    if r.status_code != requests.codes.ok:
        print("Got error {}: {}".format(r.status_code, r.text))
        return None

    return r.json()

def get_global_position(base_url):
    return get_data("{}/api/v1/position/global".format(base_url))

def gen_gga(time_t, lat, lng, fix_quality, num_sats, hdop, alt_m, geoidal_sep_m, dgps_age_sec=None, dgps_ref_id=None):
    # Code is adapted from https://gist.github.com/JoshuaGross/d39fd69b1c17926a44464cb25b0f9828
    hhmmssss = '%02d%02d%02d%s' % (time_t.tm_hour, time_t.tm_min, time_t.tm_sec, '.%02d' if 0 != 0 else '')

    lat_abs = abs(lat)
    lat_deg = lat_abs
    lat_min = (lat_abs - floor(lat_deg)) * 60
    lat_sec = round((lat_min - floor(lat_min)) * 1000)
    lat_pole_prime = 'S' if lat < 0 else 'N'
    lat_format = '%02d%02d.%03d' % (lat_deg, lat_min, lat_sec)

    lng_abs = abs(lng)
    lng_deg = lng_abs
    lng_min = (lng_abs - floor(lng_deg)) * 60
    lng_sec = round((lng_min - floor(lng_min)) * 1000)
    lng_pole_prime = 'W' if lng < 0 else 'E'
    lng_format = '%03d%02d.%03d' % (lng_deg, lng_min, lng_sec)

    dgps_format = '%s,%s' % ('%.1f' % dgps_age_sec if dgps_age_sec is not None else '', '%04d' % dgps_ref_id if dgps_ref_id is not None else '')

    result = 'GPGGA,%s,%s,%s,%s,%s,%d,%02d,%.1f,%.1f,M,%.1f,M,%s' % (hhmmssss, lat_format, lat_pole_prime, lng_format, lng_pole_prime, fix_quality, num_sats, hdop, alt_m, geoidal_sep_m, dgps_format)
    crc = 0
    for c in result:
        crc = crc ^ ord(c)
    crc = crc & 0xFF

    return '$%s*%0.2X' % (result, crc)


def send_udp(sock, ip, port, message):
    sock.sendto(message, (ip, port))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-u', '--url', help='IP/URL of Underwater GPS kit. Typically http://192.168.2.94', type=str, default='http://demo.waterlinked.com')
    # UDP options
    parser.add_argument('-i', '--ip', help="Enable UDP output by specifying IP address to send UDP packets. Default disabled", type=str, default='')
    parser.add_argument('-p', '--port', help="Port to send UDP packet", type=int, default=5000)
    # Serial port options
    parser.add_argument('-s', '--serial', help="Enable serial port output by specifying port to use. Example: '/dev/ttyUSB0' or 'COM1' Default disabled", type=str, default='')
    parser.add_argument('-b', '--baud', help="Serial port baud rate", type=int, default=9600)
    args = parser.parse_args()

    if not (args.ip or args.serial):
        parser.print_help()
        print("ERROR: Please specify either serial port to use or ip address to use")
        sys.exit(1)

    print("Using base_url: {}. Serial {}. UDP: {} {}".format(
        args.url,
        args.serial or "disabled",
        args.ip or "disabled",
        args.port if args.ip else ""))

    ser = None
    if args.serial:
        ser = serial.Serial(args.serial, args.baud)

    sock = None
    if args.ip:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        pos = get_global_position(args.url)
        if pos:
            #print("Current global position lat:{} lon:{}".format(pos["lat"], pos["lon"]))
            sentence = gen_gga(time.gmtime(), pos["lat"], pos["lon"], 0, 0, 0, 0, 0)
            print(sentence)
            if sock:
                send_udp(sock, args.ip, args.port, sentence)
            if ser:
                ser.wrote(sentence + "\n")
            time.sleep(0.2)


if __name__ == "__main__":
    main()
