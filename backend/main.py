import os
import time
import math
from supabase import create_client, Client
from pydantic import BaseModel
os.environ['TZ'] = 'America/Lima'
time.tzset()
import json
import firebase_admin
from firebase_admin import credentials, auth, db
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fpdf import FPDF
from datetime import datetime
import io
import urllib.request

# --- INICIALIZACIÓN DE SUPABASE ---
supabase_url = "https://yucotffxddiwryolyinj.supabase.co"
supabase_key = "sb_publishable_2td3ZiVDS8JPVApKjzARjA_kI9zsddV"

supabase: Client = create_client(supabase_url, supabase_key)

# --- TUS ARCHIVOS LOCALES ---
from models import *
from security import *
from firebase_utils import *

# --- INICIALIZACIÓN SEGURA DE FIREBASE ---
firebase_creds = os.getenv("FIREBASE_CREDENTIALS")

if firebase_creds:
    # Entorno de Producción (Railway)
    cred_dict = json.loads(firebase_creds)
    cred = credentials.Certificate(cred_dict)
else:
    # Entorno Local (Tu PC)
    cred = credentials.Certificate("serviceAccountKey.json")

# Evitar inicializar Firebase múltiples veces
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://iot-car-parking-43374-default-rtdb.firebaseio.com'
    })

app = FastAPI(title="Backend IoT - Gestión de Estacionamientos")

# --- CONFIGURACIÓN CORS (Para conectar con tu web) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_middleware(HTTPSRedirectMiddleware)

# 🌐 Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

last_update = {}

# --- ENDPOINT DE AUTENTICACIÓN (LOGIN) ---
@app.post("/api/auth/login")
def login(credentials: UserLogin):
    user = get_user_by_email(credentials.email)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta inactiva. Contacte al administrador.")

    hashed_password = user.get("password", "")
    if not verify_password(credentials.password, hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos")

    token_data = {
        "sub": user.get("email"),
        "role": user.get("role", "operario"),
        "uid": user.get("uid")
    }
    
    access_token = create_access_token(data=token_data)

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_role": token_data["role"]
    }

# --- ENDPOINT DE REGISTRO DE USUARIOS (PROTEGIDO - SOLO ADMIN) ---
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, current_user: dict = Depends(verify_admin_role)):
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado.")
    
    hashed_password = get_password_hash(user.password)
    
    new_user_data = {
        "name": user.name,
        "lastname": user.lastname,
        "email": user.email,
        "password": hashed_password,
        "role": user.role,
        "is_active": True  
    }
    
    user_key = create_user_in_db(new_user_data)
    
    return {
        "message": f"✅ Usuario registrado correctamente con rol: {user.role}",
        "user_id": user_key
    }

# --- ENDPOINT DE BAJA LÓGICA DE USUARIOS (PROTEGIDO - SOLO ADMIN) ---
@app.put("/api/users/{user_id}/freeze")
def freeze_user(user_id: str, current_user: dict = Depends(verify_admin_role)):
    """Congela temporalmente al usuario (ej. vacaciones)"""
    try:
        try: auth.update_user(user_id, disabled=True) # Lo saca del sistema
        except: pass
        db.reference(f"users/{user_id}").update({"is_active": False, "status": "congelado"})
        return {"message": "Usuario congelado temporalmente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/users/{user_id}/disable")
def disable_user(user_id: str, current_user: dict = Depends(verify_admin_role)):
    """Deshabilita permanentemente al usuario (Soft Delete)"""
    try:
        try: auth.update_user(user_id, disabled=True) # Lo saca del sistema
        except: pass
        db.reference(f"users/{user_id}").update({"is_active": False, "status": "deshabilitado"})
        return {"message": "Usuario deshabilitado (Baja lógica)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/users/{user_id}/reactivate")
