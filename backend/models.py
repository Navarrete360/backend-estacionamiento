from pydantic import BaseModel, EmailStr
from typing import List

class ParkingSlot(BaseModel):
    slot_id: int
    status: str

class ParkingUpdate(BaseModel):
    slots: List[ParkingSlot]

class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    lastname: str
    role: str = "operario" # Puede ser "admin" o "operario"

class AdminPasswordVerification(BaseModel):
    password: str
    filter_type: str = "all"  # Nuevo parámetro para el filtro de tiempo