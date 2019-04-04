/*
References
https://www.adafruit.com/product/1429
*/

#include <Adafruit_TLC5947.h>

#define NUM_TLC5974 1

const int latchPin = 10;
const int clockPin = 13;
const int dataPin = 12;

Adafruit_TLC5947 tlc = Adafruit_TLC5947(NUM_TLC5974, clockPin, dataPin, latchPin);

int pin = 0;

void setup() {
  tlc.begin();
}

void loop() {
  for(int pin = 0; pin < 24; pin++) {
    if(pin == 0) {
      tlc.setPWM(23, 0);
    }
    else if(pin > 0) {
      tlc.setPWM(pin - 1, 0);
    }
    tlc.setPWM(pin, 2000);
    tlc.write();
    delay(250);
  }

  for(int brightness = 0; brightness < 256; brightness++) {
    for(int pin = 0; pin < 24; pin++) {
      tlc.setPWM(pin, map(brightness, 0, 255, 0, 4095));
    }
    tlc.write();
    delay(10);
  }

  for(int brightness = 255; brightness >= 0; brightness--) {
    for(int pin = 0; pin < 24; pin++) {
      tlc.setPWM(pin, map(brightness, 0, 255, 0, 4095));
    }
    tlc.write();
    delay(10);
  }
}

