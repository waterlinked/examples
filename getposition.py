"""
Get position from Water Linked Underwater GPS
"""
import argparse
import json
import requests

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

def get_antenna_position(base_url):
    return get_data("{}/api/v1/config/antenna".format(base_url))

def get_acoustic_position(base_url):
    return get_data("{}/api/v1/position/acoustic/filtered".format(base_url))

def get_global_position(base_url, acoustic_depth = None):
    return get_data("{}/api/v1/position/global".format(base_url))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-u",
        "--url",
        help = "Base URL to use",
        type = str,
        default = "https://demo.waterlinked.com")
    parser.add_argument(
        "-a",
        "--antenna",
        action = "store_true",
        help = (
            "Use mid-point of base of antenna as origin for the acoustic " +
            "position. Default origin is the point at sea level directly " +
            "below/above that which the positions of the receivers/antenna " +
            "are defined with respect to"))
    args = parser.parse_args()

    base_url = args.url
    print("Using base_url: %s" % args.url)

    acoustic_position = get_acoustic_position(base_url)
    antenna_position = None
    if args.antenna:
        antenna_position = get_antenna_position(base_url)
    depth = None
    if acoustic_position:
        if antenna_position:
            print(acoustic_position)
            print(antenna_position)
            print("Current acoustic position relative to antenna. X: {}, Y: {}, Z: {}".format(
                acoustic_position["x"] - antenna_position["x"],
                acoustic_position["y"] - antenna_position["y"],
                acoustic_position["z"] - antenna_position["depth"]))
        else:
            print("Current acoustic position. X: {}, Y: {}, Z: {}".format(
                acoustic_position["x"],
                acoustic_position["y"],
                acoustic_position["z"]))
        depth = acoustic_position["z"]

    global_position = get_global_position(base_url)
    if global_position:
        if depth:
            print("Current global position. Latitude: {}, Longitude: {}, Depth: {}".format(
                global_position["lat"],
                global_position["lon"],
                depth))
        else:
            print("Current global position latitude :{} longitude :{}".format(
                global_position["lat"],
                global_position["lon"]))

if __name__ == "__main__":
    main()
