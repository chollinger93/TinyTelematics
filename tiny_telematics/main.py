from argparse import ArgumentParser
from ast import parse
from asyncio import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Generator, List, Generic, NewType, Optional, TypeVar
from collections import deque
from gps import gps as GpsClient
from gps import WATCH_ENABLE, WATCH_NEWSTYLE
import json
import uuid
import time
import logging
import colorlog
from redis import Redis as RedisClient
from kafka import KafkaProducer
import jsonpickle
import subprocess
from geopy import distance
import statistics
from dacite import from_dict
import yaml

# Model (also types)
REDIS_KEY = 'buffer'

@dataclass
class GpsRecord:
    lat: float
    lon: float
    altitude: float
    speed: float
    timestamp: float = time.time()
    id: str = hex(uuid.getnode())

    def __str__(self):
        return str(json.dumps(self.__dict__))

    def to_json(self):
        return jsonpickle.encode(self)

@dataclass
class GeneralConfig:
    expected_wifi_network: str
    shutdown_timer_s: int = 10
    cache_buffer: int = 10
    filter_empty_records: bool = False

@dataclass
class CacheConfig:
    host: str = 'localhost'
    port: int = 6379
    db: int = 0

@dataclass
class KafkaConfig:
    boostrap_servers: str 
    topic: str 

@dataclass
class Config:
    general: GeneralConfig
    cache: CacheConfig
    kafka: KafkaConfig

# Types
T = TypeVar("T")
NonEmptyGpsRecordList = NewType("NonEmptyGpsRecordList", List[GpsRecord])


def poll_gps(gps_client: GpsClient, do_filter_empty_records=False) -> Optional[GpsRecord]:
    """Poll the GPS sensor for a record

    Args:
        gps_client (GpsClient): GPS Client

    Returns:
        Optional[GpsRecord]: Might be not available
    """
    while True:
        try:
            report = gps_client.next()
            # TPV - Time Position Velocity
            # Returns a dictwrapper with various readings; we only need TPV
            if report["class"] == "TPV":
                # Get data
                lat = report.get("lat", 0.0)
                lon = report.get("lon", 0.0)
                altitude = report.get("alt", 0.0)
                speed = report.get("speed", 0.0)
                if do_filter_empty_records and (lat == 0.0  or lon == 0.0):
                    logger.warning('Empty record, filtering')
                    return None
                r = GpsRecord(lat, lon, altitude, speed) # TODO: filter 0.0
                logger.debug('Point: %s', r.to_json())
                return r
        except KeyError as e:
            # this happens
            continue


def write_cache(client: RedisClient, records: NonEmptyGpsRecordList) -> int:
    """Writes to the cache.

    Has side effects!

    Args:
        client (RedisClient): Redis client
        NonEmptyList (NonEmptyList[GpsRecord]): Non empty list of GPS readings

    Returns:
        IO[Unit]
    """
    logger.debug('Caching %s records', len(records))
    return client.rpush(REDIS_KEY, *list(map(lambda r: r.to_json(), records)))


def read_cache(client: RedisClient) -> Generator[GpsRecord, None, None]:
    """Reads from the redis cache, returning all records that have been buffered.

    Has side effects!

    Args:
        client (RedisClient): Redis client

    Yields:
        Generator[GpsRecord]: One record at a time, non-empty, non-null
    """
    for r in client.lrange(REDIS_KEY, 0, -1):
        yield jsonpickle.decode(r)


def clear_cache(client: RedisClient) -> int:
    logger.debug('Clearing cache at %s', REDIS_KEY)
    return client.delete(REDIS_KEY)

def publish_data(producer: KafkaProducer, topic: str, record: GpsRecord) -> None:
    """Publishes data to Kafka

    Args:
        client (KafkaProducer): KafkaProducer
        record (GpsRecord): Data to publish

    Returns:
        IO[Unit]
    """
    logger.debug('Publishing record: %s', record.to_json())
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
        logger.exception(e)
        return False


