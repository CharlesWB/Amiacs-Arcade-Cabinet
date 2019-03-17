#ifndef __INC_SINGLETRICOLORLEDCONTROLLER_H
#define __INC_SINGLETRICOLORLEDCONTROLLER_H

#include "FastLED.h"

/// Single tri-color (4 pin) LED controller class
/// @tparam RED_PIN the pin to write data out for the red LED
/// @tparam GREEN_PIN the pin to write data out for the green LED
/// @tparam BLUE_PIN the pin to write data out for the blue LED
/// @tparam RGB_ORDER the RGB ordering for the led data
template<uint8_t RED_PIN, uint8_t GREEN_PIN, uint8_t BLUE_PIN, EOrder RGB_ORDER = RGB>
class SingleTriColorLEDController : public CPixelLEDController<RGB_ORDER> {
public:
  SingleTriColorLEDController() {}

protected:
  virtual void init() {
    pinMode(RED_PIN, OUTPUT);
    pinMode(GREEN_PIN, OUTPUT);
    pinMode(BLUE_PIN, OUTPUT);

    analogWrite(RED_PIN, 0);
    analogWrite(GREEN_PIN, 0);
    analogWrite(BLUE_PIN, 0);
  }

  virtual void showPixels(PixelController<RGB_ORDER> &pixels) {
      uint8_t r = pixels.loadAndScale0();
      uint8_t g = pixels.loadAndScale1();
      uint8_t b = pixels.loadAndScale2();

      analogWrite(RED_PIN, r);
      analogWrite(GREEN_PIN, g);
      analogWrite(BLUE_PIN, b);
  }
};

#endif
