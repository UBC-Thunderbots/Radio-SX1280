#define RXBUFFER_SIZE 127

uint8_t buff[RXBUFFER_SIZE];

void setup() {
  // Initialize Serial communication at a baud rate of 115200
  Serial.begin(115200);

  // Initialize buffer with 'A'
  for (int i = 0; i < RXBUFFER_SIZE; ++i) {
    buff[i] = 'A';
  }
}

void loop() {
  // Check if data is available to read from the serial port
  if (Serial.available() > 0) {
    // Read the incoming byte:
    String incomingCommand = Serial.readStringUntil('\n');
    
    // Check if the command is "PING"
    if (incomingCommand == "PING") {
      // Respond with "PONG"
      Serial.println("PONG");
    }
  }
}