from app.database import SessionLocal, get_db
from app.models import Usuario, Estudiante, RolEnum
from datetime import datetime

# Crear sesión
db = SessionLocal()

try:
    # Crear un usuario de prueba
    usuario_prueba = Usuario(
        email="estudiante@ejemplo.com",
        nombre_completo="Juan Pérez",
        contraseña_hash="hash_temporal",  # Aquí irá bcrypt después
        rol=RolEnum.estudiante
    )
    db.add(usuario_prueba)
    db.commit()
    db.refresh(usuario_prueba)
    
    print(f"✅ Usuario creado: ID={usuario_prueba.id}, Email={usuario_prueba.email}")
    
    # Crear estudiante asociado
    estudiante = Estudiante(
        usuario_id=usuario_prueba.id,
        numero_matricula="EST001"
    )
    db.add(estudiante)
    db.commit()
    
    print(f"✅ Estudiante creado: ID={estudiante.id}, Matrícula={estudiante.numero_matricula}")
    
    # Consultar
    usuarios = db.query(Usuario).all()
    print(f"✅ Total de usuarios en BD: {len(usuarios)}")
    
finally:
    db.close()
