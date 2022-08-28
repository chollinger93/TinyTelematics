from argparse import ArgumentParser
from asyncio import subprocess
from typing import Generator, List, Optional
from collections import deque
from gps import gps as GpsClient
from gps import WATCH_ENABLE, WATCH_JSON, WATCH_NEWSTYLE

import time
import logging
import colorlog
from redis import Redis as RedisClient
from kafka import KafkaProducer
import subprocess
from geopy import distance
import statistics
from dacite import from_dict
import yaml
import random
import sys
from dateutil.parser import isoparse
from abc import ABC, abstractmethod
from tiny_telematics.model import GpsRecord, NonEmptyGpsRecordList
from tiny_telematics.config import Config
import jsonpickle


# Constants
REDIS_KEY = "buffer"


class AbstractKafkaProduction(ABC):
    @staticmethod
    @abstractmethod
    def create(bootstrap_servers: str) -> KafkaProducer:
        pass


class KafkaProduction(AbstractKafkaProduction):
    @staticmethod
    def create(bootstrap_servers: str) -> KafkaProducer:
        return KafkaProducer(bootstrap_servers=bootstrap_servers)


def poll_gps(
    trip_id: int,
    max_drift_s: float = 5,
    do_filter_empty_records=False,
) -> Generator[Optional[GpsRecord], None, None]:
    """Poll the GPS sensor for a record

    Args:
        gps_client (GpsClient): GPS Client

    Returns:
        Optional[GpsRecord]: Might be not available
    """
    c = 0
    prev_tpv = None
    gps_session = GpsClient(mode=WATCH_ENABLE | WATCH_JSON | WATCH_NEWSTYLE)
    for report in gps_session:
        gps_session.read()
        try:
            # TPV - Time Position Velocity
            # Returns a dictwrapper with various readings; we only need TPV
            if report["class"] == "TPV":
                logger.debug(gps_session)
                c += 1
                # Get data to see if we need to continue
                ts = isoparse(report.get("time", "1776-07-04T12:00:00.000Z"))
                mode = report.get("mode", 0)
                if mode <= 1:
                    logger.warning("No GPS fix (%s), continue", mode)
                    continue
                logger.debug("Raw TPV: %s", report)
                # Account for drift, i.e. the rest of the program lags behind the gpsd buffer
                # In that case, just throw away records until we're current
                gps_time = ts.timestamp()
                now = time.time()
                drift_s = now - gps_time
                if drift_s >= max_drift_s:
                    logger.warning("Correcting %ss drift, skipping record", drift_s)
                    continue
                # Parse remaining attributes
                lat = report.get("lat", 0.0)
                lon = report.get("lon", 0.0)
                altitude = report.get("alt", 0.0)
                speed = report.get("speed", 0.0)
                if do_filter_empty_records and (lat == 0 or lon == 0):
                    logger.warning("Empty record, filtering")
                    continue
                # Check for duplicates
                if prev_tpv and prev_tpv.get("lat", 0.0) == lat and prev_tpv.get("lon", 0.0) == lon:
                    logger.warning("Duplicate record, filtering")
                    prev_tpv = report
                    continue
                # Only of all is well do we yield
                r = GpsRecord(
                    tripId=trip_id,
                    lat=lat,
                    lon=lon,
                    altitude=altitude,
                    speed=speed,
                    timestamp=int(ts.timestamp()),  # seconds
                )
                logger.debug("Point: %s", r.to_json())
                prev_tpv = report
                yield r
            else:
                logger.debug("Class is %s, skipping", report["class"])
                continue
        except KeyError as e:
            logger.debug("KeyError: %s", e)
            # this happens with SKY objects in 3.22
            continue
        except StopIteration:
            # gpsd's graceful shutdown, we have to honor that
            logger.error("gpsd asked us to stop, stopping")
            break
        except Exception as e:
            logger.exception(e)
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
    logger.info("Caching %s records", len(records))
    res = client.rpush(REDIS_KEY, *list(map(lambda r: r.to_json(), records)))
    logger.debug("Cached: %s", records)
    return res


def read_cache(client: RedisClient) -> Generator[GpsRecord, None, None]:
    """Reads from the redis cache, returning all records that have been buffered.

    Has side effects!

    Args:
        client (RedisClient): Redis client

    Yields:
        Generator[GpsRecord]: One record at a time, non-empty, non-null
    """
    for r in client.lrange(REDIS_KEY, 0, -1):
        v = jsonpickle.decode(r)
        logger.debug("Decoded %s", r)
        yield v


def clear_cache(client: RedisClient) -> int:
    logger.info("Clearing cache at %s", REDIS_KEY)
    return client.delete(REDIS_KEY)


def publish_data(producer: KafkaProducer, topic: str, record: GpsRecord) -> int:
    """Publishes data to Kafka

    Args:
        client (KafkaProducer): KafkaProducer
        record (GpsRecord): Data to publish

    Returns:
        IO[NumberOfWrittenRecords]
    """
    logger.debug("Publishing record: %s", record.to_json())
    try:
        producer.send(
            topic,
            key=str(record.userId).encode("utf-8"),
            value=jsonpickle.encode(record).encode("utf-8"),
        )
        return 1
    except Exception as e:
        logger.exception("Issue publishing data: %s", e)
        return 0


def is_network_available(expected_network: str) -> bool:
    try:
        # type: ignore
        return (
            subprocess.check_output(["iwgetid", "-r"]).decode("ascii").replace("\n", "")
            == expected_network
        )
    except Exception as e:
        # logger.exception(e)
        return False


