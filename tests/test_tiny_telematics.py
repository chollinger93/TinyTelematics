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
    GpsRecord,
)
from datetime import datetime
from gps.client import dictwrapper


def test_version():
    assert __version__ == "0.1.0"


@pytest.mark.skip(reason="Just to hook up a debugger to real data")
def test_real_data():
    from gps import gps as GpsClient
    from gps import WATCH_ENABLE, WATCH_NEWSTYLE

    gps_client = GpsClient(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
    r = poll_gps(gps_client)


class TestGPS:
    @mock.patch("gps.gps")
    def test_valid_run(self, gps_client):
        data = {
            "lat": 10.0,
            "lon": -10.0,
            "altitude": 0,
            "speed": 39.3395,
            "class": "TPV",
        }
        gps_client.next.return_value = dictwrapper(data)
        r = poll_gps(gps_client)
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
    @mock.patch("redis.Redis")
    def test_write_cache(self, client):
        client.rpush.return_value = 1
        record = GpsRecord(10.0, -10.0, 0, -1)
        r = write_cache(client, [record])
        assert r == 1

    @mock.patch("redis.Redis")
    def test_read_cache(self, client):
        client.lrange.return_value = [GpsRecord(10.0, -10.0, 0, -1).to_json()]
        for r in read_cache(client):
            assert r != None
            assert r.lat == 10.0
            assert r.lon == -10.0
