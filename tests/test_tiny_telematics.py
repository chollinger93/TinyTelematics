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
)
from datetime import datetime
from gps.client import dictwrapper


def test_version():
    assert __version__ == '0.1.0'


@pytest.mark.skip(reason='Just to hook up a debugger to real data')
def test_real_data():
    from gps import gps as GpsClient
    from gps import WATCH_ENABLE, WATCH_NEWSTYLE

    gps_client = GpsClient(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
    r = poll_gps(gps_client)

@pytest.fixture()
def mock_gps():
    data = {
        'lat': 10.0,
        'lon': -10.0,
        'altitude': 0,
        'speed': 39.3395,
        'class': 'TPV',
    }
    with mock.patch('gps.gps') as m:
        m.next.return_value = dictwrapper(data)
        yield m

@pytest.fixture()
def mock_redis():
    with mock.patch('redis.Redis') as m:
        m.rpush.return_value = 1
        m.lrange.return_value = [GpsRecord(10.0, -10.0, 0, -1).to_json()]
        yield m

@pytest.fixture()
def mock_kafka():
    with mock.patch('kafka.KafkaProducer') as m:
        m.send.return_value = None
        yield m

class TestGPS:
    def test_valid_run(self, mock_gps):
        r = poll_gps(mock_gps)
        assert r.lat == 10.0
        assert r.lon == -10.0

    def test_calculate_distance_in_m(self):
        newport_ri = GpsRecord(41.49008, -71.312796, 0, 0)
        cleveland_oh = GpsRecord(41.499498, -81.695391, 0, 0)
        m = calculate_distance_in_m(newport_ri, cleveland_oh)
        assert int(m) == 866455

    def test_movement_has_changed_during_observation(self):
        # Changed
        newport_ri = GpsRecord(41.49008, -71.312796, 0, 0)
        cleveland_oh = GpsRecord(41.499498, -81.695391, 0, 0)
        assert movement_has_changed_during_observation([newport_ri, cleveland_oh], 10)
        # no change
        l = [GpsRecord(0, 0.1, 0, 0), GpsRecord(0, 0.0, 0, 0), GpsRecord(0, 0.0, 0, 0)]
        # mean distance here is 5565.974539663679m
        assert not movement_has_changed_during_observation(l, 5567)


class TestCache:
    def test_write_cache(self, mock_redis):
        record = GpsRecord(10.0, -10.0, 0, -1)
        r = write_cache(mock_redis, [record])
        assert r == 1

    def test_read_cache(self, mock_redis):
        for r in read_cache(mock_redis):
            assert r != None
            assert r.lat == 10.0
            assert r.lon == -10.0

class TestMain:
    @mock.patch('subprocess.check_output')
    def test_is_network_available(self, mock_subproc):
        mock_subproc.return_value = b'WiFi'
        assert is_network_available('WiFi')

    @mock.patch('subprocess.check_output')
    def test_main(self, mock_subproc, mock_gps, mock_redis, mock_kafka):
        mock_subproc.return_value = b'WiFi'
        main(
            gps_client=mock_gps,
            redis_client=mock_redis,
            kafka_producer=mock_kafka,
            kafka_topic='test',
            expected_network='WiFi',
            buffer_size=10,
            max_no_movement_s=2,
            wait_time_s=0.001
        )
        # a stupid test that just walks the code path and make sure no
        # types or anything break
        pass

    def test_read_config(self):
        c = read_config('config/default.yaml')
        assert c.general.expected_wifi_network == 'MyHomeWiFi'