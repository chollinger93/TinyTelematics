from asyncio import subprocess
from datetime import datetime
from typing import Generator, List, Generic, NewType, Optional, TypeVar
from collections import deque
from gps import gps as GpsClient
from gps import WATCH_ENABLE, WATCH_NEWSTYLE
import json
import uuid
import time
from redis import Redis as RedisClient
from kafka import KafkaProducer
import jsonpickle
import subprocess
from geopy import distance
import statistics

# Model (also types)
class GpsRecord:
    def __init__(
        self, lat: float, lon: float, altitude: float, speed: float, timestamp=datetime.now()):
        self.lat = lat
        self.lon = lon
        self.altitude = altitude
        self.timestamp = timestamp.timestamp
        self.speed = speed
        self.id = hex(uuid.getnode())

    def __str__(self):
        return str(json.dumps(self.__dict__))

    def to_json(self):
        return jsonpickle.encode(self)


# Types
T = TypeVar("T")
NonEmptyGpsRecordList = NewType("NonEmptyGpsRecordList", List[GpsRecord])


def poll_gps(gps_client: GpsClient) -> Optional[GpsRecord]:
    """Poll the GPS sensor for a record

    Args:
        gps_client (GpsClient): GPS Client

    Returns:
        Optional[GpsRecord]: Might be not available
    """
    while True:
        report = gps_client.next()
        # TPV - Time Position Velocity
        # Returns a dictwrapper with various readings; we only need TPV
        if report["class"] == "TPV":
            # Get data
            lat = getattr(report, "lat", 0.0)
            long = getattr(report, "lon", 0.0)
            altitude = getattr(report, "alt", -1)
            speed = getattr(report, "speed", -1)
            return GpsRecord(lat, long, altitude, speed, datetime.now())


def write_cache(client: RedisClient, records: NonEmptyGpsRecordList) -> int:
    """Writes to the cache.

    Has side effects!

    Args:
        client (RedisClient): Redis client
        NonEmptyList (NonEmptyList[GpsRecord]): Non empty list of GPS readings

    Returns:
        IO[Unit]
    """
    return client.rpush("buffer", list(map(lambda r: r.to_json(), records)))


def read_cache(client: RedisClient) -> Generator[GpsRecord, None, None]:
    """Reads from the redis cache, returning all records that have been buffered.

    Has side effects!

    Args:
        client (RedisClient): Redis client

    Yields:
        Generator[GpsRecord]: One record at a time, non-empty, non-null
    """
    for r in client.lrange("buffer", 0, -1):
        yield jsonpickle.decode(r)


def publish_data(producer: KafkaProducer, topic: str, record: GpsRecord) -> None:
    """Publishes data to Kafka

    Args:
        client (KafkaProducer): KafkaProducer
        record (GpsRecord): Data to publish

    Returns:
        IO[Unit]
    """
    producer.send(
        topic,
        key=record.id.encode("utf-8"),
        value=jsonpickle.encode(record).encode("utf-8"),
    )


def is_network_available(expected_network: str) -> bool:
    try:
        return (
            subprocess.check_output(["iwgetid", "-r"]).decode("ascii").replace("\n", "")
            == expected_network
        )
    except Exception as e:
        print(e) # TODO logger
        return False


def calculate_distance_in_m(x, y: GpsRecord) -> float:
    return distance.distance((x.lat,x.lon),(y.lat,y.lon)).meters


def movement_has_changed_during_observation(
    records: List[GpsRecord], threshold_m: float
) -> bool:
    _distances = []
    for xm0, x0 in zip(records, records[1:]):
        dist_m = calculate_distance_in_m(xm0, x0)
        _distances.append(dist_m)
    print(statistics.mean(_distances)) # TODO: log
    return statistics.mean(_distances) >= threshold_m

def main(
    gps_client: GpsClient,
    redis_client: RedisClient,
    kafka_producer: KafkaProducer,
    kafka_topic: str,
    expected_network: str,
    buffer_size=10,
    max_no_movement_s=300,
) -> None:
    ring_buffer: deque[GpsRecord] = deque(maxlen=max_no_movement_s)
    while True:
        # Flush data when you can
        if is_network_available(expected_network):
            for r in read_cache(redis_client):
                publish_data(kafka_producer, kafka_topic, r)
            # If we're at a standstill, shut down after N minutes
            if movement_has_changed_during_observation(
                list(ring_buffer), threshold_m=0.1
            ):
                break
        # With or without network, we just collect data
        _buffer: NonEmptyGpsRecordList = NonEmptyGpsRecordList(item=[])
        if len(_buffer) - 1 >= buffer_size:
            # Flush
            write_cache(redis_client, _buffer)
            _buffer = NonEmptyGpsRecordList(item=[])
        else:
            record = poll_gps(gps_client)
            if record:
                _buffer.append(record)
                ring_buffer.extend([record])
        # Collect one record per second
        time.sleep(1)


if __name__ == "__main__":
    # Resources
    gpsd = GpsClient(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
    redis_client = RedisClient(host="localhost", port=6379, db=0)
    kafka_producer = KafkaProducer(bootstrap_servers="localhost:1234")

    # Main loop
    print("Starting...")
    poll_gps(gpsd, 25)
