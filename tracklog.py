from __future__ import print_function
import requests
import argparse
import time
import logging
import gpxpy
import gpxpy.gpx

log = logging.getLogger()
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


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

def get_acoustic_position(base_url):
    return get_data("{}/api/v1/position/acoustic/filtered".format(base_url))


def get_global_position(base_url):
    return get_data("{}/api/v1/position/global".format(base_url))


def main():
    parser = argparse.ArgumentParser(description="Push depth to Underwater GPS")
    parser.add_argument('-u', '--url', help='Base URL to use', type=str, default='http://37.139.8.112:8000')
    parser.add_argument('-o', '--output', help='Output filename', type=str, default='tracklog.gpx')

    args = parser.parse_args()

    base_url = args.url
    filename = args.output
    log.info("Creating tracklog from: {} into file {}. Press Ctrl-C to stop logging".format(base_url, filename))

    gpx = gpxpy.gpx.GPX()

    # Create track
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create segment
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Open file for writing so we don't get an access denied error
    # after a full log session is completed
    f = open(filename, "w")

    try:
        while True:
            pos = get_global_position(base_url)
            if not pos:
                log.warning("Got no global position")
                continue

            lat = pos["lat"]
            lon = pos["lon"]

            acoustic = get_acoustic_position(base_url)
            if not acoustic:
                log.warning("Got no acoustic position")
                continue

            depth = acoustic["z"]
            altitude = -depth

            log.info("Lat: {} Lon: {} Alt: {}".format(lat, lon, altitude))
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=-altitude))

            time.sleep(1)

    except KeyboardInterrupt:
        pass
    print("Saving data to file: {}".format(filename))
    f.write(gpx.to_xml())
    f.close()

if __name__ == "__main__":
    main()
