from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Guia, Modulo
from app.dependencies import get_current_profesor, get_current_estudiante_con_suscripcion
from app.google_drive import drive_manager
import tempfile
import os
from pathlib import Path

router = APIRouter(prefix="/api/archivos", tags=["archivos"])

CARPETAS_DRIVE = {}

@router.post("/subir/guia")
async def subir_guia(
    modulo_id: int,
    titulo: str,
    archivo: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_profesor),
    db: Session = Depends(get_db)
):
    """Sube una guía a Google Drive (solo profesores)"""
    
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    if modulo.profesor_id != current_user.profesor.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    if not archivo.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")
    
    extension = Path(archivo.filename).suffix.lower().lstrip('.')
    extensiones_permitidas = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png']
    
    if extension not in extensiones_permitidas:
        raise HTTPException(status_code=400, detail="Tipo no permitido")
    
    contenido = await archivo.read()
    if len(contenido) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Archivo muy grande")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{extension}') as tmp:
            tmp.write(contenido)
            tmp_path = tmp.name
        
        carpeta_key = f"modulo_{modulo_id}_guias"
        if carpeta_key not in CARPETAS_DRIVE:
            folder_id = drive_manager.crear_carpeta(f"MODULO_{modulo_id}_GUIAS")
            if folder_id:
                CARPETAS_DRIVE[carpeta_key] = folder_id
        
        folder_id = CARPETAS_DRIVE.get(carpeta_key)
        
        archivo_id = drive_manager.subir_archivo(tmp_path, archivo.filename, parent_id=folder_id)
        os.unlink(tmp_path)
        
        if not archivo_id:
            raise HTTPException(status_code=500, detail="Error en Google Drive")
        
        guia = Guia(
            modulo_id=modulo_id,
            titulo=titulo,
            archivo_id_drive=archivo_id,
            archivo_nombre=archivo.filename,
            archivo_tipo=extension,
            archivo_tamaño_bytes=len(contenido)
        )
        db.add(guia)
        db.commit()
        db.refresh(guia)
        
        return {"mensaje": "Guía subida", "guia_id": guia.id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/listar/guias/{modulo_id}")
async def listar_guias(
    modulo_id: int,
    current_user: Usuario = Depends(get_current_estudiante_con_suscripcion),
    db: Session = Depends(get_db)
):
    """Lista guías de un módulo"""
    
    guias = db.query(Guia).filter(Guia.modulo_id == modulo_id).all()
    
    return {
        "modulo_id": modulo_id,
        "cantidad": len(guias),
        "guias": [{"id": g.id, "titulo": g.titulo, "archivo_nombre": g.archivo_nombre} for g in guias]
    }
