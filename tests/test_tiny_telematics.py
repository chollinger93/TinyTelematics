import pytest
from typing import Dict
from unittest import mock
from tiny_telematics import __version__
from tiny_telematics.main import (
    poll_gps,
    write_cache,
    read_cache,
    calculate_distance_in_m,
    movement_has_changed_during_observation,
    is_network_available,
    main,
    read_config,
    GpsRecord,
    generate_new_trip_id,
    send_available_data_if_possible,
)
from datetime import datetime
from gps.client import dictwrapper
import sys

TRIP_ID = 2147483647


def test_version():
    assert __version__ == "0.1.0"


@pytest.mark.skip(reason="You can run this w/ a real GPS dongle")
def test_real_data():
    import time
    from gps import gps as GpsClient
    from gps import WATCH_ENABLE, WATCH_NEWSTYLE

    last_point: GpsRecord = None
    gps_client = GpsClient(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
    i = 0
    for r in poll_gps(gps_client, TRIP_ID, prev=last_point):
        try:
            print(r)
            if r:
                last_point = r
                i += 1
            if i >= 5:
                return
            time.sleep(1)
        except KeyboardInterrupt:
            return


@pytest.fixture()
def mock_gps():
    data = {
        "lat": 10.0,
        "lon": -10.0,
        "altitude": 0,
        "speed": 39.3395,
        "class": "TPV",
    }
    with mock.patch("gps.gps") as m:
        m.next.return_value = dictwrapper(data)
        yield m


@pytest.fixture()
def mock_redis():
    with mock.patch("redis.Redis") as m:
        m.rpush.return_value = 1
        m.lrange.return_value = [
            GpsRecord(
                tripId=TRIP_ID, lat=10.0, lon=-10.0, altitude=0, speed=-1
            ).to_json()
        ]
        yield m

@pytest.fixture()
def mock_empty_redis():
    with mock.patch("redis.Redis") as m:
        m.rpush.return_value = 1
        m.lrange.return_value =  []
        m.delete.side_effect = Exception('Deleted data!')
        yield m


@pytest.fixture()
def mock_kafka():
    with mock.patch("kafka.KafkaProducer") as m:
        m.send.return_value = None
        yield m


class TestGPS:
    def test_valid_run(self, mock_gps):
        for r in poll_gps(mock_gps, TRIP_ID):
            assert r.lat == 10.0
            assert r.lon == -10.0
            return

    @mock.patch("gps.gps")
    def test_filter_empty(self, gps_client):
        data = {
            "lat": 0.0,
            "lon": 0.0,
            "altitude": 0,
            "speed": 39.3395,
            "class": "TPV",
        }
        gps_client.next.return_value = dictwrapper(data)
        for r in poll_gps(gps_client, TRIP_ID, do_filter_empty_records=True):
            assert r is None
            return

    def test_calculate_distance_in_m(self):
        newport_ri = GpsRecord(TRIP_ID, 41.49008, -71.312796, 0, 0)
        cleveland_oh = GpsRecord(TRIP_ID, 41.499498, -81.695391, 0, 0)
        m = calculate_distance_in_m(newport_ri, cleveland_oh)
        assert int(m) == 866455

    def test_movement_has_changed_during_observation(self):
        # Changed
        newport_ri = GpsRecord(TRIP_ID, 41.49008, -71.312796, 0, 0)
        cleveland_oh = GpsRecord(TRIP_ID, 41.499498, -81.695391, 0, 0)
        assert movement_has_changed_during_observation([newport_ri, cleveland_oh], 10)
        # no change
        l = [
            GpsRecord(TRIP_ID, 0, 0.1, 0, 0),
            GpsRecord(TRIP_ID, 0, 0.0, 0, 0),
            GpsRecord(TRIP_ID, 0, 0.0, 0, 0),
        ]
        # mean distance here is 5565.974539663679m
        assert not movement_has_changed_during_observation(l, 5567)

    def test_encoder(self):
        newport_ri = GpsRecord(
            TRIP_ID,
            41.49008,
            -71.312796,
            0,
            0,
            timestamp=1661172024963,
            userId=32230107204254,
        )
        assert (
            newport_ri.to_json()
            == '{"py/object": "tiny_telematics.main.GpsRecord", "tripId": 2147483647, "lat": 41.49008, "lon": -71.312796, "altitude": 0, "speed": 0, "timestamp": 1661172024963, "userId": 32230107204254}'
        )


class TestCache:
    def test_write_cache(self, mock_redis):
        record = GpsRecord(TRIP_ID, 10.0, -10.0, 0, -1)
        r = write_cache(mock_redis, [record])
        assert r == 1

    def test_read_cache(self, mock_redis):
        for r in read_cache(mock_redis):
            assert r != None
            assert r.lat == 10.0
            assert r.lon == -10.0


class TestMain:
    @mock.patch("subprocess.check_output")
    def test_is_network_available(self, mock_subproc):
        mock_subproc.return_value = b"WiFi"
        assert is_network_available("WiFi")

    # TODO: AttributeError: Attempting to set unsupported magic method '__init__'.
    @mock.patch("subprocess.check_output")
    def test_main(self, mock_subproc, mock_gps, mock_redis, mock_kafka):
        with mock.patch("tiny_telematics.main.KafkaProduction.create") as m_kafka:
            mock_subproc.return_value = b"WiFi"
            m_kafka.return_value = mock_kafka
            main(
                gps_client=mock_gps,
                redis_client=mock_redis,
                bootstrap_servers="server",
                kafka_topic="test",
                expected_network="WiFi",
                buffer_size=10,
                max_no_movement_s=2,
                wait_time_s=0.001,
            )
            # a stupid test that just walks the code path and make sure no
            # types or anything break
            pass

    @mock.patch("subprocess.check_output")
    def test_send_available_data_if_possible(
        self, mock_subproc, mock_empty_redis, mock_kafka
    ):
        with mock.patch("tiny_telematics.main.KafkaProduction.create") as m_kafka:
            mock_subproc.return_value = b"WiFi"
            m_kafka.return_value = mock_kafka
            r = send_available_data_if_possible(
                "WiFi",
                redis_client=mock_empty_redis,
                kafka_topic="test",
                bootstrap_servers="server",
            )
            # No data returned
            assert r == 0
            # also, mock_empty_redis throws on delete()
            # i.e., this tests makes sure we don't delete data


    def test_read_config(self):
        c = read_config("config/default.yaml")
        assert c.general.expected_wifi_network == "MyHomeWiFi"

    def test_generate_new_trip_id(self):
        id = generate_new_trip_id()
        assert id is not None
        assert id >= 0
        assert id <= sys.maxsize
