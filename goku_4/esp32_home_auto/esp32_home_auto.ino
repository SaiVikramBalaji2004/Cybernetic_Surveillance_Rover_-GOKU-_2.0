/*
 * GOKU Home Automation - ESP32 Web Server
 * Controls 5 relays via HTTP requests from Raspberry Pi
 * 
 * Connections:
 * Relay 1 -> GPIO 13 (Light 1)
 * Relay 2 -> GPIO 12 (Fan)
 * Relay 3 -> GPIO 14 (Pump Motor)
 * Relay 4 -> GPIO 27 (AC)
 * Relay 5 -> GPIO 26 (Light 2)
 * 
 * Common ground for all relays
 * 
 * Web Server: http://ESP32_IP/
 */

#include <WiFi.h>
#include <WebServer.h>

// WiFi Credentials - CHANGE THESE
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Relay Pins
#define RELAY_1 13  // Light 1
#define RELAY_2 12  // Fan
#define RELAY_3 14  // Pump Motor
#define RELAY_4 27  // AC
#define RELAY_5 26  // Light 2

// Relay States (0 = OFF, 1 = ON)
int relayStates[5] = {0, 0, 0, 0, 0, 0};
int relayPins[5] = {RELAY_1, RELAY_2, RELAY_3, RELAY_4, RELAY_5};
String relayNames[5] = {"Light 1", "Fan", "Pump", "AC", "Light 2"};

// Web Server on port 80
WebServer server(80);

// LED for status indication
#define LED 2

void setup() {
  Serial.begin(115200);
  
  // Initialize relay pins
  for (int i = 0; i < 5; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], LOW);  // Start OFF (relay active LOW)
  }
  
  pinMode(LED, OUTPUT);
  digitalWrite(LED, LOW);  // LED off initially
  
  // Connect to WiFi
  Serial.println();
  Serial.println("Connecting to WiFi...");
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
    digitalWrite(LED, !digitalRead(LED));  // Blink LED
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi Connected!");
    digitalWrite(LED, HIGH);  // LED on = connected
    
    // Print ESP32 info
    Serial.println();
    Serial.println("========== ESP32 INFO ==========");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("MAC Address: ");
    Serial.println(WiFi.macAddress());
    Serial.print("Gateway: ");
    Serial.println(WiFi.gatewayIP());
    Serial.println("================================");
    
    // Start web server
    setupWebServer();
    
    Serial.println("Web server started!");
    Serial.print("Access at: http://");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WiFi Connection Failed!");
    // Blink LED rapidly to indicate error
    while (true) {
      digitalWrite(LED, !digitalRead(LED));
      delay(100);
    }
  }
}

void setupWebServer() {
  // Root page - control panel
  server.on("/", HTTP_GET, []() {
    String html = "<!DOCTYPE html><html><head>";
    html += "<meta name='viewport' content='width=device-width, initial-scale=1'>";
    html += "<title>GOKU Home Automation</title>";
    html += "<style>";
    html += "body{font-family:Arial;margin:20px;background:#f0f0f0}";
    html += "h1{color:#333;text-align:center}";
    html += ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px}";
    html += ".device{background:white;padding:20px;border-radius:10px;text-align:center;box-shadow:0 2px 5px rgba(0,0,0,0.1)}";
    html += ".device h3{margin:0 0 10px 0}";
    html += ".btn{padding:10px 20px;font-size:16px;border:none;border-radius:5px;cursor:pointer;color:white}";
    html += ".btn-on{background:#4CAF50}.btn-off{background:#f44336}";
    html += ".status{font-size:12px;color:#666;margin-top:5px}";
    html += "a{text-decoration:none;color:#2196F3}";
    html += "</style></head><body>";
    
    html += "<h1>GOKU Home Automation</h1>";
    html += "<p style='text-align:center'>ESP32 IP: " + WiFi.localIP().toString() + "</p>";
    html += "<p style='text-align:center'>MAC: " + WiFi.macAddress() + "</p>";
    
    html += "<div class='grid'>";
    
    for (int i = 0; i < 5; i++) {
      String stateClass = relayStates[i] ? "btn-on" : "btn-off";
      String stateText = relayStates[i] ? "ON" : "OFF";
      
      html += "<div class='device'>";
      html += "<h3>" + relayNames[i] + "</h3>";
      html += "<div class='status'>State: <span id='state" + String(i) + "'>" + stateText + "</span></div>";
      html += "<br>";
      html += "<a href='/relay?r=" + String(i) + "&s=1'><button class='btn btn-on'>ON</button></a>";
      html += "<a href='/relay?r=" + String(i) + "&s=0'><button class='btn btn-off'>OFF</button></a>";
      html += "</div>";
    }
    
    html += "</div>";
    html += "<p style='text-align:center;margin-top:20px'>";
    html += "<a href='/allon'>ALL ON</a> | ";
    html += "<a href='/alloff'>ALL OFF</a> | ";
    html += "<a href='/status'>STATUS JSON</a>";
    html += "</p>";
    html += "</body></html>";
    
    server.send(200, "text/html", html);
  });

  // Relay control
  server.on("/relay", HTTP_GET, []() {
    String response = "OK";
    
    if (server.hasArg("r") && server.hasArg("s")) {
      int relay = server.arg("r").toInt();
      int state = server.arg("s").toInt();
      
      if (relay >= 0 && relay < 5) {
        relayStates[relay] = state;
        digitalWrite(relayPins[relay], state ? HIGH : LOW);
        
        Serial.print("Relay ");
        Serial.print(relay + 1);
        Serial.print(" -> ");
        Serial.println(state ? "ON" : "OFF");
        
        response = "Relay " + String(relay + 1) + " = " + (state ? "ON" : "OFF");
      }
    }
    
    server.send(200, "text/plain", response);
  });

  // All ON
  server.on("/allon", HTTP_GET, []() {
    for (int i = 0; i < 5; i++) {
      relayStates[i] = 1;
      digitalWrite(relayPins[i], HIGH);
    }
    Serial.println("All Relays ON");
    server.send(200, "text/plain", "All ON");
  });

  // All OFF
  server.on("/alloff", HTTP_GET, []() {
    for (int i = 0; i < 5; i++) {
      relayStates[i] = 0;
      digitalWrite(relayPins[i], LOW);
    }
    Serial.println("All Relays OFF");
    server.send(200, "text/plain", "All OFF");
  });

  // Status JSON
  server.on("/status", HTTP_GET, []() {
    String json = "{";
    for (int i = 0; i < 5; i++) {
      json += "\"relay" + String(i + 1) + "\":" + relayStates[i];
      if (i < 4) json += ",";
    }
    json += "}";
    server.send(200, "application/json", json);
  });

  // Not found
  server.onNotFound([]() {
    server.send(404, "text/plain", "Not Found");
  });

  server.begin();
}

void loop() {
  server.handleClient();
}