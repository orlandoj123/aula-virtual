from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# ==================== ENUMS ====================

class RolEnum(str, enum.Enum):
    estudiante = "estudiante"
    profesor = "profesor"
    administrador = "administrador"

class EstadoSuscripcionEnum(str, enum.Enum):
    activa = "activa"
    vencida = "vencida"
    suspendida = "suspendida"

class EstadoModuloEnum(str, enum.Enum):
    activo = "activo"
    cerrado = "cerrado"
    archivado = "archivado"

class EstadoEntregaEnum(str, enum.Enum):
    pendiente = "pendiente"
    entregada = "entregada"
    revisada = "revisada"
    calificada = "calificada"

# ==================== TABLAS ====================

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nombre_completo = Column(String, nullable=False)
    contraseña_hash = Column(String, nullable=False)
    rol = Column(Enum(RolEnum), nullable=False, default=RolEnum.estudiante)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    estudiante = relationship("Estudiante", back_populates="usuario", uselist=False)
    profesor = relationship("Profesor", back_populates="usuario", uselist=False)
    logs_acceso = relationship("LogAcceso", back_populates="usuario")

class Estudiante(Base):
    __tablename__ = "estudiantes"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    numero_matricula = Column(String, unique=True, index=True, nullable=False)
    estado_activo = Column(Boolean, default=True)
    fecha_ingreso = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="estudiante")
    suscripciones = relationship("Suscripcion", back_populates="estudiante")
    entregas = relationship("Entrega", back_populates="estudiante")

class Profesor(Base):
    __tablename__ = "profesores"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    departamento = Column(String, nullable=True)
    fecha_ingreso = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="profesor")
    modulos = relationship("Modulo", back_populates="profesor")

class Suscripcion(Base):
    __tablename__ = "suscripciones"
    
    id = Column(Integer, primary_key=True, index=True)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    fecha_inicio = Column(DateTime, default=datetime.utcnow)
    fecha_vencimiento = Column(DateTime, nullable=False)
    estado = Column(Enum(EstadoSuscripcionEnum), default=EstadoSuscripcionEnum.activa)
    monto_pagado = Column(Float, default=0.0)
    metodo_pago = Column(String, nullable=True)
    fecha_pago = Column(DateTime, nullable=True)
    
    # Relaciones
    estudiante = relationship("Estudiante", back_populates="suscripciones")

class Modulo(Base):
    __tablename__ = "modulos"
    
    id = Column(Integer, primary_key=True, index=True)
    profesor_id = Column(Integer, ForeignKey("profesores.id"), nullable=False)
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    orden = Column(Integer, default=0)
    estado = Column(Enum(EstadoModuloEnum), default=EstadoModuloEnum.activo)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_cierre = Column(DateTime, nullable=True)
    
    # Relaciones
    profesor = relationship("Profesor", back_populates="modulos")
    guias = relationship("Guia", back_populates="modulo")
    actividades = relationship("Actividad", back_populates="modulo")

class Guia(Base):
    __tablename__ = "guias"
    
    id = Column(Integer, primary_key=True, index=True)
    modulo_id = Column(Integer, ForeignKey("modulos.id"), nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    archivo_id_drive = Column(String, nullable=False, index=True)
    archivo_nombre = Column(String, nullable=False)
    archivo_tipo = Column(String, nullable=False)  # PDF, DOCX, etc
    archivo_tamaño_bytes = Column(Integer, nullable=False)
    fecha_carga = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    modulo = relationship("Modulo", back_populates="guias")

class Actividad(Base):
    __tablename__ = "actividades"
    
    id = Column(Integer, primary_key=True, index=True)
    modulo_id = Column(Integer, ForeignKey("modulos.id"), nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_apertura = Column(DateTime, default=datetime.utcnow)
    fecha_cierre = Column(DateTime, nullable=False)
    requiere_entrega = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    modulo = relationship("Modulo", back_populates="actividades")
    entregas = relationship("Entrega", back_populates="actividad")

class Entrega(Base):
    __tablename__ = "entregas"
    
    id = Column(Integer, primary_key=True, index=True)
    actividad_id = Column(Integer, ForeignKey("actividades.id"), nullable=False)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    archivo_id_drive = Column(String, nullable=True, index=True)
    archivo_nombre = Column(String, nullable=True)
    archivo_tipo = Column(String, nullable=True)
    archivo_tamaño_bytes = Column(Integer, nullable=True)
    fecha_entrega = Column(DateTime, nullable=True)
    estado = Column(Enum(EstadoEntregaEnum), default=EstadoEntregaEnum.pendiente)
    retroalimentacion_profesor = Column(Text, nullable=True)
    calificacion = Column(Float, nullable=True)
    fecha_revision = Column(DateTime, nullable=True)
    
    # Relaciones
    actividad = relationship("Actividad", back_populates="entregas")
    estudiante = relationship("Estudiante", back_populates="entregas")

class LogAcceso(Base):
    __tablename__ = "logs_acceso"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    accion = Column(String, nullable=False)  # login, logout, descarga, subida, etc
    recurso = Column(String, nullable=True)  # qué archivo/módulo
    detalles = Column(Text, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String, nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="logs_acceso")


class MensajeProfesor(Base):
    __tablename__ = "mensajes_profesor"
    
    id = Column(Integer, primary_key=True, index=True)
    profesor_id = Column(Integer, ForeignKey("profesores.id"), nullable=False)
    titulo = Column(String, nullable=False)
    contenido = Column(Text, nullable=False)
    tipo = Column(String, default="general")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    
    profesor = relationship("Profesor", back_populates="mensajes")
