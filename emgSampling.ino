void setup() {
  Serial.begin(38400); //Initialise serial communication
}

void loop() {
  int sensorValue = analogRead(A3); //Read the value from analog pin A3
  Serial.println(sensorValue); //Print the sensor value to the serial monitor
  delay(1); //Wait 1ms before reading again
}