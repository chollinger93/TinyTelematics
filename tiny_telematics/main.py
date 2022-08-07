from gps import *
import platform
import json
import uuid


class Record:
    def __init__(self, lat, long, altitude, timestamp, speed):
        self.lat = lat
        self.long = long
        self.altitude = altitude
        self.timestamp = timestamp
        self.speed = speed
        self.id = hex(uuid.getnode())

    def __str__(self):
        return str(json.dumps(self.__dict__))

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def poll_gps(_gpsd, batch=128):
    print("Starting GPS poll, batch: {}".format(batch))
    data = []
    i = 0
    while True:
        report = _gpsd.next()
        # TPV - Time Position Velocity
        if report["class"] == "TPV":
            # Get data
            lat = getattr(report, "lat", 0.0)
            long = getattr(report, "lon", 0.0)
            time = getattr(report, "time", "")
            altitude = getattr(report, "alt", "nan")
            speed = getattr(report, "speed", "nan")
            record = Record(lat, long, altitude, time, speed)
            data.append(json.dumps(record.__dict__))
            if i >= batch:
                # push_to_iot_core(data)
                # TODO: push
                data = []
                i = 0
            else:
                i += 1


if __name__ == "__main__":
    # Start
    gpsd = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)

    print("Starting...")
    poll_gps(gpsd, 25)
