#!/bin/bash

if [[ -z $SUDO_USER ]]; then
	echo "Script must be called as sudo"
	exit 1
fi

# Install dependencies
apt-get update
apt-get install gpsd gpsd-clients python-gps ntp

# Backup
GPSD=/etc/default/gpsd
cp ${GPSD} /etc/default/gpsd.bkp

# kill
kilall gpsd
rm -f /var/run/gpsd.sock

# Source and check
source ${GPSD}
if [[ $? -ne 0 ]]; then
	echo "Can't read ${GPSD}"
	exit 1
fi

# Get drives
lsusb

# Replace devices
if [[ -z "${DEVICES}" ]]; then
	echo "Replacing DEVICES"
	sed -i 's#DEVICES=""#DEVICES="/dev/ttyACM0"#g' ${GPSD}
fi

if [[ -z "${GPSD_OPTIONS}" ]]; then
	sed -i 's#GPSD_OPTIONS=""#GPSD_OPTIONS="-n"#g' ${GPSD}
fi

# Restart
service gpsd restart
# Manual
#gpsd /dev/ttyACM0 -F /var/run/gpsd.sock