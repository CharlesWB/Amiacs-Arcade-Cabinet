/*
Ideas
- Would a sine wave, breathe, heartbeat, or some kind of bounce effect for the cycle time make it interesting?
- displayModes may turn into the command byte of I2C. It would define the action to be done. Such as set or enable.
*/

#include "FastLED.h"
#include "SingleTriColorLEDController.h"

CRGB defaultSystemColor = CRGB::Orange;
CRGB playerColors[2] = {CRGB::Blue, CRGB::Red};

#define TRACKBALL_RED_PIN 3
#define TRACKBALL_GREEN_PIN 5
#define TRACKBALL_BLUE_PIN 6
#define NUM_TRACKBALLS 1
CRGB trackballs[NUM_TRACKBALLS];


enum displayModes {
  ATTRACT,
  MUTE, // Or DIMMED, SCREENSAVER_ACTIVE
  GAME_PLAYING,
  GAME_PAUSED, // RetroPie may not provide a way to respond to paused games.
  TESTING,
};


void setup() {
  SingleTriColorLEDController<TRACKBALL_RED_PIN, TRACKBALL_GREEN_PIN, TRACKBALL_BLUE_PIN> trackballLEDController;
  FastLED.addLeds(&trackballLEDController, trackballs, NUM_TRACKBALLS).setCorrection(TypicalLEDStrip);
  trackballs[0] = defaultSystemColor;

  FastLED.show();
}

void loop() {

}

