# Processes events from Retropie and Emulation Station to drive the light controller.
#
# The event bash scripts expect this to be located in ~/amiacs.
#
# Install
# cd ~
# mkdir amiacs
# cd amiacs
# wget https://raw.githubusercontent.com/CharlesWB/Amiacs-Arcade-Cabinet/master/code/Amiacs-Event-Processor/Amiacs-Event-Processor.py
# chmod +x Amiacs-Event-Processor.py
#
# References
# https://github.com/RetroPie/RetroPie-Setup/wiki/EmulationStation#scripting
# https://github.com/RetroPie/RetroPie-Setup/wiki/runcommand#runcommand-onstart-and-runcommand-onend-scripts
#
# Notes
# Emulation Station events do not provide the system name. Runcommand does. Maybe could be read from rom path.
# Emulation station events do provide the rom name and path separately. Runcommand combines them.

import argparse
import logging

logging.basicConfig(filename='~/amiacs/Amiacs-Event-Processor.log',level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('event', choices=['game-start', 'game-end', 'sleep', 'wake'], help='the event that is happening')
parser.add_argument('system', help='the system (eg: atari2600, nes, snes, megadrive, fba, etc)')

args = parser.parse_args()

logging.info(args.event)
logging.info(args.system)
