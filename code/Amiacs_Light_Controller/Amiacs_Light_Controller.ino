/*
Ideas:
- I2C command data and related methods could be a separate class.
- The player buttons flicker when using FastLED.show() and no changes were made.
  Is that an error in TLC5947SingleColorController or normal? Right now this code gets
  around this by not calling show() when no colors change.
*/

#define FASTLED_INTERNAL

#include <Adafruit_TLC5947.h>
#include <FastLED.h>
#include <Wire.h>
#include "SingleTriColorLEDController.h"
#include "TLC5947SingleColorController.h"


// General definitions.
// Can only be 2. No other values have been implemented.
#define NUM_PLAYERS 2
// Can only be 1. No other values have been implemented.
#define NUM_TRACKBALLS 1
// Can only be 2. No other values have been implemented.
#define NUM_AMBIENT_LEDS 2


// Pin definitions.
#define PLAYER_LIGHTS_LATCH_PIN 10
#define PLAYER_LIGHTS_DATA_PIN 12
#define PLAYER_LIGHTS_CLOCK_PIN 13
#define PLAYER_LIGHTS_OUTPUT_ENABLE_PIN = 8
#define TRACKBALL_RED_PIN 3
#define TRACKBALL_GREEN_PIN 5
#define TRACKBALL_BLUE_PIN 6
#define MARQUEE_LIGHT_PIN 9
#define AMBIENT_LIGHT_DATA_PIN 11
#define AMBIENT_LIGHT_CLOCK_PIN 13
#define BRIGHTNESS_PIN A7


// Player button pin numbers for the Adafruit TLC5947.
#define NUM_PLAYER_LIGHTS 24
#define PLAYER1_LIGHT_B 0
#define PLAYER1_LIGHT_A 1
#define PLAYER1_LIGHT_Y 2
#define PLAYER1_LIGHT_X 3
#define PLAYER1_LIGHT_L2 4
#define PLAYER1_LIGHT_R2 5
#define PLAYER1_LIGHT_L1 6
#define PLAYER1_LIGHT_R1 7
#define PLAYER1_LIGHT_SELECT 8
#define PLAYER1_LIGHT_START 9
#define PLAYER1_LIGHT_COMMAND 10
#define PLAYER1_LIGHT_HOTKEY 11
#define PLAYER2_LIGHT_B 12
#define PLAYER2_LIGHT_A 13
#define PLAYER2_LIGHT_Y 14
#define PLAYER2_LIGHT_X 15
#define PLAYER2_LIGHT_L2 16
#define PLAYER2_LIGHT_R2 17
#define PLAYER2_LIGHT_L1 18
#define PLAYER2_LIGHT_R1 19
#define PLAYER2_LIGHT_SELECT 20
#define PLAYER2_LIGHT_START 21
#define PLAYER2_LIGHT_COMMAND 22
#define PLAYER2_LIGHT_HOTKEY 23

#define PLAYER_ALL_LIGHTS_LAYOUT_ROWS 3
#define PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS 11
#define PLAYER1_ALL_LIGHTS_LAYOUT_COLUMNS 6
#define PLAYER2_ALL_LIGHTS_LAYOUT_COLUMNS 5

int playerAllLightLayout[PLAYER_ALL_LIGHTS_LAYOUT_ROWS][PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS] =
{
  {-1, PLAYER1_LIGHT_SELECT, PLAYER1_LIGHT_START, PLAYER1_LIGHT_COMMAND, -1, -1, PLAYER2_LIGHT_COMMAND, -1, PLAYER2_LIGHT_SELECT, PLAYER2_LIGHT_START, -1},
  {-1, -1, PLAYER1_LIGHT_Y, PLAYER1_LIGHT_X, PLAYER1_LIGHT_L2, PLAYER1_LIGHT_R2, PLAYER2_LIGHT_Y, PLAYER2_LIGHT_X, PLAYER2_LIGHT_L2, PLAYER2_LIGHT_R2, -1},
  {PLAYER1_LIGHT_HOTKEY, -1, PLAYER1_LIGHT_B, PLAYER1_LIGHT_A, PLAYER1_LIGHT_L1, PLAYER1_LIGHT_R1, PLAYER2_LIGHT_B, PLAYER2_LIGHT_A, PLAYER2_LIGHT_L1, PLAYER2_LIGHT_R1, PLAYER2_LIGHT_HOTKEY}
};

