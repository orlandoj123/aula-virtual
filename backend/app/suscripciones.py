from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Estudiante, Suscripcion, EstadoSuscripcionEnum

def get_estudiante_por_usuario(usuario_id: int, db: Session) -> Estudiante:
    """Obtiene el registro de estudiante asociado a un usuario"""
    return db.query(Estudiante).filter(
        Estudiante.usuario_id == usuario_id
    ).first()

def tiene_suscripcion_activa(estudiante_id: int, db: Session) -> bool:
    """
    Verifica si un estudiante tiene suscripción activa.
    Retorna True si tiene suscripción activa y no vencida.
    """
    suscripcion = db.query(Suscripcion).filter(
        Suscripcion.estudiante_id == estudiante_id,
        Suscripcion.estado == EstadoSuscripcionEnum.activa
    ).first()
    
    if not suscripcion:
        return False
    
    # Verificar que no haya vencido
    if suscripcion.fecha_vencimiento < datetime.utcnow():
        # Marcar como vencida
        suscripcion.estado = EstadoSuscripcionEnum.vencida
        db.commit()
        return False
    
    return True

def get_suscripcion_actual(estudiante_id: int, db: Session) -> Suscripcion:
    """Obtiene la suscripción actual de un estudiante"""
    return db.query(Suscripcion).filter(
        Suscripcion.estudiante_id == estudiante_id
    ).order_by(Suscripcion.fecha_inicio.desc()).first()

def crear_suscripcion(
    estudiante_id: int,
    fecha_vencimiento: datetime,
    monto_pagado: float = 0.0,
    metodo_pago: str = None,
    db: Session = None
) -> Suscripcion:
    """Crea una nueva suscripción para un estudiante"""
    suscripcion = Suscripcion(
        estudiante_id=estudiante_id,
        fecha_vencimiento=fecha_vencimiento,
        monto_pagado=monto_pagado,
        metodo_pago=metodo_pago,
        estado=EstadoSuscripcionEnum.activa
    )
    db.add(suscripcion)
    db.commit()
    db.refresh(suscripcion)
    return suscripcion
