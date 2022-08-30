#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

function setup(){
    sudo sysctl -w net.ipv6.conf.lo.disable_ipv6=0
    sudo killall -9 gpsd
    sudo systemctl stop gpsd.socket
    sudo aa-complain /usr/sbin/gpsd
}

gpsfake --singleshot -S $DIR/../resources/GraphHopper.nmea