#define PLAYER_PRIMARY_LIGHTS_LAYOUT_ROWS 2
#define PLAYER_PRIMARY_LIGHTS_LAYOUT_COLUMNS 8

int playerPrimaryLightLayout[PLAYER_PRIMARY_LIGHTS_LAYOUT_ROWS][PLAYER_PRIMARY_LIGHTS_LAYOUT_COLUMNS] =
{
  {PLAYER1_LIGHT_Y, PLAYER1_LIGHT_X, PLAYER1_LIGHT_L2, PLAYER1_LIGHT_R2, PLAYER2_LIGHT_Y, PLAYER2_LIGHT_X, PLAYER2_LIGHT_L2, PLAYER2_LIGHT_R2},
  {PLAYER1_LIGHT_B, PLAYER1_LIGHT_A, PLAYER1_LIGHT_L1, PLAYER1_LIGHT_R1, PLAYER2_LIGHT_B, PLAYER2_LIGHT_A, PLAYER2_LIGHT_L1, PLAYER2_LIGHT_R1}
};

// Although the color of the player lights is defined by the button plastic,
// for FastLED the player light color is white so that it is fully lit.
const CHSV playerLightColor = CHSV(0, 0, 255);

const CHSV defaultSystemColor = CHSV(24, 255, 255);
CRGB playerColors[NUM_PLAYERS] = {CRGB::Blue, CRGB::Red};
CHSV playerColorsHSV[NUM_PLAYERS] = {rgb2hsv_approximate(playerColors[0]), rgb2hsv_approximate(playerColors[1])};

// The intent for this palette is to cycle between the player colors.
CRGBPalette16 playerColorPalette = CRGBPalette16(
  playerColors[0], playerColors[0], playerColors[0], playerColors[0],
  playerColors[0], playerColors[0], playerColors[0], playerColors[0],
  playerColors[1], playerColors[1], playerColors[1], playerColors[1],
  playerColors[1], playerColors[1], playerColors[1], playerColors[1]
);

CRGB playerLights[NUM_PLAYER_LIGHTS];
CRGB trackballs[NUM_TRACKBALLS];
CRGB ambientLights[NUM_AMBIENT_LEDS];


// I2C communications between the Arduino and the Raspberry Pi.
// Data format:
// - 1 byte for the command. The command value is the same as the DisplayMode enum.
// - Data for game running display mode:
//   - 12 bytes for player 1 lights. In same order as Adafruit TLC5947 pins defined above. Non-zero value indicates light is on.
//   - 12 bytes for player 2 lights. In same order as Adafruit TLC5947 pins defined above. Non-zero value indicates light is on.
//   - 1 byte for trackball. Non-zero value indicates trackball light is on.
//   - 1 byte to indicate that the game has two separate player controls.
// Any additional data is read but ignored.
#define SLAVE_ADDRESS 0x07
#define COMMAND_ARRAY_SIZE NUM_PLAYER_LIGHTS + NUM_TRACKBALLS + 1
#define COMMAND_TRACKBALL_INDEX COMMAND_ARRAY_SIZE - 2
#define COMMAND_TWO_CONTROLS_INDEX COMMAND_ARRAY_SIZE - 1
byte command = 0;
byte commandData[COMMAND_ARRAY_SIZE];


// These values match what is found in Amiacs-Event-Processor.py.
enum DisplayMode {
  // Mode used while system starts.
  STARTING = 0,
  // Mode used when Emulation Station displays a screensaver.
  ATTRACT = 1,
  // Mode used when the Emulation Station is running.
  EMULATION_STATION = 2,
  // Mode used when a game system is running.
  GAME_RUNNING = 3,
};

DisplayMode displayMode = STARTING;

// For each DisplayMode, identify if an initialization must be done while running in loop.
// NOTE: This is manually sized to match the number of DisplayModes.
int initializeDisplayMode[] = {false, true, true, true};

