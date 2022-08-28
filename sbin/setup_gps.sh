#!/bin/bash

# Options:
# UBX_DEVICE = one of sbin/ubx for configuring specifix u-blox chipsets
# GPS_RESET = Do a hard ubx reset

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

is_installed() {
     dpkg --verify "$1" 2>/dev/null
}

function replaceDevices(){
	for i in $(seq 0 2); do
		local id=$i
		echo "Probing /dev/ttyACM$id"
		if [[ -n $(udevadm info "/dev/ttyACM$id" | grep GPS) ]]; then 
			echo "Replacing gpsd devices with /dev/ttyACM$id"
			sed -i "s#DEVICES=\"\"#DEVICES=\"/dev/ttyACM$id\"#g" ${GPSD}
			sed -iE "s#/dev/ttyACM[0-9]#/dev/ttyACM$id#g" ${GPSD}
			echo "New gpsd config:"
			cat ${GPSD}
			break
		fi
	done
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
killall -9 gpsd
killall -9 gpsfake
systemctl stop gpsd.socket
rm -f /var/run/gpsd.sock

# Source and check
if [[ ! -s "${GPSD}" ]]; then
	echo "Can't read ${GPSD}, trying to fix it..."
	cp "$DIR/../system/gpsd" ${GPSD}
fi
if [[ ! -s "${GPSD}" ]]; then
	echo "Can't read ${GPSD}, something is very broken. Refusing to cooperate."
	exit 1
fi

# Restore gpsd config
# TODO: shitty detection, needs udev rule
replaceDevices

# Loopback fix
echo "Fixing ipv6 config"
sysctl -w net.ipv6.conf.lo.disable_ipv6=0

# Restart
echo "Starting service"
service gpsd restart
if [[ $? -ne 0 ]]; then
	echo "Error: Couldn't start gpsd"
	exit 1
fi

# Uncomment this if you re-use an old receiver
if [[ -n $GPS_RESET ]]; then 
	echo "Resetting"
	r=$(ubxtool -p RESET -P 14.00)
	if [[ $? -ne 0 || -n $(echo $r | grep -i 'error' ) ]]; then
		echo "Error: Reset failed: $r"
		exit 1
	fi
fi

# Probe
ps aux | grep gpsd
# gpsmon as alternative
