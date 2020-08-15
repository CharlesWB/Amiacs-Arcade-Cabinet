#define MARQUEE_LIGHT_PIN 9

void setup() {
  pinMode(MARQUEE_LIGHT_PIN, OUTPUT);
  analogWrite(MARQUEE_LIGHT_PIN, 255);
}

void loop() {
  static uint8_t marqueeBrightness = 255;
  analogWrite(MARQUEE_LIGHT_PIN, marqueeBrightness);
  marqueeBrightness -= 4;
  delay(200);
}