// The attract DisplayMode has an additional initialization step for the brightness.
bool initializeAttractDisplayModeBrightness = true;

enum AttractDisplayMode {
  RANDOM_BLINK,
  CYLON,
  IN_TO_CENTER,
  NUM_ATTRACT_DISPLAY_MODES,
};

AttractDisplayMode attractDisplayMode = random8(NUM_ATTRACT_DISPLAY_MODES);


void setup() {
  Serial.begin(9600);

  // There's a short delay between when the Arduino starts and when the button
  // encoder and the Adafruit TLC5947 boards get power from the Raspberry Pi.
  // We'll wait for that so that the TLC5947 will be properly initialized.
  delay(5000);

  SetBrightness();

  SetupPlayerLights();
  SetupTrackballLights();
  SetupAmbientLights();
  SetupMarqueeLights();

  TestLightsDuringSetup();

  Wire.begin(SLAVE_ADDRESS);
  Wire.onReceive(CommandReceiveEvent);

  SetLightsToSystemDefaultColor();

  FastLED.show();
}

void loop() {
  switch(displayMode) {
    case STARTING:
      LoopStartingDisplayMode();
      break;
    case ATTRACT:
      LoopAttractDisplayMode();
      break;
    case EMULATION_STATION:
      LoopEmulationStationDisplayMode();
      break;
    case GAME_RUNNING:
      LoopGameRunningDisplayMode();
      break;
  }
}


// The display mode during startup is a type of attract mode.
// The lights are expected to have been turned on to their default colors prior to this.
// This will fade the brightness in and out at an increasing rate then pause before switching to Emulation Station mode.
// The typical time from power on to Emulation Station start is about one minute.
void LoopStartingDisplayMode() {
  static unsigned long startTime = millis();

  static unsigned long startingStepTimeline[] = {0, 5000, 9900, 14700, 19200, 23200, 26700, 29600, 31900, 33400, 34200, 34800, 35400, 36000, 36400, 45000};
  uint8_t stepCount = (sizeof(startingStepTimeline) / sizeof(startingStepTimeline[0]));

  SetBrightness();

  unsigned long now = millis() - startTime;
  uint8_t step = 0;
  for(uint8_t i = 0; i < stepCount; i++) {
    if(now > startingStepTimeline[i]) {
      step = i;
    }
  }

  if(step < stepCount - 2) {
    uint8_t frame = map(now, startingStepTimeline[step], startingStepTimeline[step + 1], 255, 0);

    // Offset the frame by 128 so that the brightness starts at 255.
    uint8_t brightness = quadwave8(frame + 128);

    if(playerLights[0] != CHSV(playerLightColor.hue, playerLightColor.sat, brightness)) {
      fill_solid(playerLights, NUM_PLAYER_LIGHTS, CHSV(playerLightColor.hue, playerLightColor.sat, brightness));
      fill_solid(trackballs, NUM_TRACKBALLS, CHSV(defaultSystemColor.hue, defaultSystemColor.sat, brightness));
      fill_solid(ambientLights, NUM_AMBIENT_LEDS, CHSV(defaultSystemColor.hue, defaultSystemColor.sat, brightness));
      FastLED.show();
      SetMarqueeBrightness(brightness);
    }
  }
  else if(step < stepCount - 1) {
    if(playerLights[0] != playerLightColor) {
      fill_solid(playerLights, NUM_PLAYER_LIGHTS, playerLightColor);
      fill_solid(trackballs, NUM_TRACKBALLS, defaultSystemColor);
      fill_solid(ambientLights, NUM_AMBIENT_LEDS, defaultSystemColor);
      FastLED.show();
    }
  }
  else {
    displayMode = EMULATION_STATION;
    initializeDisplayMode[EMULATION_STATION] = true;
  }
}

void LoopEmulationStationDisplayMode() {
  static unsigned long startTime = millis();

  SetBrightness();

  if(initializeDisplayMode[EMULATION_STATION]) {
    startTime = millis();

    EmulationStationDisplayModeInitialize();

    initializeDisplayMode[EMULATION_STATION] = false;
  }
}

