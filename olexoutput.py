"""
Read position from Water Linked Underwater GPS convert to use in Olex chart plotter
"""
from __future__ import print_function
from nmeaoutput import get_data, checksum, send_udp, get_master_position
import requests
import argparse
import json
import time
from math import floor
import socket
import sys


def get_acoustic_position(base_url):
    return get_data("{}/api/v1/position/acoustic/filtered".format(base_url))


def gen_ssb(time_t, x, y, z):
    """
    Generate PSIMSBB for Olex  http://www.olex.no/olexiti.html

    Valid sentence:
    $PSIMSSB,180554.432,M44,A,,C,N,M,-61.300,39.017,34.026,0.072,T,0.050576,*47
                1      ,2  ,3 ,5,6,7, 8     , 9    , 10   , 11  ,12,13, crc

    1 = Time
    2 = Name
    3 = A
    4 = Empty
    5 = C - Cartesian
    6 = N/E/H, N=North up, E=East up, H=vessel heading up
    7 = any char, sw-filter: M Measured, F Filtered, P Predicted.
    8 = distance in horizontal plane x (C+H => Starboard)
    9 = distance in horizontal plane y (C+H => Forwards)
    10 = distance in vertical plane depth
    11 = ??
    12 = T??
    13 = ??
    """

    hhmmssss = '%02d%02d%02d%s' % (time_t.tm_hour, time_t.tm_min, time_t.tm_sec, '.%02d' if 0 != 0 else '')
    name = 'UGPS'
    result = 'PSIMSSB,{0},{1},{2},{3},{4},{5},{6},{7:.2f},{8:.2f},{9:.2f},{10},{11},{12}'.format(
        hhmmssss, name, 'A', '', 'C', 'H', 'M', x, y, z, 'T', '', '')
    crc = checksum(result)
    return '$%s*%0.2X' % (result, crc)

def gen_sns(time_t, heading):
    """
    $PSIMSNS,180554.432,M44,1,2,0.0,1.0,2.0,42, ,  ,1.5,  ,  ,*47
                1      ,2  ,3,4,5  , 6 , 7 , 8,9,10, 11,12,13, crc

    1 = Time
    2 = Name
    3 = Transceiver number
    4 = Transducer number
    5 = Roll
    6 = Pitch
    7 = Heave
    8 = Heading
    9 = Tag
    10 = Parameters
    11 = Time age
    12 = Spare1
    13 = Master/Slave
    """
    hhmmssss = '%02d%02d%02d%s' % (time_t.tm_hour, time_t.tm_min, time_t.tm_sec, '.%02d' if 0 != 0 else '')
    name = 'UGPS'
    result = 'PSIMSNS,{0},{1},{2},{3},{4},{5},{6},{7:.1f},{8},{9},{10},{11},{12}'.format(
        hhmmssss, name, '1', '1', '', '', '', heading, '', '', '1.0', '', '')
    crc = checksum(result)
    return '$%s*%0.2X' % (result, crc)


class Sender(object):
    def __init__(self, ser, sock, ip, port, verbose):
        self.ser = ser
        self.sock = sock
        self.ip = ip
        self.port = port
        self.verbose = verbose

    def send(self, sentence):
        if self.verbose:
            print(sentence)
        if self.sock:
            send_udp(self.sock, self.ip, self.port, sentence)
        if self.ser:
            self.ser.write(sentence + "\n")


def main():
    if sys.version_info >= (3, 0):
        sys.stdout.write("This has only been tested with Python 2.x, not Python 3.x\n")
        sys.exit(1)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-u', '--url', help='IP/URL of Underwater GPS kit. Typically http://192.168.2.94', type=str, default='http://demo.waterlinked.com')
    parser.add_argument("-v", "--verbose", help="Print NMEA sentences", action="store_true")
    # UDP options
    parser.add_argument('-i', '--ip', help="Enable UDP output by specifying IP address to send UDP packets. Default disabled", type=str, default='')
    parser.add_argument('-p', '--port', help="Port to send UDP packet", type=int, default=5000)
    # Serial port options
    parser.add_argument('-s', '--serial', help="Enable serial port output by specifying port to use. Example: '/dev/ttyUSB0' or 'COM1' Default disabled", type=str, default='')
    parser.add_argument('-b', '--baud', help="Serial port baud rate", type=int, default=9600)
    args = parser.parse_args()

    if not (args.ip or args.serial):
        parser.print_help()
        print("ERROR: Please specify either serial port to use, ip address to use")
        sys.exit(1)

    print("Using base_url: {}".format(args.url))

    ser = None
    if args.serial:
        import serial
        print("Serial port: {}".format(args.serial))
        ser = serial.Serial(args.serial, args.baud)

    sock = None
    if args.ip:
        print("UDP: {} {}".format(args.ip, args.port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sender = Sender(ser, sock, args.ip, args.port, args.verbose)

    while True:
        pos = get_acoustic_position(args.url)

        if pos:
            sentence = gen_ssb(time.gmtime(), pos["x"], pos["y"], pos["z"])
            sender.send(sentence)

        master = get_master_position(args.url)
        if master:
            sentence = gen_sns(time.gmtime(), master["orientation"])
            sender.send(sentence)

        time.sleep(0.2)


if __name__ == "__main__":
    main()
