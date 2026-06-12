from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app, last_update
from security import verify_admin_role
import time

# Cliente de prueba que simula peticiones HTTP al backend
client = TestClient(app)

# --- 1. PRUEBAS BASE Y DE HARDWARE ---

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Backend IoT" in response.json()["message"]

def test_datos_incorrectos():
    """
    Control de Integridad: Rechazo automático de cadenas de texto en identificadores.
    """
    payload = {
        "slots": [
            {"slot_id": "esto_es_texto_error", "status": "libre"}
        ]
    }
    response = client.post("/api/parking/update", json=payload)
    assert response.status_code == 422 

def test_actualizar_parking():
    """
    Validación Transaccional: Ingreso y conteo de placas.
    """
    payload = {
        "slots": [
            {"slot_id": 101, "status": "ocupado"},
            {"slot_id": 102, "status": "libre"}
        ]
    }
    response = client.post("/api/parking/update", json=payload)
    assert response.status_code == 200
    assert response.json()["total_slots"] == 2

def test_sensor_inactivo():
    """
    Monitoreo: Simulación de timeout de hardware.
    """
    last_update[99] = time.time() - 15
    response = client.get("/api/sensors/monitor")
    assert response.status_code == 200
    datos = response.json()["sensors_monitor"]
    assert "99" in datos
    assert "inactivo" in datos["99"]


# --- 2. PRUEBAS DE SEGURIDAD (PRIVACIDAD Y RBAC) ---

@patch("main.get_user_by_email")
def test_login_usuario_inactivo(mock_get_user):
    """
    Gobernanza del Ciclo de Vida: Bloqueo de acceso por Baja Lógica.
    """
    mock_get_user.return_value = {
        "email": "operario_desvinculado@test.com",
        "password": "hashed_password_dummy",
        "role": "operario",
        "is_active": False
    }
    
    response = client.post("/api/auth/login", json={
        "email": "operario_desvinculado@test.com", 
        "password": "any_password"
    })
    
    assert response.status_code == 403
    assert "inactiva" in response.json()["detail"].lower()

def test_registro_sin_token_admin():
    """
    Control de Accesos: Rechazo de operaciones administrativas sin token JWT.
    """
    payload = {
        "email": "hacker@test.com",
        "password": "123",
        "name": "Intruso",
        "lastname": "Anon",
        "role": "admin"
    }
    response = client.post("/api/auth/register", json=payload)
    
    # Se validan ambos códigos de denegación perimetral y se captura el texto de error subyacente
    assert response.status_code in [401, 403], f"Respuesta de seguridad anómala: {response.text}"

def mock_admin_token():
    return {"sub": "admin@test.com", "role": "admin"}

@patch("main.get_user_by_email")
@patch("main.verify_password")
def test_descarga_pdf_password_incorrecto(mock_verify_password, mock_get_user):
    """
    Restricción de Divulgación: Re-validación de credencial para descarga de historial.
    """
    app.dependency_overrides[verify_admin_role] = mock_admin_token
    try:
        mock_get_user.return_value = {
            "email": "admin@test.com",
            "password": "hash_aislado_de_prueba" 
        }
        
        # Simulación explícita de fallo criptográfico para evitar saturación de bcrypt
        mock_verify_password.return_value = False
        
        response = client.post("/api/reports/download-pdf", json={"password": "clave_equivocada"})
        
        assert response.status_code == 403, f"Respuesta de seguridad anómala: {response.text}"
        assert "Contraseña incorrecta" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()