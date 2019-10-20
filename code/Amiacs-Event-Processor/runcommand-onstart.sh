#!/bin/bash

# Reference
# https://github.com/RetroPie/RetroPie-Setup/wiki/runcommand#runcommand-onstart-and-runcommand-onend-scripts
#
# /opt/retropie/configs/all/runcommand-onstart.sh
#
# This script is appended to any existing script.

python3 ~/amiacs/Amiacs-Event-Processor.py game-start "$@"
