/*
To Do:
- How should the color palette index be handled? Such as in CycleTrackballPalette.

Ideas:
- Would a sine wave, breathe, heartbeat, or some kind of bounce effect for the cycle time make it interesting?
- displayModes may turn into the command byte of I2C. It would define the action to be done. Such as set or enable.
*/

#include <Wire.h>
#include "FastLED.h"
#include "SingleTriColorLEDController.h"

// General definitions.
// Minimum of 1 and maximum of 4.
#define NUM_PLAYERS 2
// Can only be 1. No other values have been implemented.
#define NUM_TRACKBALLS 1
// Can only be 1. No other values have been implemented.
#define AMBIENT_NUM_LEDS 1

#define SLAVE_ADDRESS 0x07

// Pin definitions.
#define TRACKBALL_RED_PIN 3
#define TRACKBALL_GREEN_PIN 5
#define TRACKBALL_BLUE_PIN 6
#define AMBIENT_LIGHT_DATA_PIN 11
#define AMBIENT_LIGHT_CLOCK_PIN 13


const CRGB defaultSystemColor = CRGB::Orange;
CRGB playerColors[NUM_PLAYERS] = {CRGB::Blue, CRGB::Red};

CRGB trackballs[NUM_TRACKBALLS];
CRGBPalette16 trackballPalette;

CRGB ambientLights[AMBIENT_NUM_LEDS];


enum displayModes {
  ATTRACT,
  MUTE, // Or DIMMED, SCREENSAVER_ACTIVE
  GAME_PLAYING,
  GAME_PAUSED, // RetroPie may not provide a way to respond to paused games.
  TESTING,
};


void setup() {
  Serial.begin(9600);

  SetupTrackballLights();
  SetupAmbientLights();
  
  SetupTrackballPalette();

  Wire.begin(SLAVE_ADDRESS);
  Wire.onReceive(receiveEvent);

  ResetLightsToSystemDefault();
  
  FastLED.show();
  delay(1000);
}

void loop() {
  // Temporary testing until display modes are implemented.
  CycleTrackballPalette();

  FastLED.show();
  delay(100);
}

void receiveEvent(int byteCount) {
    
}

void SetupTrackballLights() {
  static SingleTriColorLEDController<TRACKBALL_RED_PIN, TRACKBALL_GREEN_PIN, TRACKBALL_BLUE_PIN> trackballLEDController;
  FastLED.addLeds(&trackballLEDController, trackballs, NUM_TRACKBALLS).setCorrection(TypicalLEDStrip);
}

void SetupAmbientLights() {
  FastLED.addLeds<P9813, AMBIENT_LIGHT_DATA_PIN, AMBIENT_LIGHT_CLOCK_PIN>(ambientLights, AMBIENT_NUM_LEDS).setCorrection(TypicalLEDStrip);
}

// The intent for this palette is to cycle through all the player colors while a game is playing.
// Because we can't know when a specific player is playing.
void SetupTrackballPalette() {
  #if NUM_PLAYERS == 1
    trackballPalette = CRGBPalette16(playerColors[0]);
  #elif NUM_PLAYERS == 2
    trackballPalette = CRGBPalette16(playerColors[0], playerColors[1]);
  #elif NUM_PLAYERS == 3
    trackballPalette = CRGBPalette16(playerColors[0], playerColors[1], playerColors[2]);
  #elif NUM_PLAYERS == 4
    trackballPalette = CRGBPalette16(playerColors[0], playerColors[1], playerColors[2], playerColors[3]);
  #else
    trackballPalette = RainbowColors_p;
  #endif
}

void ResetLightsToSystemDefault() {
  trackballs[0] = defaultSystemColor;
  ambientLights[0] = defaultSystemColor;
}

void CycleTrackballPalette() {
  static uint8_t trackballPaletteIndex = 0;
  trackballs[0] = ColorFromPalette(trackballPalette, trackballPaletteIndex);
  trackballPaletteIndex += 4;
}

void Debug_PrintColorInformation(const struct CRGB &color) {
  Serial.print("Red: ");
  Serial.print(color.red);
  Serial.print(", Green: ");
  Serial.print(color.green);
  Serial.print(", Blue: ");
  Serial.println(color.blue);
}

