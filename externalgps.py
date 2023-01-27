'''
Push external GNSS data to Water Linked Underwater GPS
"cog": the actual direction of progress of a vessel, between two points,
      with respect to the surface of the earth
"fix_quality": 1 - > Position is gathered only form GNSS satellites ,
"hdop": 1.9,
"lat": 63.422,
"lon": 10.424,
"numsats": 11 -> number of satellites
"orientation": 42,
"sog": 0.5

'''
import requests
import argparse
import time
import logging

log = logging.getLogger()
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


def set_master(url, cog, fix_quality, hdop, lat, long,
                numsats, orientation, sog):
  payload = dict(cog = cog, fix_quality = fix_quality, hdop = hdop,
                  lat = lat, long = long, numsats = numsats,
                  orientation = orientation,
                  sog = sog)

  r = requests.put(url, json=payload, timeout=10)
  if r.status_code != 200:
    log.error("Error setting gps data: {} {}".format(r.status_code, r.text))

# demo.waterlinked.com
def main():

  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('-u', '--url', help='Base URL to use', type=str,\
                      default='http://192.168.7.1')
  parser.add_argument('-c', '--cog', help='cog to send', type=float,\
                      default=42)
  parser.add_argument('-f', '--fix_quality', help='fix_quality to send',\
                      type=float, default=1)
  parser.add_argument('-h', '--hdop', help='hdop to send',\
                      type=float, default=1.9)
  parser.add_argument('-l', '--lat', help='latitude to send',\
                      type=float, default=10)
  parser.add_argument('-g', '--long', help='longitude to send',\
                      type=float, default=10)
  parser.add_argument('-n', '--numsats', help='numsats to send',\
                      type=float, default=11)
  parser.add_argument('-o', '--orientation', help='orientation to send',\
                      type=float, default=42)
  parser.add_argument('-s', '--sog', help='sog to send',\
                      type=float, default=0.5)

  parser.add_argument('-r', '--repeat', help='Repeat sending with a delay of\
                      the given number of seconds', type=int, default=1)

  args = parser.parse_args()

  baseurl = args.url

  log.info("Using baseurl: %s depth: %f temperature %f", args.url,\
            args.depth, args.temp)

  while True:
    log.info('Sending depth')

    set_master('{}/api/v1/external/master'.format(baseurl),
                args.cog, args.fix_quality, args.hdop, args.lat,
                args.long,
                args.numsats, args.orientation, args.sog)

    if args.repeat < 1:
        break

    log.info('Waiting %d seconds', args.repeat)
    time.sleep(args.repeat)


if __name__ == "__main__":
  main()  
