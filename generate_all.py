#!/usr/bin/env python3
"""
Script de generación automática de código para Aula Virtual.
Crea todos los routers, modelos y frontend de una sola vez.
"""

import os
import sys

def create_file(path, content):
    """Crea un archivo con contenido"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"✅ Creado: {path}")

# ================== ROUTERS ==================

ROUTER_MODULOS = '''from fastapi import APIRouter, Depends, HTTPException, status
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
'''

ROUTER_ACTIVIDADES = '''from fastapi import APIRouter, Depends, HTTPException, status
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
'''

ROUTER_ENTREGAS = '''from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
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
'''

ROUTER_ADMIN = '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Estudiante, Suscripcion, EstadoSuscripcionEnum
from app.dependencies import get_current_admin
from app.suscripciones import crear_suscripcion
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/usuarios")
async def listar_usuarios(
    current_user: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Lista todos los usuarios (solo admin)"""
    
    usuarios = db.query(Usuario).all()
    
    return {
        "cantidad": len(usuarios),
        "usuarios": [
            {
                "id": u.id,
                "email": u.email,
                "nombre": u.nombre_completo,
                "rol": u.rol.value,
                "activo": u.activo
            }
            for u in usuarios
        ]
    }

@router.post("/suscripcion/crear/{estudiante_id}")
async def crear_suscripcion_admin(
    estudiante_id: int,
    dias: int = 30,
    monto: float = 0.0,
    current_user: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Crea una suscripción manualmente (admin)"""
    
    estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    fecha_vencimiento = datetime.utcnow() + timedelta(days=dias)
    
    suscripcion = crear_suscripcion(
        estudiante_id=estudiante_id,
        fecha_vencimiento=fecha_vencimiento,
        monto_pagado=monto,
        db=db
    )
    
    return {
        "mensaje": "Suscripción creada",
        "suscripcion_id": suscripcion.id,
        "fecha_vencimiento": suscripcion.fecha_vencimiento
    }

@router.post("/usuario/{usuario_id}/desactivar")
async def desactivar_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Desactiva un usuario (admin)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario.activo = False
    db.commit()
    
    return {"mensaje": "Usuario desactivado", "usuario_id": usuario_id}

@router.post("/usuario/{usuario_id}/activar")
async def activar_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Activa un usuario (admin)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario.activo = True
    db.commit()
    
    return {"mensaje": "Usuario activado", "usuario_id": usuario_id}

@router.get("/estadisticas")
async def obtener_estadisticas(
    current_user: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas del sistema"""
    
    total_usuarios = db.query(Usuario).count()
    total_estudiantes = db.query(Estudiante).count()
    suscripciones_activas = db.query(Suscripcion).filter(
        Suscripcion.estado == EstadoSuscripcionEnum.activa
    ).count()
    
    return {
        "total_usuarios": total_usuarios,
        "total_estudiantes": total_estudiantes,
        "suscripciones_activas": suscripciones_activas,
        "fecha_reporte": datetime.utcnow()
    }
'''

# ================== FRONTEND ==================

FRONTEND_INDEX = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aula Virtual</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div id="app">
        <div class="container">
            <header>
                <h1>🎓 Aula Virtual</h1>
                <nav>
                    <a href="#" onclick="logout()">Cerrar Sesión</a>
                </nav>
            </header>
            
            <div id="content">
                <!-- Se reemplaza dinámicamente -->
            </div>
        </div>
    </div>
    
    <script src="/static/js/api.js"></script>
    <script src="/static/js/app.js"></script>
</body>
</html>
'''

FRONTEND_LOGIN = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Aula Virtual</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body class="login-page">
    <div class="login-container">
        <div class="login-box">
            <h1>🎓 Aula Virtual</h1>
            
            <form onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" id="email" required>
                </div>
                
                <div class="form-group">
                    <label>Contraseña:</label>
                    <input type="password" id="password" required>
                </div>
                
                <button type="submit">Iniciar Sesión</button>
            </form>
            
            <p>¿No tienes cuenta? <a href="#registro">Registrarse</a></p>
            
            <div id="registro" style="display:none; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ccc;">
                <h3>Registrarse como Estudiante</h3>
                <form onsubmit="handleRegistro(event)">
                    <div class="form-group">
                        <label>Email:</label>
                        <input type="email" id="reg_email" required>
                    </div>
                    <div class="form-group">
                        <label>Nombre Completo:</label>
                        <input type="text" id="reg_nombre" required>
                    </div>
                    <div class="form-group">
                        <label>Matrícula:</label>
                        <input type="text" id="reg_matricula" required>
                    </div>
                    <div class="form-group">
                        <label>Contraseña:</label>
                        <input type="password" id="reg_password" required minlength="8">
                    </div>
                    <button type="submit">Registrarse</button>
                </form>
            </div>
            
            <div id="message" class="message"></div>
        </div>
    </div>
    
    <script src="/static/js/api.js"></script>
    <script>
        async function handleLogin(e) {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const contraseña = document.getElementById('password').value;
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, contraseña })
                });
                
                if (!response.ok) throw new Error('Login fallido');
                
                const data = await response.json();
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('rol', data.rol);
                localStorage.setItem('usuario_id', data.usuario_id);
                
                window.location.href = '/dashboard';
            } catch (error) {
                document.getElementById('message').textContent = 'Error: ' + error.message;
            }
        }
        
        async function handleRegistro(e) {
            e.preventDefault();
            const email = document.getElementById('reg_email').value;
            const nombre_completo = document.getElementById('reg_nombre').value;
            const numero_matricula = document.getElementById('reg_matricula').value;
            const contraseña = document.getElementById('reg_password').value;
            
            try {
                const response = await fetch('/api/auth/registro/estudiante', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, nombre_completo, numero_matricula, contraseña })
                });
                
                if (!response.ok) throw new Error('Registro fallido');
                
                const data = await response.json();
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('rol', data.rol);
                localStorage.setItem('usuario_id', data.usuario_id);
                
                window.location.href = '/dashboard';
            } catch (error) {
                document.getElementById('message').textContent = 'Error: ' + error.message;
            }
        }
        
        document.querySelector('a[href="#registro"]').onclick = (e) => {
            e.preventDefault();
            document.getElementById('registro').style.display = 
                document.getElementById('registro').style.display === 'none' ? 'block' : 'none';
        };
    </script>
