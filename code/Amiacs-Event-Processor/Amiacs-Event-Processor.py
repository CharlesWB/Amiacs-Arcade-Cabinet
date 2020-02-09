# Processes events from Retropie and Emulation Station to drive the light controller.
#
# The event bash scripts expect this to be located in ~/amiacs.
#
# Install
# cd ~
# mkdir amiacs
# cd amiacs
# wget https://github.com/CharlesWB/Amiacs-Arcade-Cabinet/raw/master/code/Amiacs-Event-Processor/Amiacs-Event-Processor.py --output-document=Amiacs-Event-Processor.py
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
import os
import smbus
from enum import Enum


# These value match what is found in Amiacs_Light_Controller.ino.
class DisplayMode(Enum):
    Starting = 0
    Attract = 1
    Emulation_Station = 2
    Game_Running = 3


class Light(Enum):
    Off = False
    On = True

    # Not the best practice for repr, but it looks good in PlayerLights.
    def __repr__(self):
        return self.name

    def I2CData(self):
        return 1 if self == Light.On else 0


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
        self.Select = Select
        self.Start = Start
        self.HotKey = HotKey
        self.Command = Command

    # The indenting is designed for use with the CabinetLights class.
    def __repr__(self):
        return '{}(\n        {})'.format(self.__class__.__name__, self.__dict__)

    # Returns the lights in a list. The order matches what Amiacs_Light_Controller.ino will expect.
    def I2CData(self):
        return [self.A.I2CData(), self.B.I2CData(), self.Y.I2CData(), self.X.I2CData(), self.L2.I2CData(), self.R2.I2CData(),
                self.L1.I2CData(), self.R1.I2CData(), self.Select.I2CData(), self.Start.I2CData(), self.Command.I2CData(), self.HotKey.I2CData()]


class CabinetLights:
    def __init__(self, player1Lights=PlayerLights(), isTwoPlayer=True, player2Lights=PlayerLights()):
        self.player1Lights = player1Lights
        if isTwoPlayer:
            self.player2Lights = player1Lights
        else:
            self.player2Lights = player2Lights

    def __repr__(self):
        return "{}(\n    'player1Lights':{}\n    'player2Lights':{})".format(self.__class__.__name__, self.player1Lights, self.player2Lights)

    def I2CData(self):
        return self.player1Lights.I2CData() + self.player2Lights.I2CData()


systemLights = {
    'default': CabinetLights(PlayerLights(B=Light.On, A=Light.On), False),
    'arcade': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Y=Light.On, X=Light.On, L2=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'atari2600': CabinetLights(
        PlayerLights(B=Light.On, HotKey=Light.On, Command=Light.On)),
    'atari7800': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'c64': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, HotKey=Light.On, Command=Light.On)),
    'coleco': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, HotKey=Light.On, Command=Light.On)),
    'daphne': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, Select=Light.On, Start=Light.On, Command=Light.On)),
    'famicom': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'fds': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'gamegear': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On), False),
    'gb': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On), False),
    'gba': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On), False),
    'gbc': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On), False),
    'genesis': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'intellivision': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'markiii': CabinetLights(
        PlayerLights(B=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'mastersystem': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, HotKey=Light.On, Command=Light.On), False),
    'megadrivej': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'n64': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'neogeo': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'nes': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'nesh': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'pc': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On), False),
    'pcengine': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On), False),
    'psx': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'scummvm': CabinetLights(
        PlayerLights(B=Light.On, L2=Light.On, R2=Light.On), False),
    'sega32x': CabinetLights(
        PlayerLights(B=Light.On, X=Light.On, Y=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'segacd': CabinetLights(
        PlayerLights(B=Light.On, X=Light.On, Y=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'segah': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'sg-1000': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'snes': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On)),
    'turbografx16': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On), False),
    'virtualboy': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Select=Light.On, Start=Light.On, HotKey=Light.On, Command=Light.On))
}

gameLights = {
    'asteroid.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, Start=Light.On, Select=Light.On, HotKey=Light.On, Command=Light.On))
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

romname = os.path.basename(args.rompath)

logging.info('--------')
logging.info('Arguments:')
logging.info('event: %s', args.event)
logging.info('system: %s', args.system)
logging.info('emulator: %s', args.emulator)
logging.info('rom name: %s', romname)
logging.info('rompath: %s', args.rompath)
logging.info('commandline: %s', args.commandline)

if args.event == 'game-start':
    if romname.lower() in gameLights:
        logging.info('Configuring lights for game %s.', romname)
        lights = gameLights[romname.lower()]
    elif args.system.lower() in systemLights:
        logging.info('Configuring lights for system %s.', args.system)
        lights = systemLights[args.system.lower()]
    else:
        logging.info('Configuring default lights.')
        lights = systemLights['default']

    logging.info(lights)

    bus.write_i2c_block_data(address, DisplayMode.Game_Running.value, lights.I2CData())

if args.event == 'game-end':
    bus.write_byte(address, DisplayMode.Emulation_Station.value)