void EmulationStationDisplayModeInitialize() {
  fill_solid(playerLights, NUM_PLAYER_LIGHTS, playerLightColor);

  playerLights[PLAYER1_LIGHT_L2] = CRGB::Black;
  playerLights[PLAYER1_LIGHT_R2] = CRGB::Black;
  playerLights[PLAYER1_LIGHT_COMMAND] = CRGB::Black;
  playerLights[PLAYER1_LIGHT_HOTKEY] = CRGB::Black;
  playerLights[PLAYER2_LIGHT_L2] = CRGB::Black;
  playerLights[PLAYER2_LIGHT_R2] = CRGB::Black;
  playerLights[PLAYER2_LIGHT_COMMAND] = CRGB::Black;
  playerLights[PLAYER2_LIGHT_HOTKEY] = CRGB::Black;

  fill_solid(trackballs, NUM_TRACKBALLS, CRGB::Black);

  fill_solid(ambientLights, NUM_AMBIENT_LEDS, defaultSystemColor);

  FastLED.show();
}

void LoopGameRunningDisplayMode() {
  SetBrightness();

  if(initializeDisplayMode[GAME_RUNNING]) {
    GameRunningDisplayModeInitialize();

    initializeDisplayMode[GAME_RUNNING] = false;
  }

  if(CommandIsTrackballOn() && CommandIsTwoControllerGame()) {
    CycleTrackballBetweenPlayerColors();
  }
}

void GameRunningDisplayModeInitialize() {
  for(int light = 0; light < NUM_PLAYER_LIGHTS; light++) {
    if(commandData[light] != 0) {
      playerLights[light] = playerLightColor;
    }
    else {
      playerLights[light] = CRGB::Black;
    }
  }

  if(CommandIsTrackballOn()) {
    fill_solid(trackballs, NUM_TRACKBALLS, playerColors[0]);
  }
  else {
    fill_solid(trackballs, NUM_TRACKBALLS, CRGB::Black);
  }

  fill_solid(ambientLights, NUM_AMBIENT_LEDS, defaultSystemColor);

  FastLED.show();
}

// Randomly alternate between the various attract display modes.
// Dim the lights over time. At a low level completely turn off the lights.
void LoopAttractDisplayMode() {
  const static unsigned long duration = 120000;
  const static unsigned long dimmingDuration = 2 * duration;

  static unsigned long startTime = millis();
  static unsigned long dimmingStartTime = millis();

  static float brightnessFactor = 1;

  if(initializeAttractDisplayModeBrightness) {
    dimmingStartTime = millis();

    brightnessFactor = 1;

    initializeAttractDisplayModeBrightness = false;
  }

  if(initializeDisplayMode[ATTRACT]) {
    startTime = millis();

    AttractDisplayModeInitialize();

    initializeDisplayMode[ATTRACT] = false;
  }

  if(brightnessFactor > .2) {
    SetBrightness(brightnessFactor);

    unsigned long dimmingNow = millis() - dimmingStartTime;
    if(dimmingNow > dimmingDuration) {
      brightnessFactor *= .6;
      dimmingStartTime = millis();
    }

    unsigned long now = millis() - startTime;
    if(now <= duration) {
      if(attractDisplayMode == RANDOM_BLINK) {
        AttractDisplayModeRandomBlink();
      }
      else if(attractDisplayMode == CYLON) {
        AttractDisplayModeCylon();
      }
      else if(attractDisplayMode == IN_TO_CENTER) {
        AttractDisplayModeInToCenter();
      }

      FastLED.show();
    }
    else {
      AttractDisplayMode nextAttractDisplayMode = random8(NUM_ATTRACT_DISPLAY_MODES);
      if(nextAttractDisplayMode != attractDisplayMode) {
        attractDisplayMode = nextAttractDisplayMode;
        initializeDisplayMode[ATTRACT] = true;
      }
    }
  }
  else {
    fill_solid(playerLights, NUM_PLAYER_LIGHTS, CRGB::Black);
    fill_solid(trackballs, NUM_TRACKBALLS, CRGB::Black);
    fill_solid(ambientLights, NUM_AMBIENT_LEDS, CRGB::Black);
    SetMarqueeBrightness(0);

    FastLED.show();
  }
}

