/*
To Do:
- How should the color palette index be handled? Such as in CycleTrackballByPalette.

Ideas:
- Would a sine wave, breathe, heartbeat, or some kind of bounce effect for the cycle time make it interesting?
- The cycle time of brightness or color would be a rate such as steps/millisecond.
- DisplayMode may turn into the command byte of I2C. It would define the action to be done. Such as set or enable.
- Create a Brightness class that handles the differences between max levels for the TLC5947 and others.
-- Use 4095 (uint16_t) as maximum. Map all others from that value.
-- Allows setting a maximum. Possibly controlled by dimmer.
*/

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
// Can only be 1. No other values have been implemented.
#define NUM_AMBIENT_LEDS 1

#define SLAVE_ADDRESS 0x07

// Pin definitions.
#define PLAYER_LIGHTS_LATCH_PIN 10
#define PLAYER_LIGHTS_DATA_PIN 12
#define PLAYER_LIGHTS_CLOCK_PIN 13
#define TRACKBALL_RED_PIN 3
#define TRACKBALL_GREEN_PIN 5
#define TRACKBALL_BLUE_PIN 6
#define MARQUEE_LIGHT_PIN 9
#define AMBIENT_LIGHT_DATA_PIN 11
#define AMBIENT_LIGHT_CLOCK_PIN 13

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
#define PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS 12

int playerAllLightLayout[PLAYER_ALL_LIGHTS_LAYOUT_ROWS][PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS] =
{
  {-1, PLAYER1_LIGHT_SELECT, PLAYER1_LIGHT_START, -1, PLAYER1_LIGHT_COMMAND, -1, -1, PLAYER2_LIGHT_COMMAND, -1, PLAYER2_LIGHT_SELECT, PLAYER2_LIGHT_START, -1},
  {-1, -1, -1, PLAYER1_LIGHT_Y, PLAYER1_LIGHT_X, PLAYER1_LIGHT_L2, PLAYER1_LIGHT_R2, PLAYER2_LIGHT_Y, PLAYER2_LIGHT_X, PLAYER2_LIGHT_L2, PLAYER2_LIGHT_R2, -1},
  {PLAYER1_LIGHT_HOTKEY, -1, -1, PLAYER1_LIGHT_B, PLAYER1_LIGHT_A, PLAYER1_LIGHT_L1, PLAYER1_LIGHT_R1, PLAYER2_LIGHT_B, PLAYER2_LIGHT_A, PLAYER2_LIGHT_L1, PLAYER2_LIGHT_R1, PLAYER2_LIGHT_HOTKEY}
};

#define PLAYER_PRIMARY_LIGHTS_LAYOUT_ROWS 2
#define PLAYER_PRIMARY_LIGHTS_LAYOUT_COLUMNS 8

int playerPrimaryLightLayout[PLAYER_PRIMARY_LIGHTS_LAYOUT_ROWS][PLAYER_PRIMARY_LIGHTS_LAYOUT_COLUMNS] =
{
  {PLAYER1_LIGHT_Y, PLAYER1_LIGHT_X, PLAYER1_LIGHT_L2, PLAYER1_LIGHT_R2, PLAYER2_LIGHT_Y, PLAYER2_LIGHT_X, PLAYER2_LIGHT_L2, PLAYER2_LIGHT_R2},
  {PLAYER1_LIGHT_B, PLAYER1_LIGHT_A, PLAYER1_LIGHT_L1, PLAYER1_LIGHT_R1, PLAYER2_LIGHT_B, PLAYER2_LIGHT_A, PLAYER2_LIGHT_L1, PLAYER2_LIGHT_R1}
};

const CHSV defaultSystemColor = CHSV(HUE_ORANGE, 255, 255);
CRGB playerColors[NUM_PLAYERS] = {CRGB::Blue, CRGB::Red};

// The intent for this palette is to cycle through the player colors while a game is playing.
// Because we don't know when a specific player is playing so we show both colors.
CRGBPalette16 trackballPlayersPalette = CRGBPalette16(playerColors[0], playerColors[1]);

CRGB playerLights[NUM_PLAYER_LIGHTS];
CRGB trackballs[NUM_TRACKBALLS];
CRGB ambientLights[NUM_AMBIENT_LEDS];


