from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Estudiante, Suscripcion, EstadoSuscripcionEnum
from app.dependencies import get_current_admin
from app.suscripciones import crear_suscripcion
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/usuarios")
async def listar_usuarios(
    current_user: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Lista todos los usuarios (solo admin)"""
    
    usuarios = db.query(Usuario).all()
    
    return {
        "cantidad": len(usuarios),
        "usuarios": [
            {
                "id": u.id,
                "email": u.email,
                "nombre": u.nombre_completo,
                "rol": u.rol.value,
                "activo": u.activo
            }
            for u in usuarios
        ]
    }

@router.post("/suscripcion/crear/{estudiante_id}")
async def crear_suscripcion_admin(
    estudiante_id: int,
    dias: int = 30,
    monto: float = 0.0,
    current_user: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Crea una suscripción manualmente (admin)"""
    
    estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    fecha_vencimiento = datetime.utcnow() + timedelta(days=dias)
    
    suscripcion = crear_suscripcion(
        estudiante_id=estudiante_id,
        fecha_vencimiento=fecha_vencimiento,
        monto_pagado=monto,
        db=db
    )
    
    return {
        "mensaje": "Suscripción creada",
        "suscripcion_id": suscripcion.id,
        "fecha_vencimiento": suscripcion.fecha_vencimiento
    }

@router.post("/usuario/{usuario_id}/desactivar")
async def desactivar_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Desactiva un usuario (admin)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario.activo = False
    db.commit()
    
    return {"mensaje": "Usuario desactivado", "usuario_id": usuario_id}

@router.post("/usuario/{usuario_id}/activar")
async def activar_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Activa un usuario (admin)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario.activo = True
    db.commit()
    
    return {"mensaje": "Usuario activado", "usuario_id": usuario_id}

@router.get("/estadisticas")
async def obtener_estadisticas(
    current_user: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas del sistema"""
    
    total_usuarios = db.query(Usuario).count()
    total_estudiantes = db.query(Estudiante).count()
    suscripciones_activas = db.query(Suscripcion).filter(
        Suscripcion.estado == EstadoSuscripcionEnum.activa
    ).count()
    
    return {
        "total_usuarios": total_usuarios,
        "total_estudiantes": total_estudiantes,
        "suscripciones_activas": suscripciones_activas,
        "fecha_reporte": datetime.utcnow()
    }
