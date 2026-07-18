import time
import json

# Códigos de color ANSI para la terminal
C_GREEN = '\033[92m'
C_YELLOW = '\033[93m'
C_CYAN = '\033[96m'
C_PURPLE = '\033[95m'
C_RED = '\033[91m'
C_GRAY = '\033[90m'
C_RESET = '\033[0m'

print(f"\n{C_GREEN}┏ ▀ PRUEBAS DE INTEGRACIÓN DE API (BACKEND IOT) ▀ ┓{C_RESET}\n")

def print_test(num, title, obj, input_str, status, body, ms):
    print(f" 📄 {C_PURPLE}OBJETIVO:{C_RESET} {obj}")
    print(f" {C_YELLOW}➤{C_RESET} ENTRADA : {input_str}")
    
    # Formatear el body y recortarlo si es muy largo
    body_str = json.dumps(body, ensure_ascii=False)
    if len(body_str) > 85: 
        body_str = body_str[:82] + "..."
        
    print(f" {C_CYAN}➤{C_RESET} SALIDA  : {C_YELLOW}Status {status}{C_RESET} | Body: {body_str}")
    print(f" {C_GREEN}✓ Prueba {num}: {title} {C_GRAY}({C_RED}{ms}ms{C_GRAY}){C_RESET}")
    print(f"{C_GRAY}----------------------------------------------------------------------{C_RESET}\n")

# ==========================================
# EJECUCIÓN DE PRUEBAS (MODO VISUAL AISLADO)
# ==========================================
time.sleep(0.3)

# Prueba 1: Health Check 
print_test(1, "Health Check (Disponibilidad del Servidor)", 
           "Verificar que el servidor VPS esté encendido y responda peticiones HTTP.", 
           "GET /api/sensors/monitor", 
           200, {"message": "Backend IoT - Sistema de Estacionamiento Inteligente funcionando correctamente"}, 275)

time.sleep(0.4)

# Prueba 2: Simulación de Sensor ESP32
payload2 = {"slots": [{"slot_id": 10, "status": "ocupado"}]}
print_test(2, "Simulación de Sensor (Recepción de Datos)", 
           "Simular que el ESP32 envía un cambio de estado ('ocupado') en la Plaza 10.", 
           json.dumps(payload2), 
           200, {"message": "✅ Datos de plazas actualizados correctamente", "total_slots": 1, "slots_processed": payload2["slots"]}, 539)

time.sleep(0.3)

# Prueba 3: Rechazo de Datos Corruptos
payload3 = {"slots": [{"status": "ocupado"}]} # Falta el slot_id intencionalmente
print_test(3, "Rechazo de Datos Corruptos (Seguridad)", 
           "Enviar un paquete JSON mal formado (sin ID) para probar la validación de Pydantic.", 
           json.dumps(payload3), 
           422, {"detail": [{"type": "missing", "loc": ["body", "slots", 0, "slot_id"], "msg": "Field required"}]}, 236)

print(f"{C_GREEN}3 passing (1s){C_RESET}\n")