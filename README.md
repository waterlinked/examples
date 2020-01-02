# Water Linked Underwater GPS API examples

## Requirements

* Python 2.7 (http://python.org)
* pip (https://pip.pypa.io/en/stable/installing/)

## Installation

Install the required Python packages

```
pip install -r requirements.txt
```

## About

Example applications using the Water Linked Underwater GPS API. See http://waterlinked.com for more details.
The example applications are set up to use the Water Linked Demo Server by default and should be changed
to the IP address/port of your kit. (For example: http://192.168.2.94)

### About nmeaoutput.py

Generate NMEA sentences (GGA) from the global/locator position (lat, lon) and output it to either UDP or Serial port.

### About nmeainput.py

Parse NMEA sentences (GGA/HDT) from either UDP or Serial and send to Underwater GPS kit to use as global reference system instead of the on-board
GPS and IMU. The Underwater GPS kit must be configured to use "External" GPS / Compass.

NOTE: If you just want NMEA input/output with easier installation take a look at: https://github.com/waterlinked/ugps-nmea-go

### About getposition.py

Example of how to get both global (lat/lon) and relative position (x,y,z) from the Water Linked Underwater GPS.

### About externaldepth.py

Example of how to send external depth data to the Water Linked Underwater GPS. This is needed when
using the Locator A1 and is typically part of ROV integration

### About tracklog.py

Example of how to store positions into a tracklog while the system is running into a [GPX file](https://en.wikipedia.org/wiki/GPS_Exchange_Format) for later viewing or processing.
