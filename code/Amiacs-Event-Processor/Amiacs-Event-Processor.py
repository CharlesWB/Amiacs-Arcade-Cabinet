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
# wget https://github.com/CharlesWB/Amiacs-Arcade-Cabinet/raw/master/code/Amiacs-Event-Processor/Amiacs-Trackball-Games.json --output-document=Amiacs-Trackball-Games.json
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
# import smbus
from enum import Enum
from pathlib import Path

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


systemLights = {
    'default': CabinetLights(PlayerLights(B=True, A=True), False, False),
    '3do': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, Select=True, Start=True, Hotkey=True, Command=True), False, False),
    'amigacd32': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'arcade': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, Y=True, X=True, L2=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'atari800': CabinetLights(
        PlayerLights(B=True, Hotkey=True, Command=True)),
    'atari2600': CabinetLights(
        PlayerLights(B=True, Hotkey=True, Command=True)),
    'atari5200': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'atari7800': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'atarijaguar': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, Y=True, X=True, L2=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'atomiswave': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, Y=True, X=True, L2=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'c64': CabinetLights(
        PlayerLights(B=True, A=True, Hotkey=True, Command=True)),
    'coleco': CabinetLights(
        PlayerLights(B=True, A=True, Hotkey=True, Command=True)),
    'daphne': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R2=True, Select=True, Start=True, Command=True), False),
    'dreamcast': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'famicom': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'fds': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'gamegear': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Hotkey=True, Command=True), False, False),
    'gb': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Hotkey=True, Command=True), False, False),
    'gba': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Select=True, Start=True, Hotkey=True, Command=True), False, False),
    'gbc': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Hotkey=True, Command=True), False, False),
    'genesis': CabinetLights(
        PlayerLights(B=True, A=True, Y=True, Start=True, Hotkey=True, Command=True)),
    'intellivision': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'markiii': CabinetLights(
        PlayerLights(B=True, Start=True, Hotkey=True, Command=True)),
    'mastersystem': CabinetLights(
        PlayerLights(B=True, A=True, Hotkey=True, Command=True), False, False),
    'megadrive': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'megadrivej': CabinetLights(
        PlayerLights(B=True, A=True, Y=True, X=True, Start=True, Hotkey=True, Command=True)),
    'n64': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'naomi': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, Y=True, X=True, L2=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'nds': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, Y=True, X=True, L2=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'neogeo': CabinetLights(
        PlayerLights(B=True, A=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'neogeocd': CabinetLights(
        PlayerLights(B=True, A=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'nes': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'nesh': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'openbor': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, Start=True)),
    'pc': CabinetLights(
        PlayerLights(B=True, A=True), False, False),
    'pcengine': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Hotkey=True, Command=True), False, False),
    'ps2': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'psp': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'pspminis': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'psx': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'scummvm': CabinetLights(
        PlayerLights(B=True, L2=True, R2=True), False, False),
    'sega32x': CabinetLights(
        PlayerLights(B=True, X=True, Y=True, Start=True, Hotkey=True, Command=True)),
    'segacd': CabinetLights(
        PlayerLights(B=True, X=True, Y=True, Start=True, Hotkey=True, Command=True)),
    'segah': CabinetLights(
        PlayerLights(B=True, A=True, Y=True, X=True, Start=True, Hotkey=True, Command=True)),
    'sg-1000': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Hotkey=True, Command=True)),
    'snes': CabinetLights(
        PlayerLights(B=True, A=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'snescd': CabinetLights(
        PlayerLights(B=True, A=True, Y=True, X=True, Select=True, Start=True, Hotkey=True, Command=True)),
    'turbografx16': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Hotkey=True, Command=True), False, False),
    'virtualboy': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Select=True, Start=True, Hotkey=True, Command=True))
}

