from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Profesor, MensajeProfesor
from app.dependencies import get_current_profesor
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/mensajes", tags=["mensajes"])

class CrearMensajeRequest(BaseModel):
    titulo: str
    contenido: str
    tipo: str = "general"

@router.post("/crear")
async def crear_mensaje(
    datos: CrearMensajeRequest,
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Crea un mensaje personalizado"""
    
    profesor = db.query(Profesor).filter(Profesor.usuario_id == current_user.id).first()
    
    mensaje = MensajeProfesor(
        profesor_id=profesor.id,
        titulo=datos.titulo,
        contenido=datos.contenido,
        tipo=datos.tipo
    )
    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)
    
    return {"id": mensaje.id, "mensaje": "Mensaje creado"}

@router.get("/listar")
async def listar_mensajes(
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Lista mensajes del profesor"""
    
    profesor = db.query(Profesor).filter(Profesor.usuario_id == current_user.id).first()
    mensajes = db.query(MensajeProfesor).filter(
        MensajeProfesor.profesor_id == profesor.id
    ).all()
    
    return {
        "cantidad": len(mensajes),
        "mensajes": [
            {
                "id": m.id,
                "titulo": m.titulo,
                "contenido": m.contenido,
                "tipo": m.tipo,
                "activo": m.activo
            }
            for m in mensajes
        ]
    }

@router.put("/{mensaje_id}")
async def editar_mensaje(
    mensaje_id: int,
    datos: CrearMensajeRequest,
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Edita un mensaje"""
    
    mensaje = db.query(MensajeProfesor).filter(MensajeProfesor.id == mensaje_id).first()
    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    mensaje.titulo = datos.titulo
    mensaje.contenido = datos.contenido
    mensaje.tipo = datos.tipo
    db.commit()
    
    return {"mensaje": "Actualizado"}

@router.delete("/{mensaje_id}")
async def eliminar_mensaje(
    mensaje_id: int,
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Elimina un mensaje"""
    
    mensaje = db.query(MensajeProfesor).filter(MensajeProfesor.id == mensaje_id).first()
    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    db.delete(mensaje)
    db.commit()
    
    return {"mensaje": "Eliminado"}

@router.get("/sin-suscripcion")
async def get_mensaje_sin_suscripcion(
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Obtiene el mensaje para estudiantes sin suscripción"""
    
    profesor = db.query(Profesor).filter(Profesor.usuario_id == current_user.id).first()
    mensaje = db.query(MensajeProfesor).filter(
        MensajeProfesor.profesor_id == profesor.id,
        MensajeProfesor.tipo == "sin_suscripcion"
    ).first()
    
    if not mensaje:
        return {
            "titulo": "Suscripción requerida",
            "contenido": "Debes tener una suscripción activa. Contacta al profesor."
        }
    
    return {"titulo": mensaje.titulo, "contenido": mensaje.contenido}
