#!/bin/bash

# Options:
# UBX_DEVICE = one of sbin/ubx for configuring specifix u-blox chipsets
# GPS_RESET = Do a hard ubx reset

function gps_status(){
    s=$1
    if [[ $s -ne 0 ]]; then
        echo "setup_gps.sh failed"
        exit 1
    fi 
}

if [[ $UID -eq 0 || -n $SUDO_USER ]]; then
	echo "Cowardly refusing to run as root or sudo"
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PY_BIN="$HOME/.pyenv/versions/3.8.13/bin/python3"
BASE_DIR="$DIR/.."
source $HOME/.bashrc

echo "Starting with Python env $PY_BIN"
cd "$BASE_DIR"
poetry env use $PY_BIN

if [[ $UID -eq 0 ]]; then
	SUDO_USER=0
fi

# TODO: this is dumb because it needs passwordless sudo
echo "Running setup"
if [[ -n $SUDO_USER || $UID -eq 0 ]]; then
    echo "Running as root"
	/bin/bash $DIR/setup_gps.sh
    gps_status $?
else
    echo "Running w/ sudo"
    sudo /bin/bash $DIR/setup_gps.sh
    gps_status $?
fi


if [[ -n $(~/.pyenv/versions/3.8.13/bin/pip3 list | grep tiny-telematics) || -n "$DO_BUILD" ]]; then
    echo "Building"
    cd "$BASE_DIR"
    poetry build
    poetry install
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


# Configure the u-blox device, if you have one
# Note: This is specific for my u-blox G7020-KT
if [[ -n $UBX_DEVICE && -f $DIR/ubx/$UBX_DEVICE ]]; then 
	echo "Configuring $UBX_DEVICE"
	/bin/bash $DIR/ubx/$UBX_DEVICE
else
	echo "UBX_DEVICE not set"
fi

echo "Running"
cd "$BASE_DIR"
poetry run python -m tiny_telematics.main --config $DIR/../config/dev.yaml -v
