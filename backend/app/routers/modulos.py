from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Modulo, Profesor
from app.dependencies import get_current_profesor, get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/modulos", tags=["modulos"])

@router.post("/crear")
async def crear_modulo(
    nombre: str,
    descripcion: str = None,
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Crea un nuevo módulo (solo profesores)"""
    
    profesor = db.query(Profesor).filter(Profesor.usuario_id == current_user.id).first()
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    
    # Contar módulos del profesor para determinar orden
    cantidad = db.query(Modulo).filter(Modulo.profesor_id == profesor.id).count()
    
    modulo = Modulo(
        profesor_id=profesor.id,
        nombre=nombre,
        descripcion=descripcion,
        orden=cantidad + 1
    )
    db.add(modulo)
    db.commit()
    db.refresh(modulo)
    
    return {
        "id": modulo.id,
        "nombre": modulo.nombre,
        "orden": modulo.orden,
        "estado": modulo.estado.value
    }

@router.get("/listar")
async def listar_modulos(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos los módulos del profesor o para el estudiante"""
    
    if current_user.rol.value == "profesor":
        profesor = db.query(Profesor).filter(Profesor.usuario_id == current_user.id).first()
        modulos = db.query(Modulo).filter(Modulo.profesor_id == profesor.id).order_by(Modulo.orden).all()
    else:
        # Estudiantes ven todos los módulos activos
        modulos = db.query(Modulo).filter(Modulo.estado == "activo").order_by(Modulo.orden).all()
    
    return {
        "cantidad": len(modulos),
        "modulos": [
            {
                "id": m.id,
                "nombre": m.nombre,
                "descripcion": m.descripcion,
                "estado": m.estado.value,
                "orden": m.orden
            }
            for m in modulos
        ]
    }

@router.get("/{modulo_id}")
async def obtener_modulo(
    modulo_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene detalles de un módulo"""
    
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    return {
        "id": modulo.id,
        "nombre": modulo.nombre,
        "descripcion": modulo.descripcion,
        "estado": modulo.estado.value,
        "orden": modulo.orden,
        "fecha_creacion": modulo.fecha_creacion
    }

@router.post("/{modulo_id}/cerrar")
async def cerrar_modulo(
    modulo_id: int,
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Cierra un módulo (solo profesor propietario)"""
    
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    profesor = db.query(Profesor).filter(Profesor.usuario_id == current_user.id).first()
    if modulo.profesor_id != profesor.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    modulo.estado = "cerrado"
    modulo.fecha_cierre = datetime.utcnow()
    db.commit()
    
    return {"mensaje": "Módulo cerrado", "modulo_id": modulo.id}
