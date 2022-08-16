#!/bin/bash

if [[ -z $SUDO_USER ]]; then
	echo "Script must be called as sudo"
	exit 1
fi

# Install dependencies
if [[ -z $(dpkg -s gpsd) ]]; then 
	echo "Installing dependencies"
	apt-get update
	apt-get install gpsd gpsd-clients gpsd-tools ntp
fi

# Backup
GPSD=/etc/default/gpsd
cp ${GPSD} /etc/default/gpsd.bkp

# kill
echo "Killing orphaned services"
killall gpsd
rm -f /var/run/gpsd.sock

# Source and check
source ${GPSD}
if [[ $? -ne 0 ]]; then
	echo "Can't read ${GPSD}"
	exit 1
fi

# Get drives
#lsusb

# Replace devices
if [[ -z "${DEVICES}" ]]; then
	echo "Replacing DEVICES"
	sed -i 's#DEVICES=""#DEVICES="/dev/ttyACM0"#g' ${GPSD}
fi

if [[ -z "${GPSD_OPTIONS}" ]]; then
	sed -i 's#GPSD_OPTIONS=""#GPSD_OPTIONS="-n"#g' ${GPSD}
fi

# Loopback fix
echo "Fixing ipv6 config"
sysctl -w net.ipv6.conf.lo.disable_ipv6=0

# Restart
echo "Starting service"
service gpsd restart
# Manual
#gpsd /dev/ttyACM0 -F /var/run/gpsd.sock