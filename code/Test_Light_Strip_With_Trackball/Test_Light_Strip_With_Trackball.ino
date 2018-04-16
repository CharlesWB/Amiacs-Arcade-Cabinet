#include "FastLED.h"

#define NUM_LEDS 1

#define DATA_PIN 3
#define CLOCK_PIN 13

#define RED 4
#define GREEN 5
#define BLUE 6

CRGB leds[NUM_LEDS];

void setup() {
  FastLED.addLeds<P9813, DATA_PIN, CLOCK_PIN, RGB>(leds, NUM_LEDS);
  pinMode(RED, OUTPUT);
  pinMode(GREEN, OUTPUT);
  pinMode(BLUE, OUTPUT);
  digitalWrite(RED, HIGH);
  digitalWrite(GREEN, HIGH);
  digitalWrite(BLUE, HIGH);
}

void loop() {
  static uint8_t hue = 0;
  CHSV color = CHSV(hue++, 255, 255);
  FastLED.showColor(color);
  CRGB rgbColor = color;
  analogWrite(RED, 255- rgbColor.r);
  analogWrite(GREEN, 255 - rgbColor.g);
  analogWrite(BLUE, 255 - rgbColor.b);
  delay(200);
}
