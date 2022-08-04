"""
Read position from Water Linked Underwater GPS, convert to an NMEA sentence,
and send to either a serial port, a UDP socket, or a virtual port
"""
import argparse
import datetime
import json
import math
import os
import requests
import signal
import socket
import subprocess
import sys
import time

def get_data(url, stderr=False):
    try:
        r = requests.get(url, timeout=0.2)
    except requests.exceptions.RequestException as exc:
        if stderr:
            print("Exception occured {}".format(exc))
        return None

    if r.status_code != requests.codes.ok:
        if stderr:
            print("Got error {}: {}".format(r.status_code, r.text))
        return None

    return r.json()

def get_global_position(base_url):
    return get_data("{}/api/v1/position/global".format(base_url))

def get_acoustic_position(base_url):
    return get_data("{}/api/v1/position/acoustic/filtered".format(base_url))

def get_master_position(base_url):
    return get_data("{}/api/v1/position/master".format(base_url))

def checksum(sentence):
    """Calculate and return checsum for given NMEA sentence"""
    crc = 0
    for c in sentence:
        crc = crc ^ ord(c)
    crc = crc & 0xFF
    return crc

def gen_gga(parameters, dgps_age_sec=None, dgps_ref_id=None):
    # Code is adapted from https://gist.github.com/JoshuaGross/d39fd69b1c17926a44464cb25b0f9828
    now = parameters["timestamp"]
    timestamp = "{:.2f}".format(
         float(now.strftime("%H%M%S.%f")))

    lat_abs = abs(parameters["latitude"])
    lat_deg = lat_abs
    lat_min = (lat_abs - math.floor(lat_deg)) * 60
    lat_sec = round((lat_min - math.floor(lat_min)) * 1000)
    lat_pole_prime = 'S' if parameters["latitude"] < 0 else 'N'
    lat_format = '%02d%02d.%03d' % (lat_deg, lat_min, lat_sec)

    lng_abs = abs(parameters["longitude"])
    lng_deg = lng_abs
    lng_min = (lng_abs - math.floor(lng_deg)) * 60
    lng_sec = round((lng_min - math.floor(lng_min)) * 1000)
    lng_pole_prime = 'W' if parameters["longitude"] < 0 else 'E'
    lng_format = '%03d%02d.%03d' % (lng_deg, lng_min, lng_sec)

    dgps_format = '%s,%s' % ('%.1f' % dgps_age_sec if dgps_age_sec is not None else '', '%04d' % dgps_ref_id if dgps_ref_id is not None else '')

    result = 'GPGGA,%s,%s,%s,%s,%s,%d,%02d,%.1f,%.1f,M,,M,%s' % (
        timestamp,
        lat_format,
        lat_pole_prime,
        lng_format,
        lng_pole_prime,
        parameters["fix_quality"],
        parameters["number_of_satellites"],
        parameters["horizontal_dilution_of_precision"],
        parameters["altitude"],
        dgps_format)
    crc = checksum(result)

    return '$%s*%0.2X\r\n' % (result, crc)


def send_udp(sock, ip, port, message):
    sock.sendto(message.encode(), (ip, port))


class VirtualPort:
    """
    Create a virtual port in the computer. Valid for linux with socat installed.
    """
    def __init__(self, password, origin='/dev/ttyS8', end='/dev/ttyS9'):
        self.origin = origin
        self.end=end
        self.p = subprocess.Popen(['/bin/bash', '-c', 'echo %s|sudo -S sudo socat PTY,link=%s PTY,link=%s' % (password, self.origin, self.end)], preexec_fn=os.setpgrp)
        time.sleep(1)  # Wait for process to start
        subprocess.call(['/bin/bash', '-c', 'echo %s|sudo -S sudo chmod 666 %s' % (password, self.origin)])
        subprocess.call(['/bin/bash', '-c', 'echo %s|sudo -S sudo chmod 666 %s' % (password, self.end)])
        return

    def stop(self):
        os.killpg(self.p.pid, signal.SIGTERM)
        return

    def write(self, message):
        message = "echo \"" + message + "\" > " + self.origin
        subprocess.call(["/bin/bash", "-c", message])
        return

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-u', '--url', help='IP/URL of Underwater GPS kit. Typically http://192.168.2.94', type=str, default='http://demo.waterlinked.com')
    parser.add_argument('-m', '--master', help='Print master position instead of global', action="store_true")
    parser.add_argument("-v", "--verbose", help="Print NMEA sentences", action="store_true")
    # UDP options
    parser.add_argument('-i', '--ip', help="Enable UDP output by specifying IP address to send UDP packets. Default disabled", type=str, default='')
    parser.add_argument('-p', '--port', help="Port to send UDP packet", type=int, default=5000)
    # Serial port options
    parser.add_argument('-s', '--serial', help="Enable serial port output by specifying port to use. Example: '/dev/ttyUSB0' or 'COM1'. Default: disabled", type=str, default='')
    parser.add_argument('-b', '--baud', help="Serial port baud rate", type=int, default=9600)
    # Virtual port options
    parser.add_argument('-w', '--password', help='Password to execute sudo commands', type=str, default='')
    parser.add_argument('-o', '--origin', help='Virtual port to write to', type=str, default='/dev/ttyS7')
    parser.add_argument('-e', '--end', help='Virtual port to read from', type=str, default='/dev/ttyS9')
    args = parser.parse_args()

    if not (args.ip or args.serial or args.password):
        parser.print_help()
        print("ERROR: Please specify either serial port to use, IP address to use, or a password to create a virtual port")
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

    virtualPort = None
    if args.password:
        print("Sending data from virtual port '{}' to '{}'".format(args.origin, args.end))
        virtualPort = VirtualPort(args.password, args.origin, args.end)

    while True:
        if args.master:
            pos = get_master_position(args.url)
            if not pos:
                continue
            parameters = {
                "timestamp": datetime.datetime.utcnow(),
                "latitude": pos["lat"],
                "longitude": pos["lon"],
                "fix_quality": pos["fix_quality"],
                "number_of_satellites": pos["numsats"],
                "horizontal_dilution_of_precision": pos["hdop"],
                "altitude": 0,
            }
        else:
            global_position = get_global_position(args.url)
            acoustic_position = get_acoustic_position(args.url)
            if (not global_position) or (not acoustic_position):
                continue
            parameters = {
                "timestamp": datetime.datetime.utcnow(),
                "latitude": global_position["lat"],
                "longitude": global_position["lon"],
                "fix_quality": global_position["fix_quality"],
                "number_of_satellites": global_position["numsats"],
                "horizontal_dilution_of_precision": global_position["hdop"],
                "altitude": -float(acoustic_position["z"]),
            }
        sentence = gen_gga(parameters)
        if args.verbose:
            print(sentence)
        if sock:
            send_udp(sock, args.ip, args.port, sentence.encode("utf-8"))
        if ser:
            ser.write(sentence)
        if virtualPort:
            #Add \ to make the simbol $ writable
            dollar_sentence = '\\' + sentence
            virtualPort.write(dollar_sentence)
        time.sleep(0.2)

if __name__ == "__main__":
    main()
