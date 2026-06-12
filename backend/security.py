import time
import jwt
import bcrypt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuración JWT
SECRET_KEY = "clave_secreta_estacionamiento_iot" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120 

# Esquema de seguridad
security = HTTPBearer()

# --- FUNCIONES DE CONTRASEÑAS (NATIVO BCRYPT) ---
def get_password_hash(password: str) -> str:
    """Genera el hash irreversible de una contraseña usando bcrypt nativo."""
    # Bcrypt requiere que el texto plano sea convertido a bytes
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    
    # Retornamos el hash como string para poder guardarlo en Firebase JSON
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña ingresada coincide con el hash guardado."""
    try:
        # Control de Integridad
        if not hashed_password or not hashed_password.startswith("$2"):
            return False
            
        # Convertimos ambos a bytes para la comparación matemática
        pwd_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception as e:
        print(f"⚠️ Alerta de seguridad procesando hash: {e}")
        return False

# --- FUNCIONES JWT ---
def create_access_token(data: dict):
    """Genera un token JWT firmado."""
    to_encode = data.copy()
    expire = time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Middleware para interceptar y validar el token JWT."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha expirado. Vuelva a iniciar sesión.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido o corrupto.")

def verify_admin_role(payload: dict = Security(verify_token)):
    """Middleware que verifica si el usuario es Administrador."""
    role = payload.get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requieren privilegios de Administrador.")
    return payload