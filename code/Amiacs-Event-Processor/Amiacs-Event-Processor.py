# Processes events from Retropie and Emulation Station to drive the light controller.
#
# The event bash scripts expect this to be located in ~/amiacs.
#
# This is a simplistic version of what https://www.ledblinky.net/ provides.
#
# Install
# cd ~
# mkdir amiacs
# cd amiacs
# wget https://github.com/CharlesWB/Amiacs-Arcade-Cabinet/raw/master/code/Amiacs-Event-Processor/Amiacs-Event-Processor.py --output-document=Amiacs-Event-Processor.py
# wget https://github.com/CharlesWB/Amiacs-Arcade-Cabinet/raw/master/code/Amiacs-Event-Processor/Amiacs-System-Lights.json --output-document=Amiacs-System-Lights.json
# wget https://github.com/CharlesWB/Amiacs-Arcade-Cabinet/raw/master/code/Amiacs-Event-Processor/Amiacs-Game-Lights.json --output-document=Amiacs-Game-Lights.json
#
# References
# https://retropie.org.uk/docs/Runcommand/#runcommand-onstart-and-runcommand-onend-scripts
#
# https://retropie.org.uk/docs/EmulationStation/#scripting
#
# Notes
# Emulation Station events do not provide the system name. Runcommand does. Maybe could be parsed from rom path.
# Emulation station events do provide the rom name and path separately. Runcommand combines them.

import argparse
import logging
import json
import os
import smbus
from enum import Enum
from pathlib import Path

# path = Path('.\\code\\Amiacs-Event-Processor')
path = Path('/home/pi/amiacs/')

# These values match what is found in Amiacs_Light_Controller.ino.
class DisplayMode(Enum):
    Starting = 0
    Attract = 1
    Emulation_Station = 2
    Game_Running = 3


class PlayerLights:
    def __init__(
            self,
            B=False, A=False, Y=False, X=False,
            L1=False, R1=False, L2=False, R2=False,
            Hotkey=False, Select=False, Start=False, Command=False):
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
        self.Hotkey = Hotkey
        self.Command = Command

    # The indenting is designed for use with the CabinetLights class.
    def __repr__(self):
        return '{}(\n        {})'.format(self.__class__.__name__, {k: "On" if v else "Off" for k, v in self.__dict__.items()})

    # Returns the lights in a list. The order matches what Amiacs_Light_Controller.ino will expect.
    def I2CData(self):
        return [int(self.B), int(self.A), int(self.Y), int(self.X), int(self.L2), int(self.R2),
                int(self.L1), int(self.R1), int(self.Select), int(self.Start), int(self.Command), int(self.Hotkey)]


class CabinetLights:
    def __init__(self, player1Lights=None, isTwoPlayerGame=True, isTwoControllerGame=True, player2Lights=None, usesTrackball=False):
        self.player1Lights = player1Lights if player1Lights is not None else PlayerLights()
        self.player2Lights = player2Lights if player2Lights is not None else PlayerLights()

        self.isTwoPlayerGame = isTwoPlayerGame
        self.isTwoControllerGame = isTwoControllerGame

        # When this is a two player and two controller game, we'll automatically copy the lights from player one to simplify construction.
        # Excluding Hotkey and Command because they are not normal player buttons.
        # For example, the arcade system uses player one's Hotkey and Command buttons, but not player two's.
        if isTwoPlayerGame and isTwoControllerGame and player2Lights is None:
            self.player2Lights.B = player1Lights.B
            self.player2Lights.A = player1Lights.A
            self.player2Lights.L1 = player1Lights.L1
            self.player2Lights.R1 = player1Lights.R1
            self.player2Lights.Y = player1Lights.Y
            self.player2Lights.X = player1Lights.X
            self.player2Lights.L2 = player1Lights.L2
            self.player2Lights.R2 = player1Lights.R2
            self.player2Lights.Select = player1Lights.Select
            self.player2Lights.Start = player1Lights.Start

        # When this is a two player game with one shared controller, we'll automatically copy the Start and Select buttons.
        # This is useful for games that alternate two players and have separate coin and two player buttons.
        if isTwoPlayerGame and not isTwoControllerGame and player2Lights is None:
            self.player2Lights.Select = player1Lights.Select
            self.player2Lights.Start = player1Lights.Start

        self.usesTrackball = usesTrackball

    def __repr__(self):
        return "{}(\n    'player1Lights':{}\n    'player2Lights':{}\n    usesTrackball:{})".format(self.__class__.__name__, self.player1Lights, self.player2Lights, self.usesTrackball)

    def I2CData(self):
        return self.player1Lights.I2CData() + self.player2Lights.I2CData() + [int(self.usesTrackball)] + [int(self.isTwoPlayerGame)]


