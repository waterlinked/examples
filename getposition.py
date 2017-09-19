from __future__ import print_function
import requests
import json


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
    base_url = "http://37.139.8.112:8000"

    data = get_acoustic_position(base_url)
    if data:
        #print(data)
        print("Current acoustic position {},{},{}".format(data["x"], data["y"], data["z"]))

    pos = get_global_position(base_url)
    if pos:
        #print(pos)
        print("Current global position lat:{} lon:{}".format(pos["lat"], pos["lon"]))



if __name__ == "__main__":
    main()
