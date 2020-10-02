#include "FastLED.h"

#define NUM_LEDS 2

#define DATA_PIN 11
#define CLOCK_PIN 13

CRGB leds[NUM_LEDS];

void setup() {
  FastLED.addLeds<P9813, DATA_PIN, CLOCK_PIN, RBG>(leds, NUM_LEDS);

  leds[0] = CRGB::Blue;
  leds[1] = CRGB::Red;

  FastLED.show();

  delay(2000);

  leds[0] = CRGB::Red;
  leds[1] = CRGB::Green;

  FastLED.show();

  delay(2000);

  leds[0] = CRGB::Green;
  leds[1] = CRGB::Blue;

  FastLED.show();

  delay(2000);
}

void loop() {
  
  static uint8_t hue = 0;
  FastLED.showColor(CHSV(hue++, 255, 255)); 

  delay(200);
}
