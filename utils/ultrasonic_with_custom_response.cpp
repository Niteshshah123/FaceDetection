#include <WiFi.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// Wi-Fi credentials
const char *ssid = "abcd";
const char *password = "nitesh123";

// Ultrasonic sensor pins
const int trigPin = 2;  // Trig pin
const int echoPin = 4;  // Echo pin

// Variables for distance measurement
long duration;
float distanceCm;
float distanceInch;

// Timer to ensure we calculate distance every 100ms
unsigned long previousMillis = 0;
const long interval = 50;  // Interval to read the sensor (100ms)

// WiFi server object
WiFiServer server(80);


void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);  // Disable brownout detector
  Serial.begin(115200);

  // Configure pins for the ultrasonic sensor
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  delay(10);

  // Start connecting to Wi-Fi
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  server.begin();
}

void loop() {
  unsigned long currentMillis = millis();

  // Handle incoming client requests
  WiFiClient client = server.available();  // listen for incoming clients

  if (client) {                     // if you get a client,
    Serial.println("New Client.");  // print a message out the serial port
    String currentLine = "";        // make a String to hold incoming data from the client
    while (client.connected()) {    // loop while the client's connected
      if (client.available()) {     // if there's bytes to read from the client,
        char c = client.read();     // read a byte, then
        Serial.write(c);            // print it out the serial monitor
        if (c == '\n') {            // if the byte is a newline character

          // if the current line is blank, you got two newline characters in a row.
          // that's the end of the client HTTP request, so send a response:
          if (currentLine.length() == 0) {
            // HTTP headers always start with a response code (e.g. HTTP/1.1 200 OK)
            // and a content-type so the client knows what's coming, then a blank line:
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/plain");
            client.println();

            // Respond every 100ms
            if (currentMillis - previousMillis >= interval) {
              previousMillis = currentMillis;

              // Calculate the distance
              calculateDistance();

              // Respond with 1 if distance is less than 12cm, otherwise 0
              if (distanceCm < 25.0) {
                client.print("1");
              } else {
                client.print("0");
              }

              // The HTTP response ends with another blank line:
              client.println();
            }

            // break out of the while loop:
            break;
          } else {  // if you got a newline, then clear currentLine:
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }
      }
    }
    // close the connection:
    client.stop();
    Serial.println("Client Disconnected.");
  }
}

// Function to calculate the distance using the ultrasonic sensor
void calculateDistance() {
  // Clear the trigPin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Set the trigPin HIGH for 10 microseconds to send out a pulse
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Read the echoPin, returns the duration (time in microseconds)
  duration = pulseIn(echoPin, HIGH);

  // Calculate the distance in centimeters
  distanceCm = (duration * 0.0343) / 2;

  // Convert the distance to inches
  distanceInch = distanceCm / 2.54;

  // Print the distance on the serial monitor
  Serial.print("Distance: ");
  Serial.print(distanceCm);
  Serial.print(" cm, ");
  Serial.print(distanceInch);
  Serial.println(" inches");
}
