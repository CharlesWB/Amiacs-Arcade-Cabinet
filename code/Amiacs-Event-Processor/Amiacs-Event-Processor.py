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
import os
import smbus
from enum import Enum


# These values match what is found in Amiacs_Light_Controller.ino.
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
            Hotkey=Light.Off, Select=Light.Off, Start=Light.Off, Command=Light.Off):
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
        return '{}(\n        {})'.format(self.__class__.__name__, self.__dict__)

    # Returns the lights in a list. The order matches what Amiacs_Light_Controller.ino will expect.
    def I2CData(self):
        return [self.B.I2CData(), self.A.I2CData(), self.Y.I2CData(), self.X.I2CData(), self.L2.I2CData(), self.R2.I2CData(),
                self.L1.I2CData(), self.R1.I2CData(), self.Select.I2CData(), self.Start.I2CData(), self.Command.I2CData(), self.Hotkey.I2CData()]


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
        return self.player1Lights.I2CData() + self.player2Lights.I2CData() + [1 if self.usesTrackball else 0] + [1 if self.isTwoPlayerGame else 0]


trackballGames = [
    "720.zip",
    "aburner2.zip",
    "aburner.zip",
    "alien3.zip",
    "amspdwy.zip",
    "apb.zip",
    "arcadecl.zip",
    "arkanoid.zip",
    "arkatour.zip",
    "arknoid2.zip",
    "arkretrn.zip",
    "ataxx.zip",
    "beezer.zip",
    "bking2.zip",
    "bking3.zip",
    "bking.zip",
    "blaster.zip",
    "cameltry.zip",
    "capbowl.zip",
    "ccastles.zip",
    "centiped.zip",
    "champbwl.zip",
    "chasehq.zip",
    "chqflag.zip",
    "contcirc.zip",
    "countryc.zip",
    "csprint.zip",
    "dblaxle.zip",
    "dunkshot.zip",
    "ebases.zip",
    "esb.zip",
    "gghost.zip",
    "gimeabrk.zip",
    "gloc.zip",
    "gridiron.zip",
    "gt2k.zip",
    "gt3d.zip",
    "gt97.zip",
    "gt98.zip",
    "gt99.zip",
    "gtclassc.zip",
    "gtg2.zip",
    "gtg.zip",
    "hangon.zip",
    "hangonjr.zip",
    "hcrash.zip",
    "horshoes.zip",
    "hotrod.zip",
    "hydra.zip",
    "ikarijpb.zip",
    "indyheat.zip",
    "irrmaze.zip",
    "jedi.zip",
    "jpark.zip",
    "kick.zip",
    "konamigt.zip",
    "krzybowl.zip",
    "le2.zip",
    "liberatr.zip",
    "marble.zip",
    "mhavoc.zip",
    "milliped.zip",
    "minigolf.zip",
    "missile.zip",
    "mjleague.zip",
    "nightstr.zip",
    "offroad.zip",
    "offroadt.zip",
    "opwolf.zip",
    "othunder.zip",
    "outrun.zip",
    "paperboy.zip",
    "polepos2.zip",
    "polepos.zip",
    "poundfor.zip",
    "quantum.zip",
    "rachero.zip",
    "redbaron.zip",
    "roadblst.zip",
    "sbrkout.zip",
    "shangon.zip",
    "sharrier.zip",
    "shuuz.zip",
    "spiker.zip",
    "spyhunt2.zip",
    "spyhunt.zip",
    "ssprint.zip",
    "startrek.zip",
    "starwars.zip",
    "superchs.zip",
    "syvalion.zip",
    "teedoff.zip",
    "tempest.zip",
    "toutrun.zip",
    "wacko.zip",
    "wcbowl.zip",
    "wcbowldx.zip"]

systemLights = {
    'default': CabinetLights(PlayerLights(B=Light.On, A=Light.On), False, False),
    '3do': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'amigacd32': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'arcade': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Y=Light.On, X=Light.On, L2=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'atari800': CabinetLights(
        PlayerLights(B=Light.On, Hotkey=Light.On, Command=Light.On)),
    'atari2600': CabinetLights(
        PlayerLights(B=Light.On, Hotkey=Light.On, Command=Light.On)),
    'atari5200': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'atari7800': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'atarijaguar': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Y=Light.On, X=Light.On, L2=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'atomiswave': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Y=Light.On, X=Light.On, L2=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'c64': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Hotkey=Light.On, Command=Light.On)),
    'coleco': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Hotkey=Light.On, Command=Light.On)),
    'daphne': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R2=Light.On, Select=Light.On, Start=Light.On, Command=Light.On), False),
    'dreamcast': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'famicom': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'fds': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'gamegear': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'gb': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'gba': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'gbc': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'genesis': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'intellivision': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'markiii': CabinetLights(
        PlayerLights(B=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'mastersystem': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'megadrive': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'megadrivej': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'n64': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'naomi': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Y=Light.On, X=Light.On, L2=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'nds': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Y=Light.On, X=Light.On, L2=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'neogeo': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'neogeocd': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'nes': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'nesh': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'openbor': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Start=Light.On)),
    'pc': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On), False, False),
    'pcengine': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'ps2': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'psp': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'pspminis': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'psx': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'scummvm': CabinetLights(
        PlayerLights(B=Light.On, L2=Light.On, R2=Light.On), False, False),
    'sega32x': CabinetLights(
        PlayerLights(B=Light.On, X=Light.On, Y=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'segacd': CabinetLights(
        PlayerLights(B=Light.On, X=Light.On, Y=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'segah': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'sg-1000': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'snes': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'snescd': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On)),
    'turbografx16': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'virtualboy': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Select=Light.On, Start=Light.On, Hotkey=Light.On, Command=Light.On))
}