void AttractDisplayModeInitialize() {
  fill_solid(playerLights, NUM_PLAYER_LIGHTS, CRGB::Black);
  fill_solid(trackballs, NUM_TRACKBALLS, CRGB::Black);
  fill_solid(ambientLights, NUM_AMBIENT_LEDS, CRGB::Black);

  FastLED.show();
}

// Cycle columns in to the center and back, fading out the other columns.
// Fade the trackball in sync with the cycle.
// Fade in and out each side of the ambient lights to match the cycling player colors.
void AttractDisplayModeInToCenter() {
  const static unsigned long duration = 2400;

  static unsigned long startTime = millis();

  unsigned long now = millis() - startTime;

  unsigned long elapsed = now - (duration * (now / duration));
  int player1Column = elapsed / (duration / (2 * PLAYER1_ALL_LIGHTS_LAYOUT_COLUMNS));
  if(player1Column >= PLAYER1_ALL_LIGHTS_LAYOUT_COLUMNS) {
    player1Column = (2 * PLAYER1_ALL_LIGHTS_LAYOUT_COLUMNS) - player1Column - 1;
  }

  int player2Column = elapsed / (duration / (2 * PLAYER2_ALL_LIGHTS_LAYOUT_COLUMNS));
  if(player2Column >= PLAYER2_ALL_LIGHTS_LAYOUT_COLUMNS) {
    player2Column = (2 * PLAYER2_ALL_LIGHTS_LAYOUT_COLUMNS) - player2Column - 1;
  }

  for(uint8_t column = 0; column < PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS; column++) {
    for(uint8_t row = 0; row < PLAYER_ALL_LIGHTS_LAYOUT_ROWS; row++) {
      if(playerAllLightLayout[row][column] >= 0) {
        if(column == player1Column || column == PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS - player2Column - 1) {
          playerLights[playerAllLightLayout[row][column]] = playerLightColor;
        }
        else {
          playerLights[playerAllLightLayout[row][column]].nscale8(250);
        }
      }
    }
  }

  if(elapsed > duration / 2) {
    elapsed = duration - elapsed;
  }
  fill_solid(trackballs, NUM_TRACKBALLS, CHSV(defaultSystemColor.hue, defaultSystemColor.sat, map(elapsed, 0, duration / 2, 20, 255)));

  ambientLights[0] = CHSV(playerColorsHSV[0].hue, playerColorsHSV[0].sat, map(elapsed, 0, duration / 2, 50, 255));
  ambientLights[1] = CHSV(playerColorsHSV[1].hue, playerColorsHSV[1].sat, map(elapsed, 0, duration / 2, 50, 255));
}

