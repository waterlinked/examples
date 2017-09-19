from __future__ import print_function
import requests
import argparse
import time
import logging

log = logging.getLogger()
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


def set_depth(url, depth, temp):
    payload = dict(depth=depth, temp=temp)
    r = requests.put(url, json=payload, timeout=10)
    if r.status_code != 200:
        log.error("Error setting depth: {} {}".format(r.status_code, r.text))


def main():
    parser = argparse.ArgumentParser(description="Push depth to Underwater GPS")
    parser.add_argument('-u', '--url', help='Base URL to use', type=str, default='http://37.139.8.112:8000')
    parser.add_argument('-d', '--depth', help='Depth to send', type=float, default=0.5)
    parser.add_argument('-t', '--temp', help='Temperature to send', type=float, default=10)
    parser.add_argument('-r', '--repeat', help='Repeat sending with a delay of the given number of seconds', type=int, default=0)

    args = parser.parse_args()

    baseurl = args.url
    log.info("Using baseurl: %s depth: %f temperature %f", args.url, args.depth, args.temp)

    while True:
        log.info('Sending depth')
        set_depth('{}/api/v1/external/depth'.format(baseurl), args.depth, args.temp)

        if args.repeat < 1:
            break

        log.info('Waiting %d seconds', args.repeat)
        time.sleep(args.repeat)


if __name__ == "__main__":
    main()
