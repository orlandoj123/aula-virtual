from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# ==================== ENUMS ====================

class RolEnum(str, Enum):
    estudiante = "estudiante"
    profesor = "profesor"
    administrador = "administrador"

class EstadoSuscripcionEnum(str, Enum):
    activa = "activa"
    vencida = "vencida"
    suspendida = "suspendida"

# ==================== AUTH ====================

class RegistroEstudiante(BaseModel):
    """Datos para registrar un nuevo estudiante"""
    email: EmailStr
    nombre_completo: str = Field(..., min_length=3, max_length=100)
    numero_matricula: str = Field(..., min_length=3, max_length=50)
    contraseña: str = Field(..., min_length=8, max_length=100)

class RegistroProfesor(BaseModel):
    """Datos para registrar un nuevo profesor"""
    email: EmailStr
    nombre_completo: str = Field(..., min_length=3, max_length=100)
    contraseña: str = Field(..., min_length=8, max_length=100)
    departamento: Optional[str] = None

class LoginRequest(BaseModel):
    """Datos para login"""
    email: EmailStr
    contraseña: str

class TokenResponse(BaseModel):
    """Respuesta con token"""
    access_token: str
    token_type: str
    usuario_id: int
    rol: RolEnum

class TokenData(BaseModel):
    """Datos dentro del JWT"""
    usuario_id: Optional[int] = None
    email: Optional[str] = None
    rol: Optional[str] = None

# ==================== USUARIO ====================

class UsuarioBase(BaseModel):
    email: str
    nombre_completo: str
    rol: RolEnum

class UsuarioResponse(UsuarioBase):
    id: int
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

# ==================== ESTUDIANTE ====================

class EstudianteBase(BaseModel):
    numero_matricula: str

class EstudianteResponse(EstudianteBase):
    id: int
    usuario_id: int
    estado_activo: bool
    fecha_ingreso: datetime
    usuario: UsuarioResponse
    
    class Config:
        from_attributes = True

# ==================== SUSCRIPCIÓN ====================

class SuscripcionResponse(BaseModel):
    id: int
    estudiante_id: int
    fecha_inicio: datetime
    fecha_vencimiento: datetime
    estado: EstadoSuscripcionEnum
    monto_pagado: float
    
    class Config:
        from_attributes = True

# ==================== MÓDULO ====================

class ModuloResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    estado: str
    
    class Config:
        from_attributes = True

# ==================== GUÍA ====================

class GuiaResponse(BaseModel):
    id: int
    titulo: str
    archivo_nombre: str
    archivo_tamaño_bytes: int
    
    class Config:
        from_attributes = True