def calculate_distance_in_m(x, y: GpsRecord) -> float:
    return distance.distance((x.lat, x.lon), (y.lat, y.lon)).meters


def movement_has_changed_during_observation(
    records: List[GpsRecord], threshold_m: float
) -> bool:
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
    logger.info("Mean distance in m: %s" % (statistics.mean(_distances)))
    return statistics.mean(_distances) >= threshold_m


def send_available_data_if_possible(
    expected_network: str,
    redis_client: RedisClient,
    kafka_topic: str,
    bootstrap_servers: str,
) -> int:
    """If the network is available, create a Kafka producer, read from the cache, and send data

    Args:
        expected_network (str): WiFi network
        redis_client (RedisClient): RedisClient
        kafka_topic (str): Kafka topic
        bootstrap_servers (str): Kafka servers

    Returns:
        int: Number of records sent
    """
    read_records = 0
    sent_records = 0
    # We only do this if we have WiFi, otherwise Kafka crashes
    if is_network_available(expected_network):
        try:
            # TODO: move creation elsewhere
            kafka_producer = KafkaProduction.create(bootstrap_servers=bootstrap_servers)
        except Exception as e:
            # It's possible we can't reach Kafka, which shouldn't crash the application
            logger.exception("Kafka error: %s", e)
            return 0
        for r in read_cache(redis_client):
            read_records += 1
            sent_records += publish_data(kafka_producer, kafka_topic, r)
        # Clear cache after producing
        if sent_records == read_records and sent_records > 0:
            clear_cache(redis_client)
            logger.info("Sent %s records to Kafka", sent_records)
        elif sent_records != read_records and (sent_records > 0 or read_records > 0):
            # TODO: this introduces duplicates, but avoids data loss. easy fix w/ partial deletes
            logger.error(
                "Sent records (%s) and read records (%s) do not match, not flushing cache!",
                sent_records,
                read_records,
            )
        else:
            pass
    return sent_records


def generate_new_trip_id() -> int:
    return int(random.choice(range(0, sys.maxsize)))


def main(
    redis_client: RedisClient,
    kafka_topic: str,
    bootstrap_servers: str,
    expected_network: str,
    buffer_size=10,
    max_no_movement_s=300,
    wait_time_s=1,
    max_drift_s=5,
    do_filter_empty_records=False,
) -> None:

    # Upon startup, we'll clear the cache once if we can
    if is_network_available(expected_network):
        logger.info("Found network %s, clearing existing cache" % expected_network)
        send_available_data_if_possible(
            expected_network, redis_client, kafka_topic, bootstrap_servers
        )
    # Buffers
    shutdown_buffer: deque[GpsRecord] = deque(maxlen=max_no_movement_s)
    _buffer: NonEmptyGpsRecordList = NonEmptyGpsRecordList([])
    # Generate a unique ID. We'll terminate otherwise
    trip_id = generate_new_trip_id()
    logger.info("Using tripId %s", trip_id)
    # Poll periodically, but indefinitely so we don't lose the connection
    # Once this function returns, we're done
    for record in poll_gps(trip_id, max_drift_s, do_filter_empty_records):
        # With or without network, we collect data first
        if record:
            _buffer.append(record)
            shutdown_buffer.extend([record])
        else:
            logger.debug("No GPS record returned")

        # Flush the buffer once it's full
        if len(_buffer) - 1 >= buffer_size:
            logger.debug("%s records in buffer, flushing to cache", len(_buffer))
            write_cache(redis_client, _buffer)
            _buffer = NonEmptyGpsRecordList([])

        # Flush data when you can
        if is_network_available(expected_network):
            logger.debug("Found network %s" % expected_network)
            send_available_data_if_possible(
                expected_network, redis_client, kafka_topic, bootstrap_servers
            )
            # If we're at a standstill, shut down after N minutes, but only if we have enough data
            if len(list(shutdown_buffer)) >= max_no_movement_s:
                if not movement_has_changed_during_observation(
                    list(shutdown_buffer), threshold_m=0.1
                ):
                    logger.warning(
                        "Suspect standstill, flushing cache again & shutting down"
                    )
                    send_available_data_if_possible(
                        expected_network, redis_client, kafka_topic, bootstrap_servers
                    )
                    break
                else:
                    logger.info(
                        "Enough movement change, suspect you're driving in circles in the driveway. Continue."
                    )
                    shutdown_buffer = deque(maxlen=max_no_movement_s)
            else:
                logger.debug(
                    "Not enough yet, cannot determine standstill (buffer: %s/%s)",
                    len(list(shutdown_buffer)),
                    max_no_movement_s,
                )

        # Collect one record per second
        time.sleep(wait_time_s)
        logger.debug("Polling GPS (buffer: %s)", len(_buffer))


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

if __name__ == "__main__":
    parser = ArgumentParser(description="Runs the TinyTelematics client")
    parser.add_argument("-c", "--config", type=str, help="Path to the config file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    # Read config
    config = read_config(args.config)
    # Resources
    redis_client = RedisClient(
        host=config.cache.host, port=config.cache.port, db=config.cache.db
    )

    # Main loop
    logger.info("Starting...")
    logger.info("Config: %s", config)
    main(
        redis_client=redis_client,
        kafka_topic=config.kafka.topic,
        bootstrap_servers=config.kafka.boostrap_servers,
        expected_network=config.general.expected_wifi_network,
        buffer_size=config.general.cache_buffer,
        max_no_movement_s=config.general.shutdown_timer_s,
        wait_time_s=config.general.poll_frequency_s,
        max_drift_s=config.general.max_drift_s,
        do_filter_empty_records=config.general.filter_empty_records,
    )
