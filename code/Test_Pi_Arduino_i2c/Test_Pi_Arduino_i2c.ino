// Testing the communication between Raspberry Pi and Arduino using I2C.

// https://oscarliang.com/raspberry-pi-arduino-connected-i2c/
// https://www.arduino.cc/en/Tutorial/MasterWriter
// https://raspberry-projects.com/pi/programming-in-python/i2c-programming-in-python/using-the-i2c-interface-2

#include <Wire.h>

#define SLAVE_ADDRESS 0x07
int number = 0;
int state = 0;

void setup() {
  pinMode(13, OUTPUT);

  Serial.begin(9600);

  Wire.begin(SLAVE_ADDRESS);

  Wire.onReceive(receiveData);
  Wire.onRequest(sendData);

  Serial.println("Ready!");
}

void loop() {
  delay(100);
}

void receiveData(int byteCount) {
  Serial.print("Byte count: ");
  Serial.println(byteCount);
  
  Serial.print("Wire available: ");
  Serial.println(Wire.available());

  number = Wire.read();
  Serial.print("Number received: ");
  Serial.println(number);
  
  if(number == 1) {
    if(state == 0) {
      digitalWrite(13, HIGH);
      Serial.println("LED on");
      state = 1;
    }
    else {
      digitalWrite(13, LOW);
      Serial.println("LED off");
      state = 0;
    }
  }

  if(Wire.available()) {
    Serial.println("data received:");
    while(Wire.available()) {
      byte b = Wire.read();
      Serial.println(b);
    }
  }

  Serial.println("End");
  Serial.println();
}

void sendData(){
  Wire.write(number);
}
