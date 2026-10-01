from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Actividad, Modulo, Profesor
from app.dependencies import get_current_profesor, get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/actividades", tags=["actividades"])

@router.post("/crear")
async def crear_actividad(
    modulo_id: int,
    titulo: str,
    descripcion: str = None,
    fecha_cierre: datetime = None,
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Crea una nueva actividad (solo profesores)"""
    
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    profesor = db.query(Profesor).filter(Profesor.usuario_id == current_user.id).first()
    if modulo.profesor_id != profesor.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    actividad = Actividad(
        modulo_id=modulo_id,
        titulo=titulo,
        descripcion=descripcion,
        fecha_cierre=fecha_cierre or datetime.utcnow()
    )
    db.add(actividad)
    db.commit()
    db.refresh(actividad)
    
    return {
        "id": actividad.id,
        "titulo": actividad.titulo,
        "modulo_id": modulo_id
    }

@router.get("/modulo/{modulo_id}")
async def listar_actividades(
    modulo_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista actividades de un módulo"""
    
    actividades = db.query(Actividad).filter(Actividad.modulo_id == modulo_id).all()
    
    return {
        "cantidad": len(actividades),
        "actividades": [
            {
                "id": a.id,
                "titulo": a.titulo,
                "descripcion": a.descripcion,
                "fecha_cierre": a.fecha_cierre,
                "requiere_entrega": a.requiere_entrega
            }
            for a in actividades
        ]
    }
