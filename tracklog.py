"""
Create tracklog from Water Linked Underwater GPS
"""
import requests
import argparse
import time
import datetime
import gpxpy
import gpxpy.gpx

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

def get_master_position(base_url):
    return get_data("{}/api/v1/position/master".format(base_url))

def _elevation(base_url):
    acoustic_position = get_acoustic_position(base_url)
    if not acoustic_position:
        return None

    depth = acoustic_position["z"]
    return -depth

def create_master_tracklog(gpx, base_url):
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    while True:
        position = get_master_position(base_url)
        if not position:
            log.warning("No master position")
            continue
        latitude = position["lat"]
        longitude = position["lon"]

        print("Master: Latitude: {} Longitude: {}".format(latitude, longitude))
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
            latitude,
            longitude,
            time=datetime.datetime.utcnow()))

        time.sleep(1)

def create_locator_tracklog(gpx, base_url):
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    while True:
        global_position = get_global_position(base_url)
        if not global_position:
            print("No global position")
            continue

        latitude = global_position["lat"]
        longitude = global_position["lon"]
        elevation = _elevation(base_url)

        print("Global: Latitude: {} Longitude: {} Elevation: {}".format(
            latitude,
            longitude,
            elevation))
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
            latitude,
            longitude,
            elevation=elevation,
            time=datetime.datetime.utcnow()))

def main():
    parser = argparse.ArgumentParser(description = (
            "Output global locator GPS track or master GPS track. Default: " +
            "global locator GPS track"))
    parser.add_argument(
        "-u",
        "--url",
        help="URL of UGPS master unit",
        type=str,
        default="https://demo.waterlinked.com")
    parser.add_argument(
        "-o",
        "--output",
        help="File path to use for tracklog output",
        type=str,
        default="tracklog.gpx")
    parser.add_argument(
        "-m",
        "--master",
        action = "store_true",
        help="Output master GPS track instead of locator GPS track")

    args = parser.parse_args()

    base_url = args.url
    output_filepath = args.output

    print(
        "Creating tracklog for UGPS system at {}. " +
        "Press Ctrl-C to stop logging".format(base_url, output_filepath))

    gpx = gpxpy.gpx.GPX()
    try:
        if args.master:
            create_master_tracklog(gpx, base_url)
        else:
            create_locator_tracklog(gpx, base_url)
    except KeyboardInterrupt:
        pass

    print("Saving data to: {}".format(output_filepath))

    with open(output_filepath, "w") as output_file:
        output_file.write(gpx.to_xml())

if __name__ == "__main__":
    main()
