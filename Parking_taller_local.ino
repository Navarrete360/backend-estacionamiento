// Pines de sensores y RELES

const int numSlots = 4;

const int trigPins[numSlots] = {33, 13, 21, 15};

const int echoPins[numSlots] = {32, 12, 19, 18};

// Pines de control para los 4 Modulos Rele (pin IN)

const int relayPins[numSlots] = {26, 14, 4, 2};



// Umbral de distancia (cm)

const int distanciaUmbral = 200;



// Intervalo de lectura: (5 segundos)

const unsigned long loopInterval = 1000;



// Logica para Modulo Rele (Activacion por BAJO - LOW)

#define RELAY_ON LOW

#define RELAY_OFF HIGH



// --- Medir distancia ---

long medirDistancia(int trigPin, int echoPin)

{

digitalWrite(trigPin, LOW);

delayMicroseconds(2);

digitalWrite(trigPin, HIGH);

delayMicroseconds(10);

digitalWrite(trigPin, LOW);



long duracion = pulseIn(echoPin, HIGH, 30000); // timeout 30 ms

if (duracion == 0) return 999; // sin lectura valida

long distancia = duracion * 0.0344 / 2; // cm

return distancia;

}



// --- SETUP ---

void setup()

{

Serial.begin(115200);

Serial.println("Iniciando sistema de parking en modo local (sin WiFi).");



// Configurar pines

for (int i = 0; i < numSlots; i++)

{

pinMode(trigPins[i], OUTPUT);

pinMode(echoPins[i], INPUT);

pinMode(relayPins[i], OUTPUT);

// Inicializar reles: APAGADO (Ocupado por defecto)

digitalWrite(relayPins[i], RELAY_OFF);

}



Serial.println("Configuracion de pines de sensores y reles completa.");

Serial.println("Los datos de estado se mostraran aqui (Monitor Serie).");

}



// --- LOOP ---

void loop()

{

String estados[numSlots];

long distancias[numSlots];



// Leer todos los sensores

for (int i = 0; i < numSlots; i++)

{

distancias[i] = medirDistancia(trigPins[i], echoPins[i]);


// Determinar el estado

String nuevoEstado = (distancias[i] < distanciaUmbral) ? "Ocupado" : "Libre";

estados[i] = nuevoEstado;



// Control del Rele: Si es 'Libre', se ENCIENDE el Panel

digitalWrite(relayPins[i], (estados[i] == "Libre") ? RELAY_OFF : RELAY_ON );
//digitalWrite(relayPins[i], (estados[i] == "Libre") ? RELAY_ON : RELAY_OFF); para logica inversa

}



// Mostrar datos en el monitor serie

Serial.println("\n--- Estado Actual de Plazas ---");

for (int i = 0; i < numSlots; i++)

{

Serial.printf("Plaza %d -> %s | Distancia: %ld cm\n",

i + 1, estados[i].c_str(), distancias[i]);

}

Serial.println("------------------------------");



// Esperar antes de la siguiente lectura (5000 ms)

delay(loopInterval);

}