#include <WiFi.h>
#include <WebServer.h>
#include <Arduino.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

#define RELAY_1 13
#define RELAY_2 12
#define RELAY_3 14
#define RELAY_4 27
#define RELAY_5 26
#define RELAY_6 25
#define RELAY_7 33
#define RELAY_8 32

int relayPins[] = {RELAY_1, RELAY_2, RELAY_3, RELAY_4, RELAY_5, RELAY_6, RELAY_7, RELAY_8};
int relayStates[] = {0, 0, 0, 0, 0, 0, 0, 0};

WebServer server(80);

const char index_html[] = R"rawliteral(
<!DOCTYPE html><html>
<head><title>GOKU ESP32 Control</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font-family: Arial; text-align: center; margin: 0px auto; padding: 20px; }
  .btn { background-color: #4CAF50; border: none; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; }
  .btn-off { background-color: #f44336; }
</style>
</head>
<body>
<h1>GOKU Relay Control</h1>
)rawliteral";

void handleRoot() {
  String html = index_html;
  for(int i = 0; i < 8; i++) {
    html += "<p>Relay " + String(i+1) + ": ";
    html += relayStates[i] ? "<span style='color:green'>ON</span>" : "<span style='color:red'>OFF</span>";
    html += " <a href=\"/relay?r=" + String(i) + "&s=1\"><button class='btn'>ON</button></a>";
    html += " <a href=\"/relay?r=" + String(i) + "&s=0\"><button class='btn btn-off'>OFF</button></a></p>";
  }
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void handleRelay() {
  if (server.hasArg("r") && server.hasArg("s")) {
    int r = server.arg("r").toInt();
    int s = server.arg("s").toInt();
    if (r >= 0 && r < 8) {
      digitalWrite(relayPins[r], s ? HIGH : LOW);
      relayStates[r] = s;
    }
  }
  server.send(200, "text/plain", "OK");
}

void setup() {
  Serial.begin(115200);
  
  for(int i = 0; i < 8; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], LOW);
  }
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(WiFi.localIP());
  
  server.on("/", handleRoot);
  server.on("/relay", handleRelay);
  
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
}