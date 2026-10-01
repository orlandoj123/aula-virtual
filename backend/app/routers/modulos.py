from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Modulo, Profesor, Actividad, Guia, Entrega
from app.dependencies import get_current_profesor, get_current_user
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/modulos", tags=["modulos"])

class CrearModuloRequest(BaseModel):
    nombre: str
    descripcion: str = None

@router.post("/crear")
async def crear_modulo(
    datos: CrearModuloRequest,
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Crea un módulo"""
    
    profesor = db.query(Profesor).filter(Profesor.usuario_id == current_user.id).first()
    cantidad = db.query(Modulo).filter(Modulo.profesor_id == profesor.id).count()
    
    modulo = Modulo(
        profesor_id=profesor.id,
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        orden=cantidad + 1
    )
    db.add(modulo)
    db.commit()
    db.refresh(modulo)
    
    return {"id": modulo.id, "nombre": modulo.nombre}

@router.get("/listar")
async def listar_modulos(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista módulos"""
    
    if current_user.rol.value == "profesor":
        profesor = db.query(Profesor).filter(Profesor.usuario_id == current_user.id).first()
        modulos = db.query(Modulo).filter(Modulo.profesor_id == profesor.id).order_by(Modulo.orden).all()
    else:
        modulos = db.query(Modulo).filter(Modulo.estado == "activo").order_by(Modulo.orden).all()
    
    return {
        "cantidad": len(modulos),
        "modulos": [
            {
                "id": m.id,
                "nombre": m.nombre,
                "descripcion": m.descripcion,
                "estado": m.estado.value,
                "guias_count": len(m.guias),
                "actividades_count": len(m.actividades)
            }
            for m in modulos
        ]
    }

@router.get("/{modulo_id}/completo")
async def obtener_modulo_completo(
    modulo_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene módulo con guías, actividades y entregas"""
    
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    return {
        "id": modulo.id,
        "nombre": modulo.nombre,
        "descripcion": modulo.descripcion,
        "guias": [
            {
                "id": g.id,
                "titulo": g.titulo,
                "archivo_nombre": g.archivo_nombre,
                "archivo_tamaño_bytes": g.archivo_tamaño_bytes,
                "archivo_id_drive": g.archivo_id_drive
            }
            for g in modulo.guias
        ],
        "actividades": [
            {
                "id": a.id,
                "titulo": a.titulo,
                "descripcion": a.descripcion,
                "fecha_cierre": a.fecha_cierre,
                "requiere_entrega": a.requiere_entrega
            }
            for a in modulo.actividades
        ]
    }

@router.post("/{modulo_id}/cerrar")
async def cerrar_modulo(
    modulo_id: int,
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Cierra un módulo"""
    
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    modulo.estado = "cerrado"
    modulo.fecha_cierre = datetime.utcnow()
    db.commit()
    
    return {"mensaje": "Módulo cerrado"}