def reactivate_user(user_id: str, current_user: dict = Depends(verify_admin_role)):
    """Rehabilita al usuario y le devuelve el acceso"""
    try:
        try: auth.update_user(user_id, disabled=False) # Le devuelve el acceso
        except: pass
        db.reference(f"users/{user_id}").update({"is_active": True, "status": "activo"})
        return {"message": "Usuario reactivado y operativo."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT REPORTE PDF (VALIDACIÓN ADMIN)
@app.post("/api/reports/download-pdf")
def download_financial_report(auth_data: AdminPasswordVerification, current_user: dict = Depends(verify_admin_role)):
    """
    Exporta el historial en PDF filtrado por tiempo y calcula la recaudación.
    """
    # 1. Re-validación de identidad
    user = get_user_by_email(current_user["sub"])
    if not verify_password(auth_data.password, user.get("password", "")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Contraseña incorrecta. Descarga bloqueada por seguridad.")

    # 2. Extracción y Filtrado de Datos
    history = get_history_data()
    current_time_ms = time.time() * 1000 
    
    # --- NUEVO: Calcular exactamente la medianoche de hoy (00:00:00) ---
    now = datetime.now()
    start_of_day_ms = datetime(now.year, now.month, now.day).timestamp() * 1000

    filtered_history = {}
    total_revenue = 0.0
    
    for key, record in history.items():
        # Soporte para llaves automáticas y manuales
        exit_time = record.get("exitTime") or record.get("endTime") or 0
        
        # Filtros de tiempo
        if auth_data.filter_type == "day" and exit_time < start_of_day_ms:
            continue  # FIX DIARIO: Si el ticket se cobró antes de hoy a las 00:00, lo ignoramos
        elif auth_data.filter_type == "week" and (current_time_ms - exit_time) > 604800000:
            continue  # Últimos 7 días
        elif auth_data.filter_type == "month" and (current_time_ms - exit_time) > 2592000000:
            continue  # Últimos 30 días
            
        filtered_history[key] = record
        
        # Soporte para cobros automáticos y manuales
        raw_monto = record.get("amountPaid") or record.get("amount") or record.get("cobro") or 0
        total_revenue += float(raw_monto)

    # 3. Generación del documento PDF en memoria
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="REPORTE FINANCIERO Y AUDITORIA VEHICULAR", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    
    # Textos dinámicos del periodo
    periodos = {"day": "Diario (Desde las 00:00 hrs)", "week": "Ultimos 7 Dias", "month": "Ultimos 30 Dias", "all": "Historial Completo"}
    texto_periodo = periodos.get(auth_data.filter_type, "Historial Completo")
    
    pdf.cell(200, 6, txt=f"Estacionamiento Don Carlos - Periodo: {texto_periodo}", ln=True, align='C')
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 10, txt=f"RECAUDACION TOTAL DEL PERIODO: S/ {total_revenue:.2f}", ln=True, align='C')
    pdf.ln(5)
    
    # Cabeceras de tabla
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(25, 10, "Plaza", border=1, align='C')
    pdf.cell(35, 10, "Placa", border=1, align='C')
    pdf.cell(45, 10, "Ingreso", border=1, align='C')
    pdf.cell(45, 10, "Salida", border=1, align='C')
    pdf.cell(40, 10, "Cobro (S/)", border=1, align='C')
    pdf.ln()
    
    # Ordenar la lista para mostrar del más nuevo al más viejo
    pdf.set_font("Arial", '', 9)
    sorted_records = sorted(filtered_history.values(), key=lambda x: (x.get("exitTime") or x.get("endTime") or 0), reverse=True)
    
    for record in sorted_records:
        plaza = record.get("slot") or record.get("plaza") or "N/A"
        placa = record.get("plate") or record.get("placa") or "N/A"
        
        pdf.cell(25, 10, str(plaza), border=1, align='C')
        pdf.cell(35, 10, str(placa), border=1, align='C')
        
        in_ms = record.get("entryTime") or record.get("startTime") or 0
        out_ms = record.get("exitTime") or record.get("endTime") or 0
        
        entry_ts = in_ms / 1000 if in_ms else 0
        exit_ts = out_ms / 1000 if out_ms else 0
        
        entry_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(entry_ts)) if entry_ts else "N/A"
        exit_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(exit_ts)) if exit_ts else "N/A"
        
        pdf.cell(45, 10, entry_str, border=1, align='C')
        pdf.cell(45, 10, exit_str, border=1, align='C')
        
        amount = record.get("amountPaid") or record.get("amount") or record.get("cobro") or 0
        pdf.cell(40, 10, f"S/ {float(amount):.2f}", border=1, align='C')
        pdf.ln()

    # 4. Transmitir archivo al cliente
    pdf_bytes = pdf.output()
    return StreamingResponse(
        io.BytesIO(pdf_bytes), 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename=reporte_{auth_data.filter_type}.pdf"}
    )
