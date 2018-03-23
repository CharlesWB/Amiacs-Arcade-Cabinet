// Note that brown wire is for 5V.

// Define Pins
#define RED 3
#define GREEN 5
#define BLUE 6

#define delayTime 10 // fading time between colors


void setup()
{
  pinMode(RED, OUTPUT);
  pinMode(GREEN, OUTPUT);
  pinMode(BLUE, OUTPUT);
  digitalWrite(RED, HIGH);
  digitalWrite(GREEN, HIGH);
  digitalWrite(BLUE, HIGH);
}

// define variables
int redValue;
int greenValue;
int blueValue;


// main loop
void loop()
{
  cycleSingleColor(GREEN);
  cycleSingleColor(BLUE);
  turnOnSingleColor(RED);
  delay(1000);

  redValue = 255; // choose a value between 1 and 255 to change the color.
  greenValue = 0;
  blueValue = 0;
  for(int i = 0; i < 255; i += 1) // fades out red bring green full when i=255
  {
    redValue -= 1;
    greenValue += 1;
    analogWrite(RED, 255 - redValue);
    analogWrite(GREEN, 255 - greenValue);
    delay(delayTime * 5);
  }

  redValue = 0;
  greenValue = 255;
  blueValue = 0;
  for(int i = 0; i < 255; i += 1)  // fades out green bring blue full when i=255
  {
    greenValue -= 1;
    blueValue += 1;
    analogWrite(GREEN, 255 - greenValue);
    analogWrite(BLUE, 255 - blueValue);
    delay(delayTime * 5);
  }

  redValue = 0;
  greenValue = 0;
  blueValue = 255;
  for(int i = 0; i < 255; i += 1)  // fades out blue bring red full when i=255
  {
  redValue += 1;
  blueValue -= 1;
  analogWrite(RED, 255 - redValue);
  analogWrite(BLUE, 255 - blueValue);
  delay(delayTime * 5);
  }

  turnOffSingleColor(RED);
}


void cycleSingleColor(int pin)
{
  for(int i = 0; i < 255; i += 1)
  {
    analogWrite(pin, 255 - i);
    delay(delayTime);
  }

  for(int i = 255; i >= 0; i -= 1)
  {
    analogWrite(pin, 255 - i);
    delay(delayTime);
  }
}

void turnOnSingleColor(int pin)
{
  for(int i = 0; i < 255; i += 1)
  {
    analogWrite(pin, 255 - i);
    delay(delayTime);
  }
}

void turnOffSingleColor(int pin)
{
  for(int i = 255; i >= 0; i -= 1)
  {
    analogWrite(pin, 255 - i);
    delay(delayTime);
  }
}

