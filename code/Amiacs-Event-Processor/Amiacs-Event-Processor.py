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
# https://github.com/RetroPie/RetroPie-Setup/wiki/runcommand#runcommand-onstart-and-runcommand-onend-scripts
#
# https://github.com/RetroPie/RetroPie-Setup/wiki/EmulationStation#scripting
# Event scripting was added with RetroPie 4.5 (Emulation Station v2.8.4).
# I was able to get game-start, game-end and quit events to fire, but not sleep, wake, screensaver-start, and screensaver-stop.
# Sleep and wake are in the source code (es-core/src/Window.cpp), but not the screensaver events. Maybe I
# don't understand when sleep and wake occur.
# I need screensaver events to work. I'm using runcommand for the game start and end. For now we'll
# fake it in the light controller.
#
# Notes
# Emulation Station events do not provide the system name. Runcommand does. Maybe could be parsed from rom path.
# Emulation station events do provide the rom name and path separately. Runcommand combines them.

import argparse
import logging
import smbus
from enum import Enum


class Light(Enum):
    Off = False
    On = True

    # Not the best practice for repr, but it looks good in PlayerLights.
    def __repr__(self):
        return self.name


class PlayerLights:
    def __init__(
            self,
            B=Light.Off, A=Light.Off, Y=Light.Off, X=Light.Off,
            L1=Light.Off, R1=Light.Off, L2=Light.Off, R2=Light.Off,
            HotKey=Light.Off, Select=Light.Off, Start=Light.Off, Command=Light.Off):
        # The order appears to be used by __dict__ which I use in __repr__.
        # This order roughly aligns with the three rows of buttons.
        self.B = B
        self.A = A
        self.L1 = L1
        self.R1 = R1
        self.Y = Y
        self.X = X
        self.L2 = L2
        self.R2 = R2
        self.HotKey = HotKey
        self.Select = Select
        self.Start = Start
        self.Command = Command

    # The indenting is designed for use with the CabinetLights class.
    def __repr__(self):
        return '{}(\n        {})'.format(self.__class__.__name__, self.__dict__)


class CabinetLights:
    def __init__(self, player1Lights=PlayerLights(), player2Lights=PlayerLights()):
        self.player1Lights = player1Lights
        self.player2Lights = player2Lights

    def __repr__(self):
        return "{}(\n    'player1Lights':{}\n    'player2Lights':{})".format(self.__class__.__name__, self.player1Lights, self.player2Lights)


systemLights = {
    'default': CabinetLights(),
    'arcade': CabinetLights(PlayerLights(B=Light.On))
}

gameLights = {
    '88games.zip': CabinetLights()
}

logging.basicConfig(
    filename='/home/pi/amiacs/Amiacs-Event-Processor.log', level=logging.INFO)

bus = smbus.SMBus(1)
address = 0x07

parser = argparse.ArgumentParser(
    'Given event information, send a command to the Amiacs light controller.')
parser.add_argument('event', choices=[
                    'game-start', 'game-end', 'sleep', 'wake'], help='the event that has occurred')
parser.add_argument(
    'system', help='the system (eg: atari2600, nes, snes, megadrive, fba, etc)')
parser.add_argument(
    'emulator', help='the emulator (eg: lr-stella, lr-fceumm, lr-picodrive, pifba, etc)')
parser.add_argument('rompath', help='the full path to the rom file')
parser.add_argument(
    'commandline', help='the full command line used to launch the emulator')

args = parser.parse_args()

logging.info('--------')
logging.info('Arguments:')
logging.info('event:%s', args.event)
logging.info('system:%s', args.system)
logging.info('emulator:%s', args.emulator)
logging.info('rompath:%s', args.rompath)
logging.info('commandline:%s', args.commandline)

# TODO The rompath needs to be parsed to get the rom filename for the dictionary index.
if args.rompath.lower() in gameLights:
    logging.info('Configuring lights for game %s.', args.rompath)
    lights = gameLights[args.rompath.lower()]
elif args.system.lower() in systemLights:
    logging.info('Configuring lights for system %s.', args.system)
    lights = systemLights[args.system.lower()]
else:
    logging.info('Configuring default lights.')
    lights = systemLights['default']

logging.info(lights)

if args.event == 'game-start':
    bus.write_byte(address, 1)

if args.event == 'game-end':
    bus.write_byte(address, 0)