# --- ENDPOINT PARA RECIBIR VARIOS SLOTS (ESP32) ---
@app.post("/api/parking/update")
def update_parking(data: ParkingUpdate):
    for slot in data.slots:
        save_parking_data(slot.slot_id, slot.status)
        last_update[slot.slot_id] = time.time()

    return {
        "message": "✅ Datos actualizados",
        "total_slots": len(data.slots),
        "slots": [{"slot_id": s.slot_id, "status": s.status} for s in data.slots]
    }

# --- ENDPOINT PARA CONSULTAR ESTADO ACTUAL ---
@app.get("/api/parking/status")
def get_status():
    data = get_all_parking_data()
    if not data:
        return {"message": "⚠️ No hay datos disponibles aún."}
    return {"parking_slots": data}

# --- ENDPOINT PARA MONITOREAR SENSORES ---
@app.get("/api/sensors/monitor")
def monitor_sensors():
    current_time = time.time()
    sensors_status = {}
    timeout = 10  

    for slot_id, last_time in last_update.items():
        elapsed = current_time - last_time
        if elapsed > timeout:
            sensors_status[slot_id] = "⚠️ Sensor inactivo"
        else:
            sensors_status[slot_id] = "✅ Sensor funcionando"

    if not sensors_status:
        return {"message": "⏳ Aún no se han recibido datos."}
    return {"sensors_monitor": sensors_status}

# --- ENDPOINT RAÍZ ---
@app.get("/")
def root(request: Request):
    base_url = str(request.base_url).rstrip("/")
    routes = {
        "Iniciar sesión": f"{base_url}/api/auth/login",
        "Registrar usuarios (Admin)": f"{base_url}/api/auth/register",
        "Desactivar usuario (Admin)": f"{base_url}/api/users/{{user_id}}/deactivate",
        "Descargar Reporte PDF (Admin)": f"{base_url}/api/reports/download-pdf",
        "Actualizar plazas": f"{base_url}/api/parking/update",
        "Ver estado actual": f"{base_url}/api/parking/status",
        "Monitorear sensores": f"{base_url}/api/sensors/monitor",
    }
    return {"message": "🚗 Backend IoT funcionando correctamente", "available_endpoints": routes}

# Truco para forzar el despliegue en Vercel

# --- ESTRUCTURA DEL MENSAJE DEL SENSOR (O DE LA WEB) ---
class SensorData(BaseModel):
    plaza: int
    estado: str  # "ocupado" o "libre"
    placa: str = None
    origen: str = "sensor"  # NUEVO: "sensor" por defecto, o "web"