gameLights = {
    '1941.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True)),
    '1942.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    '1943.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True)),
    '1943kai.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True)),
    '1943mii.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True)),
    '1944.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True)),
    '19xx.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True)),
    '720.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    '88games.zip': CabinetLights(
        PlayerLights(B=True, A=True, Y=True, Start=True, Select=True, Hotkey=True, Command=True)),
    'aburner.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True), False, False),
    'aburner2.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True), False, False),
    'ace.daphne': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, Y=True, X=True, L2=True, R2=True, Select=True, Start=True, Command=True), False),
    'airwolf.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'alcon.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True)),
    'altbeast.zip': CabinetLights(
        PlayerLights(B=True, A=True, X=True, Start=True, Select=True, Hotkey=True, Command=True)),
    'arcadecl.zip': CabinetLights(
        PlayerLights(B=True, Y=True, X=True, Start=True, Select=True, Hotkey=True, Command=True)),
    'arkanoid.zip': CabinetLights(
        PlayerLights(B=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'astdelux.zip': CabinetLights(
        PlayerLights(B=True, Y=True, X=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'asteroid.zip': CabinetLights(
        PlayerLights(B=True, Y=True, X=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'batman.zip': CabinetLights(
        PlayerLights(B=True, Y=True, Start=True, Select=True, Hotkey=True, Command=True), False, False),
    'bwidow.zip': CabinetLights(
        PlayerLights(Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'bzone.zip': CabinetLights(
        PlayerLights(B=True, Start=True, Select=True, Hotkey=True, Command=True), False, False),
    'centiped.zip': CabinetLights(
        PlayerLights(A=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'cliff.daphne': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Start=True, Command=True), False),
    'commando.zip': CabinetLights(
        PlayerLights(B=True, A=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'csprint.zip': CabinetLights(
        PlayerLights(B=True, Start=True, Select=True, Hotkey=True, Command=True)),
    'ccastles.zip': CabinetLights(
        PlayerLights(B=True, Select=True, Hotkey=True, Command=True), True, False, PlayerLights(B=True, Select=True)),
    'gauntlet2p.zip': CabinetLights(
        PlayerLights(B=True, A=True, Select=True, Hotkey=True, Command=True), True, True, PlayerLights(B=True, A=True, Select=True)),
    'gaunt2.zip': CabinetLights(
        PlayerLights(B=True, Y=True, Start=True, Select=True, Hotkey=True, Command=True)),
    'gravitar.zip': CabinetLights(
        PlayerLights(B=True, Y=True, X=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'indytemp.zip': CabinetLights(
        PlayerLights(B=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'jedi.zip': CabinetLights(
        PlayerLights(B=True, Y=True, X=True, Select=True, Hotkey=True, Command=True), False, False),
    'lair.daphne': CabinetLights(
        PlayerLights(B=True, Select=True, Start=True, Command=True), False),
    'lair2.daphne': CabinetLights(
        PlayerLights(B=True, Select=True, Start=True, Command=True), False),
    'llander.zip': CabinetLights(
        PlayerLights(B=True, Start=True, Select=True, Hotkey=True, Command=True), False, False),
    'marble.zip': CabinetLights(
        PlayerLights(Start=True, Select=True, Hotkey=True, Command=True)),
    'mhavoc.zip': CabinetLights(
        PlayerLights(B=True, Y=True, Select=True, Hotkey=True, Command=True), True, False),
    'milliped.zip': CabinetLights(
        PlayerLights(A=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'missile.zip': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'pacman.zip': CabinetLights(
        PlayerLights(Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'paperboy.zip': CabinetLights(
        PlayerLights(B=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'polepos.zip': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, Select=True, Hotkey=True, Command=True), False, False),
    'polepos2.zip': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, Select=True, Hotkey=True, Command=True), False, False),
    'quantum.zip': CabinetLights(
        PlayerLights(Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'redbaron.zip': CabinetLights(
        PlayerLights(B=True, Start=True, Select=True, Hotkey=True, Command=True), False, False),
    'roadblst.zip': CabinetLights(
        PlayerLights(B=True, A=True, X=True, Select=True, Hotkey=True, Command=True), False, False),
    'robotron.zip': CabinetLights(
        PlayerLights(Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'spyhunt.zip': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, R1=True, Y=True, X=True, L2=True, Start=True, Select=True, Hotkey=True, Command=True), False, False),
    'starwars.zip': CabinetLights(
        PlayerLights(B=True, A=True, Y=True, X=True, Select=True, Hotkey=True, Command=True), False, False),
    'tempest.zip': CabinetLights(
        PlayerLights(B=True, Y=True, Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'toobin.zip': CabinetLights(
        PlayerLights(B=True, A=True, L1=True, L2=True, R2=True, Select=True, Hotkey=True, Command=True)),
    'wacko.zip': CabinetLights(
        PlayerLights(Start=True, Select=True, Hotkey=True, Command=True), True, False),
    'xybots.zip': CabinetLights(
        PlayerLights(A=True, L1=True, R1=True, Start=True, Select=True, Hotkey=True, Command=True), True, True, PlayerLights(A=True, Y=True, X=True, Start=True, Select=True))
}

# Methods for exporting light dictionaries to JSON.
# Only the required attributes are in the output.
# The intent was to minimize the amount of data needed in the JSON, similar to how the class can be defined.
class SimpleLights:
    def __init__(self, player1Lights=None, isTwoPlayerGame=True, isTwoControllerGame=True, player2Lights=None):
        self.player1Lights = player1Lights
        self.isTwoPlayerGame = isTwoPlayerGame
        self.isTwoControllerGame = isTwoControllerGame
        self.player2Lights = player2Lights

sysLights = {}
for system, lights in systemLights.items():
    player1 = []
    for v in vars(lights.player1Lights):
        if getattr(lights.player1Lights, v):
            player1.append(v)
    player2 = []
    if lights.player2Lights is not None:
        for v in vars(lights.player2Lights):
            if getattr(lights.player2Lights, v):
                player2.append(v)
    if not player2:
        player2 = None
    sysLights[system] = SimpleLights(player1, lights.isTwoPlayerGame, lights.isTwoPlayerGame, player2).__dict__

print(json.dumps(sysLights, indent=4))

# Methods for exporting light dictionaries as JSON.
# All attributes are defined in the output.
# The intent is to make the output simple to maintain.
print(json.dumps(systemLights, default=lambda o: o.__dict__, indent=4))

print(json.dumps(gameLights, default=lambda o: o.__dict__, indent=4))


# with open(path / 'Amiacs-Trackball-Games.json') as file:
#     trackballGames = json.load(file)

# logging.basicConfig(
#     filename=path / 'Amiacs-Event-Processor.log', level=logging.INFO)

# bus = smbus.SMBus(1)
# address = 0x07

# parser = argparse.ArgumentParser(
#     'Given event information, send a command to the Amiacs light controller.')
# parser.add_argument('event', choices=[
#                     'game-start', 'game-end', 'screensaver-start', 'screensaver-stop'], help='the event that has occurred')
# parser.add_argument(
#     'system', help='the system (eg: atari2600, nes, snes, megadrive, fba, etc)')
# parser.add_argument(
#     'emulator', help='the emulator (eg: lr-stella, lr-fceumm, lr-picodrive, pifba, etc)')
# parser.add_argument('rompath', help='the full path to the rom file')
# parser.add_argument(
#     'commandline', help='the full command line used to launch the emulator')

# args = parser.parse_args()

# romname = os.path.basename(args.rompath)

# logging.info('--------')
# logging.info('Arguments:')
# logging.info('event: %s', args.event)
# logging.info('system: %s', args.system)
# logging.info('emulator: %s', args.emulator)
# logging.info('rom name: %s', romname)
# logging.info('rompath: %s', args.rompath)
# logging.info('commandline: %s', args.commandline)

# if args.event == 'game-start':
#     if romname.lower() in gameLights:
#         logging.info('Configuring lights for game %s.', romname)
#         lights = gameLights[romname.lower()]
#     elif args.system.lower() in systemLights:
#         logging.info('Configuring lights for system %s.', args.system)
#         lights = systemLights[args.system.lower()]
#     else:
#         logging.info('Configuring default lights.')
#         lights = systemLights['default']

#     if romname.lower() in trackballGames:
#         lights.usesTrackball = True

#     logging.info(lights)

#     bus.write_i2c_block_data(
#         address, DisplayMode.Game_Running.value, lights.I2CData())

# if args.event == 'game-end':
#     bus.write_byte(address, DisplayMode.Emulation_Station.value)

# if args.event == 'screensaver-start':
#     bus.write_byte(address, DisplayMode.Attract.value)

# if args.event == 'screensaver-stop':
#     bus.write_byte(address, DisplayMode.Emulation_Station.value)
