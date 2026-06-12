import sys
from security import get_password_hash
from firebase_utils import db

def crear_admin():
    print("🛡️ Aprovisionamiento de Administrador Maestro 🛡️")
    print("-" * 50)
    email = input("Ingrese el correo del Administrador: ").strip()
    password = input("Ingrese la contraseña secreta: ").strip()
    name = input("Nombre: ").strip()
    lastname = input("Apellido: ").strip()

    if not email or not password:
        print("❌ Error: Correo y contraseña son obligatorios.")
        sys.exit(1)

    # El corazón de la seguridad: Cifrado irreversible de la contraseña
    hashed_password = get_password_hash(password)

    # Estructura del payload con privilegios administrativos
    new_admin = {
        "email": email,
        "password": hashed_password,
        "name": name,
        "lastname": lastname,
        "role": "admin",      # Otorga el máximo nivel de acceso (RBAC)
        "is_active": True     # Asegura que la cuenta nazca habilitada
    }

    # Inyección directa en el nodo /users de Firebase
    ref = db.reference("users")
    new_ref = ref.push(new_admin)
    
    print("\n✅ ¡Administrador creado exitosamente!")
    print(f"🔑 ID único generado: {new_ref.key}")
    print("El hash criptográfico ha sido guardado en la base de datos.")

if __name__ == "__main__":
    crear_admin()