# --- RUTA UNIFICADA (IOT Y WEB) ---
@app.post("/api/sensors/update")
async def update_sensor(data: SensorData):
    estado_limpio = data.estado.lower()
    
    # 1. Actualizar el mapa en Firebase SOLO si la orden viene del sensor físico
    if data.origen == "sensor":
        ref_slot = db.reference(f'parking_slots/{data.plaza}')
        ref_slot.update({'status': estado_limpio})
        
    ref_assign = db.reference(f'assignments/{data.plaza}')

    # --- INGRESO DEL VEHÍCULO ---
    if estado_limpio == "ocupado":
        assign_data = ref_assign.get()
        if not assign_data:
            # 1. Si la plaza está vacía, creamos el ticket
            plate_to_use = data.placa if data.placa else f"SEN-{data.plaza}"
            # NUEVO: Si viene de la web, el tiempo inicia en 0 (Pausado esperando al sensor)
            start_time_ms = 0 if data.origen == "web" else int(time.time() * 1000)
            
            try:
                ticket_res = supabase.table("tickets_ingreso").insert({
                    "placa_vehiculo": plate_to_use,
                    "numero_plaza": data.plaza,
                    "estado": "Finalizado"
                }).execute()
                
                ticket_id = ticket_res.data[0]['id_ticket']

                ref_assign.set({
                    "plate": plate_to_use,
                    "startTime": start_time_ms,
                    "ticket_id": ticket_id
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error creando ticket BD: {str(e)}")
        else:
            # 2. NUEVO: Si la web ya había reservado (startTime = 0) y ahora llega el auto (Sensor)
            if data.origen == "sensor" and assign_data.get("startTime", 1) == 0:
                ref_assign.update({"startTime": int(time.time() * 1000)})

    # --- SALIDA DEL VEHÍCULO ---
    elif estado_limpio == "libre":
        assign_data = ref_assign.get()

        if assign_data:
            plate = assign_data.get('plate', 'DESCONOCIDO')
            ticket_id = assign_data.get('ticket_id')
            start_time_ms = assign_data.get('startTime', 0)
            end_time_ms = int(time.time() * 1000)
            
            # NUEVO: Si se asignó en la web pero el auto NUNCA llegó al sensor
            if start_time_ms == 0:
                diff_minutes = 0
                total_monto = 0.0
                start_time_ms = end_time_ms # Se igualan para que el ticket cancelado no dé error de fecha
            else:
                diff_minutes = math.floor((end_time_ms - start_time_ms) / 60000)
                if diff_minutes < 0: diff_minutes = 0
                
                # Nivelamos la tarifa a S/ 5.00
                hours = math.ceil(diff_minutes / 60)
                if hours == 0: hours = 1 
                total_monto = float(hours * 5.00)

            from datetime import datetime
            str_ingreso = datetime.fromtimestamp(start_time_ms / 1000).strftime('%Y-%m-%dT%H:%M:%S')
            str_salida = datetime.fromtimestamp(end_time_ms / 1000).strftime('%Y-%m-%dT%H:%M:%S')

            try:
                if ticket_id:
                    supabase.table("tickets_ingreso").update({
                        "estado": "Finalizado"
                    }).eq("id_ticket", ticket_id).execute()

                supabase.table("boletas_pago").insert({
                    "id_ticket": ticket_id,
                    "tiempo_total_minutos": diff_minutes,
                    "monto_total": total_monto
                }).execute()

                db.reference('history').push({
                    "placa": plate,
                    "plate": plate, 
                    "plaza": data.plaza,
                    "slot": data.plaza,
                    "ingreso": str_ingreso,
                    "startTime": start_time_ms,
                    "salida": str_salida,
                    "endTime": end_time_ms,
                    "cobro": total_monto,
                    "amount": total_monto
                })

                ref_assign.delete()
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error en facturación: {str(e)}")

    return {"mensaje": f"Proceso unificado: Plaza {data.plaza} procesada correctamente."}

# --- ESTRUCTURA PARA SOLICITAR EL PAGO ---
class PagoRequest(BaseModel):
    placa: str

# --- NUEVO ENDPOINT: CAJERO VIRTUAL PARA EL CONDUCTOR ---
@app.post("/api/pago/generar-link")
async def generar_link_pago(req: PagoRequest):
    # 1. Buscar el vehículo en Firebase usando la placa
    assignments_ref = db.reference('assignments').get()
    
    if not assignments_ref:
        raise HTTPException(status_code=404, detail="No hay vehículos estacionados actualmente.")
    
    vehiculo_encontrado = None
    plaza_ocupada = None
    
    for plaza, data in assignments_ref.items():
        if data.get("plate") == req.placa:
            vehiculo_encontrado = data
            plaza_ocupada = plaza
            break
            
    if not vehiculo_encontrado:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado en el estacionamiento.")
        
    # 2. Calcular el tiempo y la tarifa
    start_time_ms = vehiculo_encontrado.get("startTime", 0)
    end_time_ms = int(time.time() * 1000)
    
    if start_time_ms == 0:
        raise HTTPException(status_code=400, detail="El vehículo tiene una reserva pero aún no ha ingresado.")
        
    diff_minutes = math.floor((end_time_ms - start_time_ms) / 60000)
    if diff_minutes < 0: diff_minutes = 0
    
    # Redondeo por hora a S/ 5.00
    hours = math.ceil(diff_minutes / 60)
    if hours == 0: hours = 1 
    total_monto = float(hours * 5.00)
    
    # 3. Solicitar el Link a Mercado Pago
    # 🔑 REEMPLAZA ESTO CON TU TOKEN DE PRUEBA REAL
    mp_token = os.environ.get("MP_ACCESS_TOKEN", "APP_USR-7782735169977074-061501-64408d49affd44a08ebca8d96aa3d565-3466638791")
    url_mp = "https://api.mercadopago.com/checkout/preferences"
    
    payload = {
        "items": [
            {
                "title": f"Ticket Estacionamiento Don Carlos - Placa: {req.placa}",
                "quantity": 1,
                "currency_id": "PEN",
                "unit_price": total_monto
            }
        ],
        "external_reference": req.placa,  # <-- La placa viaja a Mercado Pago
        "notification_url": "https://hook.us2.make.com/mxu8x9diobg5gtoy0tj4yne0iz5ie6c7" # <-- El aviso va a Make
    }
    
    try:
        req_mp = urllib.request.Request(
            url_mp, 
            data=json.dumps(payload).encode('utf-8'), 
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {mp_token}'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req_mp, timeout=10) as response:
            res_body = response.read()
            mp_data = json.loads(res_body.decode('utf-8'))
            
            # 4. Devolvemos la "boleta virtual" al celular del cliente
            return {
                "placa": req.placa,
                "plaza": plaza_ocupada,
                "minutos_consumidos": diff_minutes,
                "monto_total": total_monto,
                "init_point": mp_data.get("init_point") # ¡El link de pago!
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con Mercado Pago: {str(e)}")
    # --- NUEVO MODELO DE DATOS ---
class PagoConfirmado(BaseModel):
    placa: str

# --- NUEVO ENDPOINT: RECIBIR CONFIRMACIÓN 
@app.post("/api/pago/confirmar")
async def confirmar_pago(datos: PagoConfirmado):
    try:
        # 1. Buscamos todas las plazas ocupadas en Firebase
        ref = db.reference('assignments')
        plazas = ref.get()
        plaza_encontrada = None
        
        if plazas:
            for slot_id, info in plazas.items():
                if info.get('plate') == datos.placa:
                    plaza_encontrada = slot_id
                    
                    # 2. Le ponemos la etiqueta de pagado en Firebase
                    ref.child(slot_id).update({
                        "pagado": True,
                        "metodo_pago": "MercadoPago"
                    })
                    break # Detenemos el bucle al encontrar el auto
                    
        # 3. Guardamos el registro financiero en Supabase (Se guarda haya o no plaza para no perder el dinero)
        datos_pago = {
            "placa": datos.placa,
            "plaza": plaza_encontrada if plaza_encontrada else "Desconocida",
            "monto": 5.00,
            "metodo_pago": "Mercado Pago (QR)",
            "estado": "Completado"
        }
        
        # Ojo: Usamos el nombre exacto de la tabla que creaste en la imagen
        supabase.table("pagos_mercadopago").insert(datos_pago).execute()

        if plaza_encontrada:
            return {"mensaje": "Pago registrado en Firebase y Supabase exitosamente", "plaza": plaza_encontrada}
        else:
            return {"mensaje": "Pago guardado en Supabase, pero la placa no estaba en Firebase"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))