gameLights = {
    '1941.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    '1942.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    '1943.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    '1943kai.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    '1943mii.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    '1944.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    '19xx.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    '720.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    '88games.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    'aburner.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'aburner2.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'ace.daphne': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Y=Light.On, X=Light.On, L2=Light.On, R2=Light.On, Select=Light.On, Start=Light.On, Command=Light.On), False),
    'airwolf.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'alcon.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    'altbeast.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, X=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    'arcadecl.zip': CabinetLights(
        PlayerLights(B=Light.On, Y=Light.On, X=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    'arkanoid.zip': CabinetLights(
        PlayerLights(B=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'astdelux.zip': CabinetLights(
        PlayerLights(B=Light.On, Y=Light.On, X=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'asteroid.zip': CabinetLights(
        PlayerLights(B=Light.On, Y=Light.On, X=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'batman.zip': CabinetLights(
        PlayerLights(B=Light.On, Y=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'bwidow.zip': CabinetLights(
        PlayerLights(Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'bzone.zip': CabinetLights(
        PlayerLights(B=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'centiped.zip': CabinetLights(
        PlayerLights(A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'cliff.daphne': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Start=Light.On, Command=Light.On), False),
    'commando.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'csprint.zip': CabinetLights(
        PlayerLights(B=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    'ccastles.zip': CabinetLights(
        PlayerLights(B=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False, PlayerLights(B=Light.On, Select=Light.On)),
    'gauntlet2p.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, True, PlayerLights(B=Light.On, A=Light.On, Select=Light.On)),
    'gaunt2.zip': CabinetLights(
        PlayerLights(B=Light.On, Y=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    'gravitar.zip': CabinetLights(
        PlayerLights(B=Light.On, Y=Light.On, X=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'indytemp.zip': CabinetLights(
        PlayerLights(B=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'jedi.zip': CabinetLights(
        PlayerLights(B=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'lair.daphne': CabinetLights(
        PlayerLights(B=Light.On, Select=Light.On, Start=Light.On, Command=Light.On), False),
    'lair2.daphne': CabinetLights(
        PlayerLights(B=Light.On, Select=Light.On, Start=Light.On, Command=Light.On), False),
    'llander.zip': CabinetLights(
        PlayerLights(B=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'marble.zip': CabinetLights(
        PlayerLights(Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    'mhavoc.zip': CabinetLights(
        PlayerLights(B=Light.On, Y=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'milliped.zip': CabinetLights(
        PlayerLights(A=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'missile.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'pacman.zip': CabinetLights(
        PlayerLights(Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'paperboy.zip': CabinetLights(
        PlayerLights(B=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'polepos.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'polepos2.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'quantum.zip': CabinetLights(
        PlayerLights(Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'redbaron.zip': CabinetLights(
        PlayerLights(B=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'roadblst.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, X=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'robotron.zip': CabinetLights(
        PlayerLights(Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'spyhunt.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, R1=Light.On, Y=Light.On, X=Light.On, L2=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'starwars.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, Y=Light.On, X=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), False, False),
    'tempest.zip': CabinetLights(
        PlayerLights(B=Light.On, Y=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'toobin.zip': CabinetLights(
        PlayerLights(B=Light.On, A=Light.On, L1=Light.On, L2=Light.On, R2=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On)),
    'wacko.zip': CabinetLights(
        PlayerLights(Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, False),
    'xybots.zip': CabinetLights(
        PlayerLights(A=Light.On, L1=Light.On, R1=Light.On, Start=Light.On, Select=Light.On, Hotkey=Light.On, Command=Light.On), True, True, PlayerLights(A=Light.On, Y=Light.On, X=Light.On, Start=Light.On, Select=Light.On))
}

logging.basicConfig(
    filename='/home/pi/amiacs/Amiacs-Event-Processor.log', level=logging.INFO)

bus = smbus.SMBus(1)
address = 0x07

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

    if romname.lower() in trackballGames:
        lights.usesTrackball = True

    logging.info(lights)

    bus.write_i2c_block_data(
        address, DisplayMode.Game_Running.value, lights.I2CData())

if args.event == 'game-end':
    bus.write_byte(address, DisplayMode.Emulation_Station.value)

if args.event == 'screensaver-start':
    bus.write_byte(address, DisplayMode.Attract.value)

if args.event == 'screensaver-stop':
    bus.write_byte(address, DisplayMode.Emulation_Station.value)