# TODO This does not seem like the best way to decode a JSON dictionary of nested custom classes.
def lightsJsonDecoder(data):
    if len(data) == 12:
        return PlayerLights(data['B'], data['A'], data['Y'], data['X'], data['L1'], data['R1'], data['L2'], data['R2'], data['Hotkey'], data['Select'], data['Start'], data['Command'])
    elif len(data) == 5:
        return CabinetLights(data['player1Lights'], data['isTwoPlayerGame'], data['isTwoControllerGame'], data['player2Lights'], data['usesTrackball'])
    return data


logging.basicConfig(
    filename=path / 'Amiacs-Event-Processor.log', level=logging.INFO, format='%(asctime)s %(message)s')

logging.info('Begin Amiacs event processing.')

parser = argparse.ArgumentParser(
    'Given event information, send a command to the Amiacs light controller.')
parser.add_argument('event', choices=[
                    'game-start', 'game-end', 'screensaver-start', 'screensaver-stop'], help='the event that has occurred')
parser.add_argument(
    'system', help='the system (eg: atari2600, nes, snes, megadrive, fba, etc)')
parser.add_argument(
    'emulator', help='the emulator (eg: lr-stella, lr-fceumm, lr-picodrive, pifba, etc)')
parser.add_argument('rompath', help='the full path to the rom file')
parser.add_argument(
    'commandline', help='the full command line used to launch the emulator')

args = parser.parse_args()

romname = os.path.basename(args.rompath)

logging.info('Arguments:')
logging.info('event: {}'.format(args.event))
logging.info('system: {}'.format(args.system))
logging.info('emulator: {}'.format(args.emulator))
logging.info('rom name: {}'.format(romname))
logging.info('rompath: {}'.format(args.rompath))
logging.info('commandline: {}'.format(args.commandline))

bus = smbus.SMBus(1)
address = 0x07

if args.event == 'game-start':
    with open(path / 'Amiacs-System-Lights.json') as file:
        systemLights = json.load(file, object_hook=lightsJsonDecoder)

    logging.info('Loaded {} system lights.'.format(len(systemLights)))

    with open(path / 'Amiacs-Game-Lights.json') as file:
        gameLights = json.load(file, object_hook=lightsJsonDecoder)

    logging.info('Loaded {} game lights.'.format(len(gameLights)))

    if romname in gameLights:
        logging.info('Configuring lights for game {}.'.format(romname))
        lights = gameLights[romname]
    elif args.system in systemLights:
        logging.info('Configuring lights for system {}.'.format(args.system))
        lights = systemLights[args.system]
    else:
        logging.info('Configuring default lights.')
        lights = systemLights['default']

    logging.info(lights)

    bus.write_i2c_block_data(
        address, DisplayMode.Game_Running.value, lights.I2CData())

if args.event == 'game-end':
    bus.write_byte(address, DisplayMode.Emulation_Station.value)

if args.event == 'screensaver-start':
    bus.write_byte(address, DisplayMode.Attract.value)

if args.event == 'screensaver-stop':
    bus.write_byte(address, DisplayMode.Emulation_Station.value)

logging.info('End Amiacs event processing.')
