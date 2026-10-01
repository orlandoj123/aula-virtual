from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario
from app.security import decode_token
from app.schemas import TokenData
from app.suscripciones import get_estudiante_por_usuario, tiene_suscripcion_activa

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Verifica el token JWT y retorna el usuario actual.
    Usa este Depends() en cualquier endpoint protegido.
    """
    token = credentials.credentials
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    usuario_id: int = payload.get("usuario_id")
    if usuario_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    
    return usuario

async def get_current_admin(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Verifica que el usuario sea administrador"""
    if current_user.rol.value != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden acceder"
        )
    return current_user

async def get_current_profesor(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Verifica que el usuario sea profesor"""
    if current_user.rol.value not in ["profesor", "administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo profesores y administradores pueden acceder"
        )
    return current_user

async def get_current_estudiante(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Verifica que el usuario sea estudiante"""
    if current_user.rol.value != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo estudiantes pueden acceder"
        )
    return current_user

async def get_current_estudiante_con_suscripcion(
    current_user: Usuario = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Verifica que sea estudiante Y que tenga suscripción activa.
    Usa esto para endpoints que requieren suscripción.
    """
    
    estudiante = get_estudiante_por_usuario(current_user.id, db)
    
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registro de estudiante no encontrado"
        )
    
    if not tiene_suscripcion_activa(estudiante.id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes suscripción activa. Por favor, renova tu suscripción."
        )
    
    return current_user
