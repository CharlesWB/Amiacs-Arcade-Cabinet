// Since this is for single color LEDs the best color to specify in FastLED is CRGB::White.
// This way changing the brightness will work correctly.
// Any color can be specified but this will result in a different brightness.

#ifndef __INC_TLC5947SINGLECOLORCONTROLLER_H
#define __INC_TLC5947SINGLECOLORCONTROLLER_H

#include <Adafruit_TLC5947.h>
#include "FastLED.h"

/// Adafruit TLC5947 24 single color LEDs controller class
/// @tparam DATA_PIN
/// @tparam CLOCK_PIN
/// @tparam LATCH_PIN
template<uint8_t DATA_PIN, uint8_t CLOCK_PIN, uint8_t LATCH_PIN>
class TLC5947SingleColorController : public CPixelLEDController<RGB> {
  Adafruit_TLC5947 *controller;

public:
  TLC5947SingleColorController() {}

protected:
  virtual void init() {
    // TODO This is hard-coded to a single 24 pin TLC5947 board.
    controller = new Adafruit_TLC5947(1, CLOCK_PIN, DATA_PIN, LATCH_PIN);
    
    controller->begin();
    
    for(int pin = 0; pin < 24; pin++) {
      controller->setPWM(pin, 0);
    }
    controller->write();
  }

  virtual void showPixels(PixelController<RGB> &pixels) {
    uint16_t pin = 0;
    
    while(pixels.has(1)) {
      uint8_t r = pixels.loadAndScale0();
      uint8_t g = pixels.loadAndScale1();
      uint8_t b = pixels.loadAndScale2();

      // TODO Is this the best way to get the brightness?
      uint8_t luma = CRGB(r, g, b).getLuma();
      controller->setPWM(pin, map(luma, 0, 255, 0, 4095));

      // TODO Is this the best way to determine which pin we're working on as pixels is iterated?
      pin++;

      pixels.stepDithering();
      pixels.advanceData();
    }
    
    controller->write();
  }
};

#endif
