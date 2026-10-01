from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Entrega, Actividad, Estudiante
from app.dependencies import get_current_user, get_current_estudiante_con_suscripcion, get_current_profesor
from app.google_drive import drive_manager
from app.suscripciones import get_estudiante_por_usuario
from datetime import datetime
import tempfile
import os
from pathlib import Path

router = APIRouter(prefix="/api/entregas", tags=["entregas"])

@router.post("/subir/{actividad_id}")
async def subir_entrega(
    actividad_id: int,
    archivo: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_estudiante_con_suscripcion),
    db: Session = Depends(get_db)
):
    """Sube una entrega de estudiante"""
    
    actividad = db.query(Actividad).filter(Actividad.id == actividad_id).first()
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    estudiante = get_estudiante_por_usuario(current_user.id, db)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Validar extensión
    extension = Path(archivo.filename).suffix.lower().lstrip('.')
    extensiones_permitidas = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'zip']
    
    if extension not in extensiones_permitidas:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
    
    # Validar tamaño (50 MB máximo)
    contenido = await archivo.read()
    if len(contenido) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande")
    
    try:
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{extension}') as tmp:
            tmp.write(contenido)
            tmp_path = tmp.name
        
        # Subir a Drive
        archivo_id = drive_manager.subir_archivo(
            tmp_path,
            archivo.filename,
            parent_id=None  # En producción, obtener folder_id de la actividad
        )
        
        os.unlink(tmp_path)
        
        if not archivo_id:
            raise HTTPException(status_code=500, detail="Error al subir a Google Drive")
        
        # Crear o actualizar entrega
        entrega = db.query(Entrega).filter(
            Entrega.actividad_id == actividad_id,
            Entrega.estudiante_id == estudiante.id
        ).first()
        
        if entrega:
            # Eliminar archivo anterior
            if entrega.archivo_id_drive:
                drive_manager.eliminar_archivo(entrega.archivo_id_drive)
            entrega.archivo_id_drive = archivo_id
            entrega.archivo_nombre = archivo.filename
            entrega.archivo_tipo = extension
            entrega.archivo_tamaño_bytes = len(contenido)
            entrega.fecha_entrega = datetime.utcnow()
            entrega.estado = "entregada"
        else:
            entrega = Entrega(
                actividad_id=actividad_id,
                estudiante_id=estudiante.id,
                archivo_id_drive=archivo_id,
                archivo_nombre=archivo.filename,
                archivo_tipo=extension,
                archivo_tamaño_bytes=len(contenido),
                fecha_entrega=datetime.utcnow(),
                estado="entregada"
            )
            db.add(entrega)
        
        db.commit()
        
        return {
            "mensaje": "Entrega subida exitosamente",
            "entrega_id": entrega.id,
            "estado": "entregada"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/actividad/{actividad_id}")
async def listar_entregas_actividad(
    actividad_id: int,
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Lista entregas de una actividad (solo profesor)"""
    
    actividad = db.query(Actividad).filter(Actividad.id == actividad_id).first()
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    entregas = db.query(Entrega).filter(Entrega.actividad_id == actividad_id).all()
    
    return {
        "cantidad": len(entregas),
        "entregas": [
            {
                "id": e.id,
                "estudiante_id": e.estudiante_id,
                "archivo_nombre": e.archivo_nombre,
                "estado": e.estado.value,
                "fecha_entrega": e.fecha_entrega,
                "calificacion": e.calificacion
            }
            for e in entregas
        ]
    }

@router.get("/mi-entrega/{actividad_id}")
async def obtener_mi_entrega(
    actividad_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene la entrega del estudiante actual"""
    
    estudiante = get_estudiante_por_usuario(current_user.id, db)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    entrega = db.query(Entrega).filter(
        Entrega.actividad_id == actividad_id,
        Entrega.estudiante_id == estudiante.id
    ).first()
    
    if not entrega:
        return {"existe": False, "mensaje": "No has entregado aún"}
    
    return {
        "existe": True,
        "id": entrega.id,
        "archivo_nombre": entrega.archivo_nombre,
        "estado": entrega.estado.value,
        "fecha_entrega": entrega.fecha_entrega,
        "calificacion": entrega.calificacion,
        "retroalimentacion": entrega.retroalimentacion_profesor
    }

@router.post("/{entrega_id}/calificar")
async def calificar_entrega(
    entrega_id: int,
    calificacion: float,
    retroalimentacion: str = None,
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Califica una entrega (solo profesor)"""
    
    entrega = db.query(Entrega).filter(Entrega.id == entrega_id).first()
    if not entrega:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    
    entrega.calificacion = calificacion
    entrega.retroalimentacion_profesor = retroalimentacion
    entrega.estado = "calificada"
    entrega.fecha_revision = datetime.utcnow()
    db.commit()
    
    return {"mensaje": "Entrega calificada", "calificacion": calificacion}
