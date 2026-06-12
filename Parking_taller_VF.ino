#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ==========================================
// 1. CONFIGURACIÓN
// ==========================================
const char* ssid = "PLAZA";       
const char* password = "palomita";        
const char* serverUrl = "http://157.173.207.137:8000/api/parking/update";

// ==========================================
// 2. PINES
// ==========================================
const int numSlots = 4;
const int trigPins[numSlots] = {33, 13, 21, 15}; 
const int echoPins[numSlots] = {32, 12, 19, 18};
const int relayPins[numSlots] = {26, 14, 4, 2};
const int slotIds[numSlots] = {14, 15, 17, 16}; 

const int distanciaUmbral = 200; 

#define RELAY_ON LOW
#define RELAY_OFF HIGH

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 1000; 

// ==========================================
// 3. MEDICIÓN RÁPIDA
// ==========================================
long medirDistancia(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // OPTIMIZACIÓN 1: Timeout reducido
  // 200cm requieren aprox 12ms de ida y vuelta.
  // Bajamos de 30000 a 15000 microsegundos (15ms) para fallar más rápido si no hay nada.
  long duracion = pulseIn(echoPin, HIGH, 15000); 

  // Si es 0 (timeout o desconexión), asumimos Libre (999)
  if (duracion == 0) return 999; 

  long distancia = duracion * 0.0344 / 2;
  return distancia;
}

// ==========================================
// 4. ENVÍO A SERVIDOR
// ==========================================
void enviarDatosMultiples(int slotCount, String status[]) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  // Reducimos el timeout de conexión para que no congele las luces si el WiFi falla
  http.setTimeout(1000); 
  
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  JsonDocument jsonDoc;
  JsonArray arr = jsonDoc["slots"].to<JsonArray>();

  for (int i = 0; i < slotCount; i++) {
    JsonObject slot = arr.add<JsonObject>();
    slot["slot_id"] = slotIds[i]; 
    slot["status"] = status[i];
  }

  String jsonData;
  serializeJson(jsonDoc, jsonData);
  
  int httpResponseCode = http.POST(jsonData);
  if (httpResponseCode < 0) {
     // Serial.printf("Error envío: %s\n", http.errorToString(httpResponseCode).c_str());
  }
  http.end();
}

// ==========================================
// 5. SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  Serial.println("\nIniciando Sistema Rápido...");

  for (int i = 0; i < numSlots; i++) {
    pinMode(trigPins[i], OUTPUT);
    
    // Mantenemos el INPUT_PULLDOWN para evitar parpadeos por ruido
    pinMode(echoPins[i], INPUT_PULLDOWN); 
    
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], RELAY_OFF); 
  }

  WiFi.begin(ssid, password);
  // No bloqueamos el inicio esperando WiFi eternamente
  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 15) {
    delay(300);
    Serial.print(".");
    intentos++;
  }
  Serial.println("\nSetup completado");
}

// ==========================================
// 6. LOOP OPTIMIZADO
// ==========================================
void loop() {
  String estados[numSlots];
  long distancias[numSlots]; 

  for (int i = 0; i < numSlots; i++) {
    distancias[i] = medirDistancia(trigPins[i], echoPins[i]);
    
    if (distancias[i] < distanciaUmbral) {
        estados[i] = "Ocupado";
        digitalWrite(relayPins[i], RELAY_ON); 
    } 
    else {
        estados[i] = "Libre";
        digitalWrite(relayPins[i], RELAY_OFF); 
    }
    
    // OPTIMIZACIÓN 2: Delay reducido drásticamente
    // Bajamos de 60ms a 15ms. Es suficiente para evitar eco cruzado.
    delay(15); 
  }

  // Solo imprimimos debug cada cierto tiempo para no saturar el procesador
  // Serial.println("---"); 

  if (millis() - lastSendTime >= sendInterval) {
    enviarDatosMultiples(numSlots, estados);
    lastSendTime = millis();
  }
  
  // OPTIMIZACIÓN 3: Eliminado el delay(100) final.
  // El loop vuelve a empezar inmediatamente.
}
