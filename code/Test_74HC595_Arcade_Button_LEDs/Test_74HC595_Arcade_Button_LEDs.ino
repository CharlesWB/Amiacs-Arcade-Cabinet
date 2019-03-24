/*
Has three 74HC595's for 24 bits (i.e. buttons).

References
https://www.arduino.cc/en/tutorial/ShiftOut
https://shiftregister.simsso.de/
*/

#include <ShiftRegister74HC595.h>

int numberOfShiftRegisters = 3;

//Pin connected to latch pin (ST_CP) of 74HC595
const int latchPin = 10;
//Pin connected to clock pin (SH_CP) of 74HC595
const int clockPin = 13;
////Pin connected to Data in (DS) of 74HC595
const int dataPin = 11;

ShiftRegister74HC595 sr (numberOfShiftRegisters, dataPin, clockPin, latchPin);

int pin = 0;

void setup() {
  sr.setAllLow();
}

void loop() {
  for(int pin = 0; pin < 24; pin++) {
    if(pin == 0) {
      sr.set(23, LOW);
    }
    else if(pin > 0) {
      sr.set(pin - 1, LOW);
    }
    sr.set(pin, HIGH);
    delay(250);
  }
}

