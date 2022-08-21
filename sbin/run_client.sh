#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


if [[ $UID -eq 0 ]]; then
	SUDO_USER=0
fi

echo "Running setup"
if [[ -n $SUDO_USER ]]; then
	/bin/bash $DIR/setup_gps.sh
else
    sudo /bin/bash $DIR/setup_gps.sh
fi


if [[ -n $(~/.pyenv/versions/3.8.13/bin/pip3 list | grep tiny-telematics) || -n "$DO_BUILD" ]]; then
    echo "Building"
    cd "$DIR/.."
    poetry build
fi

echo "Running"
~/.pyenv/versions/3.8.13/bin/python3 -m tiny_telematics.main.py --config $DIR/../config/dev.yaml