#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PY_BIN="$HOME/.pyenv/versions/3.8.13/bin/python3"
source $HOME/.bashrc

echo "Starting with Python env $PY_BIN"
poetry env use $PY_BIN

if [[ $UID -eq 0 ]]; then
	SUDO_USER=0
fi

# TODO: this is dumb because it needs passwordless sudo
echo "Running setup"
if [[ -n $SUDO_USER && $UID -ne 0 ]]; then
    echo "Running as sudo"
	sudo /bin/bash $DIR/setup_gps.sh
else
    echo "Running sudo"
    /bin/bash $DIR/setup_gps.sh
fi


if [[ -n $(~/.pyenv/versions/3.8.13/bin/pip3 list | grep tiny-telematics) || -n "$DO_BUILD" ]]; then
    echo "Building"
    cd "$DIR/.."
    poetry build
    poetry install
fi

echo "Running"
poetry run python -m tiny_telematics.main --config $DIR/../config/dev.yaml
