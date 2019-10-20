# Processes events from Retropie and Emulation Station to drive the light controller.
#
# The event bash scripts expect this to be located in ~/amiacs.
#
# Install
# cd ~
# mkdir amiacs
# cd amiacs
# wget https://github.com/CharlesWB/Amiacs-Arcade-Cabinet/raw/master/code/Amiacs-Event-Processor/Amiacs-Event-Processor.py
#
# References
# https://github.com/RetroPie/RetroPie-Setup/wiki/EmulationStation#scripting
# I'm not getting scripting to work. There's no indication that the bash script is called.
#
# https://github.com/RetroPie/RetroPie-Setup/wiki/runcommand#runcommand-onstart-and-runcommand-onend-scripts
#
# Notes
# Emulation Station events do not provide the system name. Runcommand does. Maybe could be read from rom path.
# Emulation station events do provide the rom name and path separately. Runcommand combines them.

import argparse
import logging

logging.basicConfig(filename='/home/pi/amiacs/Amiacs-Event-Processor.log',level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('event', choices=['game-start', 'game-end', 'sleep', 'wake'], help='the event that is happening')
parser.add_argument('system', help='the system (eg: atari2600, nes, snes, megadrive, fba, etc)')
parser.add_argument('emulator', help='the emulator (eg: lr-stella, lr-fceumm, lr-picodrive, pifba, etc)')
parser.add_argument('rompath', help='the full path to the rom file')
parser.add_argument('commandline', help='the full command line used to launch the emulator')

args = parser.parse_args()

logging.info('event:%s', args.event)
logging.info('system:%s', args.system)
logging.info('emulator:%s', args.emulator)
logging.info('rompath:%s', args.rompath)
logging.info('commandline:%s', args.commandline)
