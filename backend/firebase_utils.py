import os
import json
import firebase_admin
from firebase_admin import credentials, auth, db

# --- LECTURA SEGURA DE CREDENCIALES ---
firebase_creds = os.getenv("FIREBASE_CREDENTIALS")

if firebase_creds:
    cred_dict = json.loads(firebase_creds)
    cred = credentials.Certificate(cred_dict)
else:
    cred = credentials.Certificate("serviceAccountKey.json")

try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://iot-car-parking-43374-default-rtdb.firebaseio.com'
    })

def save_parking_data(slot_id, status):
    """
    Guarda/actualiza /parking_slots/{slot_id}
    """
    slot_key = str(slot_id)
    ref = db.reference(f"/parking_slots/{slot_key}")
    # Se guarda solo el status
    ref.set({
        "status": status
    })

def get_all_parking_data():
    """
    Lee /parking_slots y retorna una LISTA de objetos.
    """
    ref = db.reference("/parking_slots")
    data = ref.get()

    if not data:
        return None

    slots = []

    if isinstance(data, dict):
        # formato esperado: {"1": {...}, "2": {...}}
        for slot_id, slot_data in data.items():
            if slot_data is None:
                continue
            slots.append({
                "slot_id": str(slot_id),
                "status": slot_data.get("status")
            })
        return slots

    if isinstance(data, list):
        for idx, slot_data in enumerate(data):
            if slot_data is None:
                continue
            slot_id = str(idx)
            slots.append({
                "slot_id": slot_id,
                "status": slot_data.get("status")
            })
        return slots

    return data

def get_user_by_email(email: str):
    """
    Busca un usuario por su email en el nodo /users de Firebase.
    Retorna el diccionario del usuario si lo encuentra, de lo contrario None.
    """
    ref = db.reference("users")
    users_data = ref.get()
    
    if users_data and isinstance(users_data, dict):
        for uid, user_info in users_data.items():
            if user_info.get("email") == email:
                # Retornamos también el UID por si lo necesitamos para el token
                user_info["uid"] = uid 
                return user_info
    return None

def create_user_in_db(user_data: dict):
    """
    Registra las credenciales y el perfil de un nuevo usuario en el nodo /users.
    Retorna el ID único (push key) generado por Firebase.
    """
    ref = db.reference("users")
    new_user_ref = ref.push()
    new_user_ref.set(user_data)
    return new_user_ref.key

def update_user_status(user_id: str, is_active: bool) -> bool:
    """
    Modifica el atributo 'is_active' de un usuario en el nodo /users/{user_id}.
    Retorna True si la operación fue exitosa, o False si el usuario no existe.
    """
    ref = db.reference(f"users/{user_id}")
    if ref.get() is None:
        return False
        
    ref.update({"is_active": is_active})
    return True

def get_history_data() -> dict:
    """
    Obtiene todos los registros del nodo /history para auditoría.
    """
    ref = db.reference("history")
    data = ref.get()
    return data if data else {}