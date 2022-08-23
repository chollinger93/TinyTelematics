#!/bin/bash

is_installed() {
     dpkg --verify "$1" 2>/dev/null
}

if [[ $UID -eq 0 ]]; then
	SUDO_USER=0
fi

if [[ -z $SUDO_USER ]]; then
	echo "Script must be called as sudo"
	exit 1
fi

# Install dependencies
if ! is_installed "gpsd" ; then 
	echo "Installing dependencies"
	apt-get update
	apt-get install gpsd gpsd-clients ntp wireless-tools gpsd-tools psmisc -y
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

function replaceDevice(){
	id=$1
	if [[ -n $(udevadm info "/dev/ttyACM$id" | grep GPS) ]]; then 
		echo "Replacing DEVICES"
		sed -i "s#DEVICES=\"\"#DEVICES=\"/dev/ttyACM$id\"#g" ${GPSD}
		sed -iE "s#/dev/ttyACM[0-9]#/dev/ttyACM$id#g" ${GPSD}
	fi
}

# Replace devices
# TODO: shitty detection, needs udev rule
replaceDevice 0
replaceDevice 1

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
ps aux | grep gpsd