def calculate_distance_in_m(x, y: GpsRecord) -> float:
    return distance.distance((x.lat, x.lon), (y.lat, y.lon)).meters


def movement_has_changed_during_observation(    records: List[GpsRecord], threshold_m: float) -> bool:
    """Did the vehicle move?

    Args:
        records (List[GpsRecord]): List of recorded movements
        threshold_m (float): The threshold in meter

    Returns:
        bool: True if the mean distance between points is >= threshold
    """
    _distances = []
    for xm0, x0 in zip(records, records[1:]):
        dist_m = calculate_distance_in_m(xm0, x0)
        _distances.append(dist_m)
    logger.info('Mean distance in m: %s' % (statistics.mean(_distances)))
    return statistics.mean(_distances) >= threshold_m


def main(
    gps_client: GpsClient,
    redis_client: RedisClient,
    kafka_producer: KafkaProducer,
    kafka_topic: str,
    expected_network: str,
    buffer_size=10,
    max_no_movement_s=300,
    wait_time_s=1,
    do_filter_empty_records=False
) -> None:
    ring_buffer: deque[GpsRecord] = deque(maxlen=max_no_movement_s)
    _buffer: NonEmptyGpsRecordList = NonEmptyGpsRecordList([])
    while True:
        # Flush data when you can
        if is_network_available(expected_network):
            logger.debug('Found network %s' % expected_network)
            for r in read_cache(redis_client):
                publish_data(kafka_producer, kafka_topic, r)
                clear_cache(redis_client)
            # If we're at a standstill, shut down after N minutes, but only if we have enough data
            if len(list(ring_buffer)) >= max_no_movement_s:
                if not movement_has_changed_during_observation(list(ring_buffer), threshold_m=0.1):
                    logger.warning('Suspect standstill, shutting down')
                    break
                else:
                    logger.info('Enough movement change, continue')
            else:
                logger.debug('No data yet, cannot determine standstill (buffer: %s/%s)', len(list(ring_buffer)),max_no_movement_s)
        # With or without network, we just collect data
        if len(_buffer) - 1 >= buffer_size:
            # Flush
            write_cache(redis_client, _buffer)
            _buffer = NonEmptyGpsRecordList([])
        else:
            logger.debug('Polling GPS (buffer: %s)', len(_buffer))
            record = poll_gps(gps_client, do_filter_empty_records)
            if record:
                _buffer.append(record)
                ring_buffer.extend([record])
            else:
                logger.debug('No GPS record returned')
        # Collect one record per second
        time.sleep(wait_time_s)

def read_config(path: str) -> Config:
    with open(path) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        return from_dict(data_class=Config, data=config)

# Logging
fmt = "%(log_color)s%(asctime)s - %(levelname)s %(filename)s:%(funcName)s():%(lineno)d - %(message)s"
formatter = colorlog.ColoredFormatter(fmt=fmt)
handler = colorlog.StreamHandler()
handler.setFormatter(formatter)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    parser = ArgumentParser(description='Runs the TinyTelematics client')
    parser.add_argument('-c', '--config', type=str, help='Path to the config file')
    args = parser.parse_args()
    # Read config
    config = read_config(args.config)
    # Resources
    gpsd = GpsClient(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
    redis_client = RedisClient(host=config.cache.host, 
        port=config.cache.port, db=config.cache.db)
    kafka_producer = KafkaProducer(bootstrap_servers=config.kafka.boostrap_servers)

    # Main loop
    logger.info('Starting...')
    logger.info('Config: %s', config)
    main(
            gps_client=gpsd,
            redis_client=redis_client,
            kafka_producer=kafka_producer,
            kafka_topic=config.kafka.topic,
            expected_network=config.general.expected_wifi_network,
            buffer_size=config.general.cache_buffer,
            max_no_movement_s=config.general.shutdown_timer_s,
            wait_time_s=1,
            do_filter_empty_records=config.general.filter_empty_records
        )