enum DisplayMode {
  STARTING, // takes 60 seconds to get a running Emulation Station. 40 seconds of that is to play the intro video.
  ATTRACT,
  MUTE, // Or DIMMED, SCREENSAVER_ACTIVE
  GAME_PLAYING,
  GAME_PAUSED, // RetroPie may not provide a way to respond to paused games.
  TESTING,
};

DisplayMode displayMode = STARTING;


void setup() {
  Serial.begin(9600);

  // There's a short delay between when the Arduino starts and when the button
  // encoder and the Adafruit TLC5947 boards get power from the Raspberry Pi.
  // We'll wait for that so that the TLC5947 will be properly initialized.
  delay(5000);

  // TODO This could be read from a potentiometer.
  FastLED.setBrightness(255);

  SetupPlayerLights();
  SetupTrackballLights();
  SetupAmbientLights();
  SetupMarqueeLights();

  Wire.begin(SLAVE_ADDRESS);
  Wire.onReceive(receiveEvent);

  SetLightsToSystemDefaultColor();

  FastLED.show();
}

void loop() {
  // Temporary testing until display modes are implemented.
  // CyclePlayerLightsByColumn();
//  CycleTrackballByPalette();
//  CycleMarqueeBrightness();

  switch(displayMode) {
    case STARTING:
      LoopStartingDisplayMode();
      break;
    case ATTRACT:
      LoopAttractDisplayMode();
      break;
  }

  FastLED.show();
}

// The display mode during startup is about verifying that all the lights work.
// The lights are expected to have been turned on to their default colors during setup.
// This will:
// - Blink once. This is actually a very fast fade out and in.
// - Turn all lights on for a moment. Use this to verify they are all working.
// - Fade the brightness out and in as a simple test of functionality.
void LoopStartingDisplayMode() {
  static unsigned long startTime = millis();

  static unsigned long startingPhaseTimeline[] = {0, 2000, 3000, 7000, 11000, 12000};

  unsigned long now = millis() - startTime;
  byte phase = 0;
  for(byte i = 0; i < (sizeof(startingPhaseTimeline) / sizeof(startingPhaseTimeline[0])); i++) {
    if(now > startingPhaseTimeline[i]) {
      phase = i;
    }
  }

  uint16_t brightness;
  uint8_t frame;
  uint8_t value;

  switch(phase) {
    case 0:
      TurnOffAllPlayerLights();
      fill_solid(trackballs, NUM_TRACKBALLS, CRGB::Black);
      break;
    case 1:
      TurnOnAllPlayerLights();
      fill_solid(trackballs, NUM_TRACKBALLS, defaultSystemColor);
      break;
    case 2:
      frame = map(now, startingPhaseTimeline[phase], startingPhaseTimeline[phase + 1], 255, 0);
      brightness = quadwave8(frame);
      // SetAllPlayerLightsBrightness(brightness);

      fill_solid(playerLights, NUM_PLAYER_LIGHTS, CHSV(0, 0, brightness));
      fill_solid(trackballs, NUM_TRACKBALLS, CHSV(defaultSystemColor.hue, defaultSystemColor.sat, brightness));
      break;
    case 3:
      frame = map(now, startingPhaseTimeline[phase], startingPhaseTimeline[phase + 1], 0, 255);
      brightness = quadwave8(frame);
      // SetAllPlayerLightsBrightness(brightness);

      fill_solid(playerLights, NUM_PLAYER_LIGHTS, CHSV(0, 0, brightness));
      fill_solid(trackballs, NUM_TRACKBALLS, CHSV(defaultSystemColor.hue, defaultSystemColor.sat, brightness));
      break;
    case 4:
      fill_solid(playerLights, NUM_PLAYER_LIGHTS, CHSV(0, 0, 255));
      fill_solid(trackballs, NUM_TRACKBALLS, defaultSystemColor);
    case 5:
      displayMode = ATTRACT;
      break;
  }
}

