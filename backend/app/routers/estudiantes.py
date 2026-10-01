from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Estudiante
from app.dependencies import get_current_user, get_current_estudiante
from app.suscripciones import (
    get_estudiante_por_usuario,
    tiene_suscripcion_activa,
    get_suscripcion_actual
)
from app.schemas import EstudianteResponse, SuscripcionResponse

router = APIRouter(prefix="/api/estudiantes", tags=["estudiantes"])

@router.get("/me", response_model=EstudianteResponse)
async def get_mi_perfil(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el perfil del estudiante actual"""
    
    # Verificar que sea estudiante
    if current_user.rol.value != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo estudiantes pueden acceder"
        )
    
    estudiante = get_estudiante_por_usuario(current_user.id, db)
    
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de estudiante no encontrado"
        )
    
    return estudiante

@router.get("/me/suscripcion")
async def get_mi_suscripcion(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene la suscripción actual del estudiante"""
    
    if current_user.rol.value != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo estudiantes pueden acceder"
        )
    
    estudiante = get_estudiante_por_usuario(current_user.id, db)
    
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de estudiante no encontrado"
        )
    
    suscripcion = get_suscripcion_actual(estudiante.id, db)
    
    if not suscripcion:
        return {
            "tiene_suscripcion": False,
            "activa": False,
            "mensaje": "No tienes suscripción activa"
        }
    
    activa = tiene_suscripcion_activa(estudiante.id, db)
    
    return {
        "tiene_suscripcion": True,
        "activa": activa,
        "id": suscripcion.id,
        "fecha_inicio": suscripcion.fecha_inicio,
        "fecha_vencimiento": suscripcion.fecha_vencimiento,
        "estado": suscripcion.estado.value,
        "monto_pagado": suscripcion.monto_pagado
    }

@router.get("/verificar-acceso")
async def verificar_acceso(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifica si el usuario tiene acceso a contenido protegido.
    Retorna True si tiene suscripción activa.
    """
    
    if current_user.rol.value != "estudiante":
        # Profesores y admins siempre tienen acceso
        return {"tiene_acceso": True, "razon": "Profesor o administrador"}
    
    estudiante = get_estudiante_por_usuario(current_user.id, db)
    
    if not estudiante:
        return {
            "tiene_acceso": False,
            "razon": "Registro de estudiante no encontrado"
        }
    
    acceso = tiene_suscripcion_activa(estudiante.id, db)
    
    return {
        "tiene_acceso": acceso,
        "razon": "Suscripción activa" if acceso else "Sin suscripción activa"
    }
