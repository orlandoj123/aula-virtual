from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models import Usuario, Estudiante
from app.schemas import (
    LoginRequest, TokenResponse, RegistroEstudiante, 
    RegistroProfesor, RolEnum
)
from app.security import hash_password, verify_password, create_access_token
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/registro/estudiante", response_model=TokenResponse)
async def registro_estudiante(
    datos: RegistroEstudiante,
    db: Session = Depends(get_db)
):
    """Registra un nuevo estudiante"""
    
    # Verificar si el email ya existe
    usuario_existente = db.query(Usuario).filter(
        Usuario.email == datos.email
    ).first()
    
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Verificar si la matrícula ya existe
    matricula_existente = db.query(Estudiante).filter(
        Estudiante.numero_matricula == datos.numero_matricula
    ).first()
    
    if matricula_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La matrícula ya está registrada"
        )
    
    # Crear usuario
    usuario = Usuario(
        email=datos.email,
        nombre_completo=datos.nombre_completo,
        contraseña_hash=hash_password(datos.contraseña),
        rol=RolEnum.estudiante
    )
    db.add(usuario)
    db.flush()  # Para obtener el ID
    
    # Crear estudiante asociado
    estudiante = Estudiante(
        usuario_id=usuario.id,
        numero_matricula=datos.numero_matricula
    )
    db.add(estudiante)
    db.commit()
    
    # Crear token
    access_token = create_access_token(
        data={"usuario_id": usuario.id, "email": usuario.email, "rol": usuario.rol.value}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        usuario_id=usuario.id,
        rol=usuario.rol
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    credenciales: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login de usuario"""
    
    # Buscar usuario por email
    usuario = db.query(Usuario).filter(
        Usuario.email == credenciales.email
    ).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    # Verificar contraseña
    if not verify_password(credenciales.contraseña, usuario.contraseña_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    # Crear token
    access_token = create_access_token(
        data={"usuario_id": usuario.id, "email": usuario.email, "rol": usuario.rol.value}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        usuario_id=usuario.id,
        rol=usuario.rol
    )

@router.get("/me")
async def get_current_user_info(
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene info del usuario actual"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "nombre_completo": current_user.nombre_completo,
        "rol": current_user.rol.value,
        "activo": current_user.activo
    }
