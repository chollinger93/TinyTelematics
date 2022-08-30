#!/bin/bash
# for docker

/bin/bash setup_gps.sh
python -m tiny_telematics.main "$@"