</body>
</html>
'''

FRONTEND_DASHBOARD = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Aula Virtual</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🎓 Aula Virtual</h1>
            <nav>
                <span id="user-info"></span>
                <button onclick="logout()">Cerrar Sesión</button>
            </nav>
        </header>
        
        <main>
            <div class="dashboard">
                <aside class="sidebar">
                    <h3>Menú</h3>
                    <ul>
                        <li><a href="#" onclick="showSection('perfil')">Mi Perfil</a></li>
                        <li><a href="#" onclick="showSection('suscripcion')">Mi Suscripción</a></li>
                        <li><a href="#" onclick="showSection('modulos')">Módulos</a></li>
                        <li><a href="#" onclick="showSection('entregas')">Mis Entregas</a></li>
                    </ul>
                </aside>
                
                <section class="content">
                    <div id="perfil" class="section">
                        <h2>Mi Perfil</h2>
                        <div id="perfil-content"></div>
                    </div>
                    
                    <div id="suscripcion" class="section" style="display:none">
                        <h2>Mi Suscripción</h2>
                        <div id="suscripcion-content"></div>
                    </div>
                    
                    <div id="modulos" class="section" style="display:none">
                        <h2>Módulos</h2>
                        <div id="modulos-content"></div>
                    </div>
                    
                    <div id="entregas" class="section" style="display:none">
                        <h2>Mis Entregas</h2>
                        <div id="entregas-content"></div>
                    </div>
                </section>
            </div>
        </main>
    </div>
    
    <script src="/static/js/api.js"></script>
    <script>
        const token = localStorage.getItem('token');
        const rol = localStorage.getItem('rol');
        
        if (!token) window.location.href = '/login';
        
        async function cargarPerfil() {
            try {
                const response = await fetch('/api/auth/me', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                document.getElementById('user-info').textContent = `${data.nombre_completo} (${data.rol})`;
                document.getElementById('perfil-content').innerHTML = `
                    <p><strong>Email:</strong> ${data.email}</p>
                    <p><strong>Nombre:</strong> ${data.nombre_completo}</p>
                    <p><strong>Rol:</strong> ${data.rol}</p>
                `;
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function cargarSuscripcion() {
            try {
                const response = await fetch('/api/estudiantes/me/suscripcion', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                if (!data.tiene_suscripcion) {
                    document.getElementById('suscripcion-content').innerHTML = '❌ No tienes suscripción activa';
                    return;
                }
                
                document.getElementById('suscripcion-content').innerHTML = `
                    <p><strong>Estado:</strong> ${data.activa ? '✅ Activa' : '❌ Vencida'}</p>
                    <p><strong>Vencimiento:</strong> ${new Date(data.fecha_vencimiento).toLocaleDateString()}</p>
                    <p><strong>Monto Pagado:</strong> $${data.monto_pagado}</p>
                `;
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function cargarModulos() {
            try {
                const response = await fetch('/api/modulos/listar', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                let html = '<div class="modulos-list">';
                data.modulos.forEach(m => {
                    html += `<div class="modulo-card">
                        <h3>${m.nombre}</h3>
                        <p>${m.descripcion || 'Sin descripción'}</p>
                        <p><small>Estado: ${m.estado}</small></p>
                    </div>`;
                });
                html += '</div>';
                
                document.getElementById('modulos-content').innerHTML = html;
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('modulos-content').innerHTML = 'Error al cargar módulos';
            }
        }
        
        function showSection(section) {
            document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
            document.getElementById(section).style.display = 'block';
            
            if (section === 'perfil') cargarPerfil();
            if (section === 'suscripcion') cargarSuscripcion();
            if (section === 'modulos') cargarModulos();
        }
        
        function logout() {
            localStorage.clear();
            window.location.href = '/login';
        }
        
        cargarPerfil();
    </script>
</body>
</html>
'''

