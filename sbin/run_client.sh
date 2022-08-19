#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "Prompting sudo for the gpsd setup"
sudo /bin/bash $DIR/setup_gps.sh

echo "Running"
poetry shell
python3 $DIR/../tiny_telematics/main.py --config $DIR/../config/dev.yaml