void LoopAttractDisplayMode() {
  static unsigned long startTime = millis();

  int playerLight = random8(NUM_PLAYER_LIGHTS);
  int on = random8(100);
  if(on > 50) {
    playerLights[playerLight] = CRGB::White;
  }
  else {
    playerLights[playerLight] = CRGB::Black;
  }

  if(millis() - startTime > 500) {
    CRGB color = ColorFromPalette(RainbowColors_p, random8(240), 255, NOBLEND);
    fill_solid(trackballs, NUM_TRACKBALLS, color);

    startTime = millis();
  }
}

void receiveEvent(int byteCount) {

}

void SetLightsToSystemDefaultColor() {
  fill_solid(playerLights, NUM_PLAYER_LIGHTS, CRGB::White);
  fill_solid(trackballs, NUM_TRACKBALLS, defaultSystemColor);
  fill_solid(ambientLights, NUM_AMBIENT_LEDS, defaultSystemColor);
}

// *** Player Lights ***

void SetupPlayerLights() {
  static TLC5947SingleColorController<PLAYER_LIGHTS_DATA_PIN, PLAYER_LIGHTS_CLOCK_PIN, PLAYER_LIGHTS_LATCH_PIN> playerLightController;
  FastLED.addLeds(&playerLightController, playerLights, NUM_PLAYER_LIGHTS);
}

void SetAllPlayerLightsBrightness(uint8_t brightness) {
  for(int pin = 0; pin < NUM_PLAYER_LIGHTS; pin++) {
    // playerLightController.setPWM(pin, brightness);
  }
}

void TurnOnAllPlayerLights() {
  fill_solid(playerLights, NUM_PLAYER_LIGHTS, CRGB::White);
}

void TurnOffAllPlayerLights() {
  fill_solid(playerLights, NUM_PLAYER_LIGHTS, CRGB::Black);
}

void CyclePlayerLightsByColumn() {
  static uint8_t playerLightColumn = 0;

  TurnOffAllPlayerLights();

  for(uint8_t row = 0; row < PLAYER_ALL_LIGHTS_LAYOUT_ROWS; row++) {
    if(playerAllLightLayout[row][playerLightColumn] != -1) {
      // playerLightController.setPWM(playerAllLightLayout[row][playerLightColumn], maximumPlayerLightBrightness);
    }
  }

  playerLightColumn++;
  if(playerLightColumn >= PLAYER_ALL_LIGHTS_LAYOUT_COLUMNS) {
    playerLightColumn = 0;
  }
}

// *** Trackball Lights ***

void SetupTrackballLights() {
  static SingleTriColorLEDController<TRACKBALL_RED_PIN, TRACKBALL_GREEN_PIN, TRACKBALL_BLUE_PIN> trackballLEDController;
  FastLED.addLeds(&trackballLEDController, trackballs, NUM_TRACKBALLS).setCorrection(TypicalLEDStrip);
}

void CycleTrackballByPalette() {
  static uint8_t trackballPlayersPaletteIndex = 128;

  // Although ColorFromPalette takes 0 to 255, CRGBPalette16 is an array of 16 so after 240 (15 x 16) it
  // appears to be rapidly cycling back to the start. To work around this we'll only use 0 to 240.
  trackballs[0] = ColorFromPalette(trackballPlayersPalette, scale8(cos8(trackballPlayersPaletteIndex), 240));
  trackballPlayersPaletteIndex += 4;
}

void CycleTrackballByPlayerColor() {
  static uint8_t trackballPlayerIndex = 0;

  trackballs[0] = playerColors[trackballPlayerIndex];

  trackballPlayerIndex++;
  if(trackballPlayerIndex >= NUM_PLAYERS)
  {
    trackballPlayerIndex = 0;
  }
}

// *** Ambient Lights ***

void SetupAmbientLights() {
  FastLED.addLeds<P9813, AMBIENT_LIGHT_DATA_PIN, AMBIENT_LIGHT_CLOCK_PIN>(ambientLights, NUM_AMBIENT_LEDS).setCorrection(TypicalLEDStrip);
}

// *** Marquee Lights ***

void SetupMarqueeLights() {
  pinMode(MARQUEE_LIGHT_PIN, OUTPUT);
  analogWrite(MARQUEE_LIGHT_PIN, 255);
}

void CycleMarqueeBrightness() {
  static uint8_t marqueeBrightness = 255;
  analogWrite(MARQUEE_LIGHT_PIN, 255);
  marqueeBrightness -= 4;
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