// Cycle back and forth through the columns, fading out the other columns.
// Cycle the trackball between player colors.
// Fade in and out each side of the ambient lights to match the cycling player colors.
// Duration is for the full cycle, which is divided into four parts.
// First part moves left to right through player 1.
// Second part moves left to right through player 2.
// Third part moves right to left through player 2.
// Fourth part moves right to left through player 1.
// Note that the player columns may not be an equal amount. So duration is not evenly divided between the two players.
void AttractDisplayModeCylon() {
  const static unsigned long durationPerColumn = 125;
  const static unsigned long duration = durationPerColumn * 2 * PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS;
  const static unsigned long player1Duration = durationPerColumn * PLAYER1_ALL_LIGHTS_LAYOUT_COLUMNS;
  const static unsigned long player2Duration = durationPerColumn * PLAYER2_ALL_LIGHTS_LAYOUT_COLUMNS;

  static unsigned long startTime = millis();

  unsigned long now = millis() - startTime;

  unsigned long elapsed = now - (duration * (now / duration));
  int playerColumn = elapsed / (duration / (2 * PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS));
  if(playerColumn >= PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS) {
    playerColumn = (2 * PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS) - playerColumn - 1;
  }

  for(uint8_t column = 0; column < PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS; column++) {
    for(uint8_t row = 0; row < PLAYER_ALL_LIGHTS_LAYOUT_ROWS; row++) {
      if(playerAllLightLayout[row][column] >= 0) {
        if(playerColumn == column) {
          playerLights[playerAllLightLayout[row][column]] = playerLightColor;
        }
        else {
          playerLights[playerAllLightLayout[row][column]].nscale8(250);
        }
      }
    }
  }

  if(playerColumn < PLAYER1_ALL_LIGHTS_LAYOUT_COLUMNS) {
    fill_solid(trackballs, NUM_TRACKBALLS, playerColors[0]);

    // Example:
    // If duration is 100 and player columns are equal then
    // player 1 runs from 0 to 25 (player1Duration) and 75 (delta is 2 * player2Duration) to 100.
    // This is converted to 25 (player1Duration) to 0 and back to 25.
    unsigned long playerElapsed = player1Duration - elapsed;
    if(elapsed >= player1Duration) {
      playerElapsed = player1Duration - (duration - elapsed);
    }

    ambientLights[0] = CHSV(playerColorsHSV[0].hue, playerColorsHSV[0].sat, map(playerElapsed, 0, player1Duration, 50, 255));
    ambientLights[1] = CRGB::Black;
  }
  else {
    fill_solid(trackballs, NUM_TRACKBALLS, playerColors[1]);

    // Example:
    // If duration is 100 and player columns are equal then
    // player 2 runs from 25 (player1Duration) to 75 (delta is 2 * player2Duration).
    // This is converted to 0 to 25 (player2Duration) and back to 0.
    unsigned long playerElapsed = elapsed - player1Duration;
    if(elapsed >= duration - player1Duration - player2Duration) {
      playerElapsed = duration - elapsed - player1Duration;
    }

    ambientLights[0] = CRGB::Black;
    ambientLights[1] = CHSV(playerColorsHSV[1].hue, playerColorsHSV[1].sat, map(playerElapsed, 0, player2Duration, 50, 255));
  }
}

// Randomly blink the player lights.
// Randomly change the color of the trackball.
// Randomly change the color of the ambient per side.
void AttractDisplayModeRandomBlink() {
  static unsigned long startTime = millis();

  int playerLight = random8(NUM_PLAYER_LIGHTS);
  int on = random8(100);
  if(on > 50) {
    playerLights[playerLight] = playerLightColor;
  }
  else {
    playerLights[playerLight] = CRGB::Black;
  }

  if(millis() - startTime > 500) {
    CRGB color = ColorFromPalette(RainbowColors_p, random8(240), 255, LINEARBLEND);
    fill_solid(trackballs, NUM_TRACKBALLS, color);

    ambientLights[0] = ColorFromPalette(RainbowColors_p, random8(240), 255, LINEARBLEND);
    ambientLights[1] = ColorFromPalette(RainbowColors_p, random8(240), 255, LINEARBLEND);

    startTime = millis();
  }
}


// *** I2C Command Processing ***

void CommandReceiveEvent(int byteCount) {
  if(Wire.available()) {
    command = Wire.read();

    memset(commandData, 0, sizeof(commandData));

    int dataIndex = 0;
    while(Wire.available()) {
      byte data = Wire.read();

      // The command data array is a certain size. I'm not going to
      // assume the data size matches the array size. Any excess data
      // will simply be read and ignored.
      if(dataIndex < COMMAND_ARRAY_SIZE) {
        commandData[dataIndex] = data;
      }

      dataIndex++;
    }

    displayMode = (DisplayMode)command;
    initializeDisplayMode[displayMode] = true;
    initializeAttractDisplayModeBrightness = true;
  }
}

bool CommandIsTrackballOn() {
  return commandData[COMMAND_TRACKBALL_INDEX] != 0;
}

bool CommandIsTwoControllerGame() {
  return commandData[COMMAND_TWO_CONTROLS_INDEX] != 0;
}


// *** Cabinet Lights ***

void SetLightsToSystemDefaultColor() {
  fill_solid(playerLights, NUM_PLAYER_LIGHTS, playerLightColor);
  fill_solid(trackballs, NUM_TRACKBALLS, defaultSystemColor);
  fill_solid(ambientLights, NUM_AMBIENT_LEDS, defaultSystemColor);
  FastLED.show();
  SetMarqueeBrightness(GetBrightness());
}

