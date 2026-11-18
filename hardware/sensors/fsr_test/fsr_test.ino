// Test 2 czujników FSR402: tylko odczyt, nic nie steruje ramieniem.
// Podłączenie każdego czujnika (dzielnik napięcia, jak w modelu nerves.py):
//   5V ── FSR ──┬── A0 (czujnik 1)        5V ── FSR ──┬── A1 (czujnik 2)
//               └── 10 kΩ ── GND                      └── 10 kΩ ── GND
// Wysyła 100 razy na sekundę linię: czas_ms,A0,A1  (zliczenia 0–1023)
void setup() {
  Serial.begin(115200);
#if defined(ARDUINO_ARCH_RENESAS)
  analogReadResolution(10);   // UNO R4: 10 bit jak w modelu (starsze płytki mają 10 bit zawsze)
#endif
}

void loop() {
  static unsigned long next = 0;
  unsigned long now = millis();
  if (now >= next) {
    next = now + 10;
    Serial.print(now);
    Serial.print(',');
    Serial.print(analogRead(A0));
    Serial.print(',');
    Serial.println(analogRead(A1));
  }
}