FRONTEND_STYLES = '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background-color: #f5f5f5;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background-color: #2c3e50;
    color: white;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

header h1 {
    font-size: 28px;
}

header nav {
    display: flex;
    gap: 20px;
    align-items: center;
}

header button {
    background-color: #e74c3c;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 14px;
}

header button:hover {
    background-color: #c0392b;
}

.login-page {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
    width: 100%;
    max-width: 400px;
    padding: 20px;
}

.login-box {
    background: white;
    padding: 40px;
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}

.login-box h1 {
    text-align: center;
    margin-bottom: 30px;
    color: #2c3e50;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #2c3e50;
}

.form-group input {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 14px;
    transition: border-color 0.3s;
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 5px rgba(102, 126, 234, 0.1);
}

button[type="submit"] {
    width: 100%;
    padding: 12px;
    background-color: #667eea;
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.3s;
}

button[type="submit"]:hover {
    background-color: #5568d3;
}

.login-box p {
    text-align: center;
    margin-top: 20px;
    color: #666;
}

.login-box a {
    color: #667eea;
    text-decoration: none;
    font-weight: 600;
    cursor: pointer;
}

.message {
    margin-top: 20px;
    padding: 12px;
    background-color: #f8d7da;
    color: #721c24;
    border-radius: 5px;
    text-align: center;
    display: none;
}

.message:not(:empty) {
    display: block;
}

