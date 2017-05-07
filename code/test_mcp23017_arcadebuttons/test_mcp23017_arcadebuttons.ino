#include <Wire.h>
#include <Adafruit_MCP23017.h>

#define playerColumns 5
#define playerRows 3
#define playerMaximumPins 16

Adafruit_MCP23017 player1;
Adafruit_MCP23017 player2;

int player1LedArray[playerRows][playerColumns] = 
{
  {8, 9, -1, -1, -1},
  {-1, 0, 1, 2, 3},
  {-1, 4, 5, 6, 7}
};

int player2LedArray[playerRows][playerColumns] = 
{
  {-1, -1, -1, 8, 9},
  {0, 1, 2, 3, -1},
  {4, 5, 6, 7, -1}
};

void setup() {
  player1.begin(0);
  player1.writeGPIOAB(0);
  for (int pin = 0; pin < playerMaximumPins; pin++)
  {
    player1.pinMode(pin, OUTPUT);
  }
  
  player2.begin(1);
  player2.writeGPIOAB(0);
  for (int pin = 0; pin < playerMaximumPins; pin++)
  {
    player2.pinMode(pin, OUTPUT);
  }
  
//  player2.pinMode(0, OUTPUT);
//  player2.pullUp(0, HIGH);
//  player2.digitalWrite(0, HIGH);
  
//  pinMode(3, OUTPUT);
//  digitalWrite(3, HIGH);
//  analogWrite(3, 8);
  
//  initializeUsingWire();
}

void loop() {
  unsigned long startTime = millis();

  while(millis() - startTime < 10000)
  {
    randomTogglePin(10);
  }

  delay(100);
  
  allPlayerDigitalWrite(HIGH);

  for(int delayTime = 250; delayTime > 0; delayTime -= 25)
  {
    allFlash(delayTime);
  }

  delay(100);

  for(int delayTime = 150; delayTime > 0; delayTime -= 25)
  {
    useArray(delayTime);
  }

  delay(100);

  for(int delayTime = 250; delayTime > 0; delayTime -= 25)
  {
    entireRow(delayTime);
  }

  delay(100);
  
  inOrder(500);

//  testUsingWire();
}

int getPlayerPin(int row, int column)
{
  int playerPin = -1;

  if (row >= 0 && row < playerRows)
  {
    if (column >= 0 && column < playerColumns)
    {
      playerPin = player1LedArray[row][column];
    }
    else if (column >= playerColumns && column < 2 * playerColumns)
    {
      playerPin = player2LedArray[row][column - playerColumns];
    }
  }

  return playerPin;
}

void playerPinDigitalWrite(int row, int column, int mode)
{
  int playerPin = getPlayerPin(row, column);

  if (playerPin >= 0 && playerPin < playerMaximumPins)
  {
    if (column < playerColumns)
    {
      player1.digitalWrite(playerPin, mode);
    }
    else
    {
      player2.digitalWrite(playerPin, mode);
    }
  }
}

int playerPinDigitalRead(int row, int column)
{
  int mode = LOW;
  int playerPin = getPlayerPin(row, column);

  if (playerPin >= 0 && playerPin < playerMaximumPins)
  {
    if (column < playerColumns)
    {
      mode = player1.digitalRead(playerPin);
    }
    else
    {
      mode = player2.digitalRead(playerPin);
    }
  }

  return mode;
}

void allPlayerDigitalWrite(int mode)
{
  for (int row = 0; row < playerRows; row++)
  {
    for (int column = 0; column < 2 * playerColumns; column++)
    {
      playerPinDigitalWrite(row, column, mode);
    }
  }
}

void randomTogglePin(int delayTime)
{
  int row = random(playerRows);
  int column = random(2 * playerColumns);

  if (getPlayerPin(row, column) != -1)
  {
    if (playerPinDigitalRead(row, column) == LOW)
    {
      playerPinDigitalWrite(row, column, HIGH);
    }
    else if (playerPinDigitalRead(row, column) == HIGH)
    {
      playerPinDigitalWrite(row, column, LOW);
    }
  
    delay(delayTime);
  }
}

void allFlash(int delayTime)
{
  allPlayerDigitalWrite(HIGH);

  delay(delayTime);

  allPlayerDigitalWrite(LOW);

  delay(delayTime);
}

void entireRow(int delayTime)
{
  for (int row = 0; row < playerRows; row++)
  {
    for (int column = 0; column < 2 * playerColumns; column++)
    {
      playerPinDigitalWrite(row, column, HIGH);
    }
    
    delay(delayTime);

    for (int column = 0; column < 2 * playerColumns; column++)
    {
      playerPinDigitalWrite(row, column, LOW);
    }
  }
}

void useArray(int delayTime)
{
  for (int row = 0; row < playerRows; row++)
  {
    for (int column = 0; column < 2 * playerColumns; column++)
    {
      playerPinDigitalWrite(row, column, HIGH);

      if (getPlayerPin(row, column) != -1)
      {
        delay(delayTime);
      }

      playerPinDigitalWrite(row, column, LOW);
    }
  }
}

void inOrder(int delayTime)
{
  for (int pin = 0; pin < playerMaximumPins; pin++)
  {
    player1.digitalWrite(pin, HIGH);
    player2.digitalWrite(pin, HIGH);
    delay(delayTime);
    player1.digitalWrite(pin, LOW);
    player2.digitalWrite(pin, LOW);
  }
}


void initializeUsingWire()
{
  Wire.begin();
  Wire.beginTransmission(0x20);
  Wire.write(0x00);
  Wire.write(0x00);
  Wire.endTransmission();
  Wire.beginTransmission(0x20);
  Wire.write(0x01);
  Wire.write(0x00);
  Wire.endTransmission();
}

void testUsingWire()
{
  Wire.beginTransmission(0x20);
  Wire.write(0x12);
  Wire.write(0);
  Wire.endTransmission();
  
  Wire.beginTransmission(0x20);
  Wire.write(0x13);
  Wire.write(0);
  Wire.endTransmission();

  for (int i = 0; i <= 7; i++)
  {
    Wire.beginTransmission(0x20);
    Wire.write(0x12);
    Wire.write(bit(i));
    Wire.endTransmission();
    delay(500);
  }

  Wire.beginTransmission(0x20);
  Wire.write(0x12);
  Wire.write(0);
  Wire.endTransmission();

  for (int i = 0; i <= 7; i++)
  {
    Wire.beginTransmission(0x20);
    Wire.write(0x13);
    Wire.write(bit(i));
    Wire.endTransmission();
    delay(500);
  }
}

