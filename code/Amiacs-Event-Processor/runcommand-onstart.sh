#!/bin/bash

# Reference
# https://retropie.org.uk/docs/Runcommand/#runcommand-onstart-and-runcommand-onend-scripts
#
# /opt/retropie/configs/all/runcommand-onstart.sh
#
# This script is appended to any existing script.

python3 ~/amiacs/Amiacs-Event-Processor.py game-start "$@"