void TestLightsDuringSetup() {
  fill_solid(playerLights, NUM_PLAYER_LIGHTS, CRGB::White);

  fill_solid(trackballs, NUM_TRACKBALLS, CRGB::Red);
  fill_solid(ambientLights, NUM_AMBIENT_LEDS, CRGB::Red);
  FastLED.show();
  delay(1000);

  fill_solid(trackballs, NUM_TRACKBALLS, CRGB::Green);
  fill_solid(ambientLights, NUM_AMBIENT_LEDS, CRGB::Green);
  FastLED.show();
  delay(1000);

  fill_solid(trackballs, NUM_TRACKBALLS, CRGB::Blue);
  fill_solid(ambientLights, NUM_AMBIENT_LEDS, CRGB::Blue);
  FastLED.show();
  delay(1000);
}


// *** Player Lights ***

void SetupPlayerLights() {
  static TLC5947SingleColorController<PLAYER_LIGHTS_DATA_PIN, PLAYER_LIGHTS_CLOCK_PIN, PLAYER_LIGHTS_LATCH_PIN> playerLightController;
  FastLED.addLeds(&playerLightController, playerLights, NUM_PLAYER_LIGHTS);
}


// *** Trackball Lights ***

void SetupTrackballLights() {
  static SingleTriColorLEDController<TRACKBALL_RED_PIN, TRACKBALL_GREEN_PIN, TRACKBALL_BLUE_PIN> trackballLEDController;
  FastLED.addLeds(&trackballLEDController, trackballs, NUM_TRACKBALLS).setCorrection(0xC0FFE0);
}

void CycleTrackballBetweenPlayerColors() {
  static unsigned long startTime = millis();

  static uint8_t playerColorPaletteIndex = 0;

  // 40 ms per step is approximately 10 seconds over 256 steps.
  if(millis() - startTime > 40) {
    fill_solid(trackballs, NUM_TRACKBALLS, ColorFromPalette(playerColorPalette, playerColorPaletteIndex));

    // TODO Remove the hard-coding of the trackball LEDs index. Or resolve flicker when updating player lights using FastLED.show().
    FastLED[1].showLedsInternal(GetBrightness());

    playerColorPaletteIndex++;

    startTime = millis();
  }
}


// *** Ambient Lights ***

void SetupAmbientLights() {
  FastLED.addLeds<P9813, AMBIENT_LIGHT_DATA_PIN, AMBIENT_LIGHT_CLOCK_PIN, RBG>(ambientLights, NUM_AMBIENT_LEDS).setCorrection(0xFF90FF);
}


// *** Marquee Lights ***

void SetupMarqueeLights() {
  pinMode(MARQUEE_LIGHT_PIN, OUTPUT);
}

void SetMarqueeBrightness(uint8_t brightness) {
  analogWrite(MARQUEE_LIGHT_PIN, brightness);
}


// *** Brightness ***

uint8_t GetBrightness() {
  static float brightness = -1;

  float dampingCoefficient = .1;

  // The first time this is called, the analogRead value will be used directly.
  if(brightness == -1) {
    dampingCoefficient = 1;
    brightness = 0;
  }

  int value = map(analogRead(BRIGHTNESS_PIN), 0, 1023, 0, 255);

  // Uses exponential smoothing.
  // References:
  // https://en.wikipedia.org/wiki/Exponential_smoothing#Basic_(simple)_exponential_smoothing_(Holt_Linear)
  // https://www.megunolink.com/articles/coding/3-methods-filter-noisy-arduino-measurements/
  brightness += (dampingCoefficient * (value - brightness));

  if(brightness >= 254) {
    brightness = 255;
  }

  return brightness;
}

void SetBrightness() {
  SetBrightness(1);
}

void SetBrightness(const float factor) {
  uint8_t brightness = GetBrightness() * factor;
  if(FastLED.getBrightness() != brightness) {
    FastLED.setBrightness(brightness);
    FastLED.show();

    SetMarqueeBrightness(brightness);
  }
}


// *** Debug ***

void Debug_PrintColorInformation(const struct CRGB &color) {
  Serial.print("Red: ");
  Serial.print(color.red);
  Serial.print(", Green: ");
  Serial.print(color.green);
  Serial.print(", Blue: ");
  Serial.println(color.blue);
}