.dashboard {
    display: flex;
    gap: 30px;
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.sidebar {
    width: 250px;
    flex-shrink: 0;
}

.sidebar h3 {
    margin-bottom: 20px;
    color: #2c3e50;
}

.sidebar ul {
    list-style: none;
}

.sidebar li {
    margin-bottom: 10px;
}

.sidebar a {
    display: block;
    padding: 12px;
    color: #667eea;
    text-decoration: none;
    border-radius: 5px;
    transition: background-color 0.3s;
}

.sidebar a:hover {
    background-color: #f0f0f0;
}

.content {
    flex: 1;
}

.section {
    display: none;
}

.section:first-of-type {
    display: block;
}

.section h2 {
    margin-bottom: 20px;
    color: #2c3e50;
    border-bottom: 2px solid #667eea;
    padding-bottom: 10px;
}

.modulos-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
}

.modulo-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.3s;
}

.modulo-card:hover {
    transform: translateY(-5px);
}

.modulo-card h3 {
    margin-bottom: 10px;
}

.modulo-card p {
    margin: 5px 0;
    font-size: 14px;
}

@media (max-width: 768px) {
    .dashboard {
        flex-direction: column;
    }
    
    .sidebar {
        width: 100%;
    }
    
    header {
        flex-direction: column;
        gap: 20px;
    }
}
'''

FRONTEND_API = '''const API_URL = 'http://localhost:8000/api';

async function apiCall(endpoint, method = 'GET', data = null) {
    const token = localStorage.getItem('token');
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    const response = await fetch(`${API_URL}${endpoint}`, options);
    
    if (!response.ok) {
        if (response.status === 401) {
            localStorage.clear();
            window.location.href = '/login';
        }
        throw new Error(`API Error: ${response.status}`);
    }
    
    return await response.json();
}
'''

FRONTEND_APP = '''// App.js - Lógica de la aplicación
function logout() {
    localStorage.clear();
    window.location.href = '/login';
}
'''

MAIN_UPDATED = '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import init_db
from app.routers import auth, estudiantes, archivos, modulos, actividades, entregas, admin
import os

# Inicializar BD
init_db()

app = FastAPI(
    title="Aula Virtual API",
    version="0.1.0",
    description="API para plataforma de educación virtual"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir frontend estático
if os.path.exists("../frontend"):
    app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Incluir routers
app.include_router(auth.router)
app.include_router(estudiantes.router)
app.include_router(archivos.router)
app.include_router(modulos.router)
app.include_router(actividades.router)
app.include_router(entregas.router)
app.include_router(admin.router)

# Rutas frontend
@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")

@app.get("/login")
async def login_page():
    return FileResponse("../frontend/login.html")

@app.get("/dashboard")
async def dashboard_page():
    return FileResponse("../frontend/dashboard.html")

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
'''

# ================== MAIN ==================

def main():
    print("🚀 Generando código completo...")
    
    # Crear routers
    create_file("backend/app/routers/modulos.py", ROUTER_MODULOS)
    create_file("backend/app/routers/actividades.py", ROUTER_ACTIVIDADES)
    create_file("backend/app/routers/entregas.py", ROUTER_ENTREGAS)
    create_file("backend/app/routers/admin.py", ROUTER_ADMIN)
    
    # Crear frontend
    create_file("frontend/index.html", FRONTEND_INDEX)
    create_file("frontend/login.html", FRONTEND_LOGIN)
    create_file("frontend/dashboard.html", FRONTEND_DASHBOARD)
    create_file("frontend/css/styles.css", FRONTEND_STYLES)
    create_file("frontend/js/api.js", FRONTEND_API)
    create_file("frontend/js/app.js", FRONTEND_APP)
    
    # Actualizar main.py
    create_file("backend/app/main.py", MAIN_UPDATED)
    
    print("\n✅ ¡Código generado exitosamente!")
    print("\nPróximos pasos:")
    print("1. cd backend")
    print("2. python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("3. Abre http://localhost:8000 en tu navegador")

if __name__ == "__main__":
    main()
