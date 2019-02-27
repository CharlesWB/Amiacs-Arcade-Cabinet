// Testing the communication between Raspberry Pi and Arduino using I2C.

// https://oscarliang.com/raspberry-pi-arduino-connected-i2c/
// https://www.arduino.cc/en/Tutorial/MasterWriter

#include <Wire.h>

#define SLAVE_ADDRESS 0x04
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

void receiveData(int byteCount){
  Serial.print("byte count: ");
  Serial.println(byteCount);

  Serial.println(Wire.available());

  if(byteCount == 1) {
    number = Wire.read();
    Serial.print("byte received: ");
    Serial.println(number);

    if (number == 1){
      if (state == 0){
        digitalWrite(13, HIGH);
        Serial.println("LED on");
        state = 1;
      }
      else{
        digitalWrite(13, LOW);
        Serial.println("LED off");
        state = 0;
      }
    }
  }
  else {
    Serial.println("data received:");
    
    while(Wire.available()) {
      byte b = Wire.read();
      Serial.println(b);
    }
  }
}

void sendData(){
  Wire.write(number);
}

