#include "FastLED.h"
#include "TLC5947SingleColorController.h"

#define NUM_LEDS 24

#define LATCH_PIN 10
#define DATA_PIN 12
#define CLOCK_PIN 13

CRGB leds[NUM_LEDS];

void setup() {
  Serial.begin(9600);
  
  static TLC5947SingleColorController<DATA_PIN, CLOCK_PIN, LATCH_PIN> ledController;
  FastLED.addLeds(&ledController, leds, NUM_LEDS);
}

void loop() {
  cylon();
  delay(500);
  blink();
}

void fadeall() { for(int i = 0; i < NUM_LEDS; i++) { leds[i].nscale8(128); } }

void cylon() {
  for(int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::White;
    FastLED.show();

    fadeall();

    delay(100);
  }

  for(int i = NUM_LEDS - 1; i >= 0; i--) {
    leds[i] = CRGB::White;
    FastLED.show();

    fadeall();

    delay(100);
  }
}

void blink() {
  FastLED.showColor(CRGB::White);
  delay(500);
  FastLED.show(CRGB::Black);
  delay(500);
}
