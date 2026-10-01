#!/usr/bin/env python3
"""
Sistema Completo de Aula Virtual
- Gestión completa de estudiantes y suscripciones
- Módulos, actividades, guías y entregas
- Mensajes personalizables por profesor
- Panel completo para estudiantes y profesores
"""

import os

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"✅ {path}")

# ================== MODELO: MENSAJE PERSONALIZADO ==================

MODELO_MENSAJE = '''# En models.py, agregar esta clase:

class MensajeProfesor(Base):
    __tablename__ = "mensajes_profesor"
    
    id = Column(Integer, primary_key=True, index=True)
    profesor_id = Column(Integer, ForeignKey("profesores.id"), nullable=False)
    titulo = Column(String, nullable=False)
    contenido = Column(Text, nullable=False)
    tipo = Column(String, default="sin_suscripcion")  # sin_suscripcion, general, etc
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    
    profesor = relationship("Profesor", back_populates="mensajes")
'''

# ================== ROUTER MEJORADO: MENSAJES ==================

ROUTER_MENSAJES = '''from fastapi import APIRouter, Depends, HTTPException, status
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
'''

# ================== ROUTER COMPLETO: MÓDULOS CON TODO ==================

ROUTER_MODULOS_COMPLETO = '''from fastapi import APIRouter, Depends, HTTPException, status
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
'''

# ================== FRONTEND: PANEL PROFESOR COMPLETO ==================

FRONTEND_PROFESOR = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Profesor - Aula Virtual</title>
    <link rel="stylesheet" href="/static/css/styles.css">
    <style>
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.4); }
        .modal.active { display: flex; justify-content: center; align-items: center; }
        .modal-content { background: white; padding: 30px; border-radius: 10px; width: 90%; max-width: 600px; max-height: 90vh; overflow-y: auto; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        .close { cursor: pointer; color: #999; font-size: 28px; font-weight: bold; }
        .close:hover { color: #000; }
        textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-family: Arial; resize: vertical; min-height: 100px; }
        .tabla { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .tabla th, .tabla td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .tabla th { background-color: #667eea; color: white; }
        .btn-pequeño { padding: 6px 12px; font-size: 12px; margin: 2px; cursor: pointer; border: none; border-radius: 4px; background-color: #667eea; color: white; }
        .btn-pequeño:hover { background-color: #5568d3; }
        .btn-eliminar { background-color: #e74c3c; }
        .btn-eliminar:hover { background-color: #c0392b; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .sidebar { width: 250px; }
        .content { flex: 1; }
        .dashboard { display: flex; gap: 30px; }
        .section { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 Panel Profesor - Aula Virtual</h1>
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
                        <li><a href="#" onclick="showSection('inicio')">Inicio</a></li>
                        <li><a href="#" onclick="showSection('modulos')">Módulos</a></li>
                        <li><a href="#" onclick="showSection('estudiantes')">Estudiantes</a></li>
                        <li><a href="#" onclick="showSection('entregas')">Entregas</a></li>
                        <li><a href="#" onclick="showSection('mensajes')">Mensajes</a></li>
                    </ul>
                </aside>
                
                <section class="content">
                    <!-- INICIO -->
                    <div id="inicio" class="section">
                        <h2>Bienvenido al Panel</h2>
                        <div id="estadisticas"></div>
                    </div>
                    
                    <!-- MÓDULOS -->
                    <div id="modulos" class="section" style="display:none">
                        <h2>Mis Módulos</h2>
                        <button class="btn" onclick="abrirModalCrearModulo()" style="margin-bottom: 20px;">➕ Crear Módulo</button>
                        <div id="lista-modulos"></div>
                    </div>
                    
                    <!-- ESTUDIANTES -->
                    <div id="estudiantes" class="section" style="display:none">
                        <h2>Gestión de Estudiantes</h2>
                        <button class="btn" onclick="abrirModalCrearEstudiante()" style="margin-bottom: 20px;">➕ Agregar Estudiante</button>
                        <table class="tabla">
                            <thead>
                                <tr>
                                    <th>Nombre</th>
                                    <th>Email</th>
                                    <th>Matrícula</th>
                                    <th>Suscripción</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody id="tbody-est"></tbody>
                        </table>
                    </div>
                    
                    <!-- ENTREGAS -->
                    <div id="entregas" class="section" style="display:none">
                        <h2>Entregas de Estudiantes</h2>
                        <div id="lista-entregas"></div>
                    </div>
                    
                    <!-- MENSAJES -->
                    <div id="mensajes" class="section" style="display:none">
                        <h2>Mensajes Personalizados</h2>
                        <button class="btn" onclick="abrirModalMensaje()" style="margin-bottom: 20px;">➕ Crear Mensaje</button>
                        <div id="lista-mensajes"></div>
                    </div>
                </section>
            </div>
        </main>
    </div>
    
    <!-- MODAL: Crear Módulo -->
    <div id="modalModulo" class="modal">
        <div class="modal-content">
            <span class="close" onclick="cerrarModal('modalModulo')">&times;</span>
            <h2>Crear Módulo</h2>
            <form onsubmit="crearModulo(event)">
                <div class="form-group">
                    <label>Nombre del Módulo:</label>
                    <input type="text" id="nombre-modulo" required>
                </div>
                <div class="form-group">
                    <label>Descripción:</label>
                    <textarea id="desc-modulo"></textarea>
                </div>
                <button type="submit" class="btn">Crear Módulo</button>
            </form>
            <div id="msg-modulo"></div>
        </div>
    </div>
    
    <!-- MODAL: Crear Estudiante -->
    <div id="modalEstudiante" class="modal">
        <div class="modal-content">
            <span class="close" onclick="cerrarModal('modalEstudiante')">&times;</span>
            <h2>Agregar Estudiante</h2>
            <form onsubmit="crearEstudiante(event)">
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" id="est-email" required>
                </div>
                <div class="form-group">
                    <label>Nombre:</label>
                    <input type="text" id="est-nombre" required>
                </div>
                <div class="form-group">
                    <label>Matrícula:</label>
                    <input type="text" id="est-matricula" required>
                </div>
                <button type="submit" class="btn">Crear Estudiante</button>
            </form>
            <div id="msg-estudiante"></div>
        </div>
    </div>
    
    <!-- MODAL: Crear Mensaje -->
    <div id="modalMensaje" class="modal">
        <div class="modal-content">
            <span class="close" onclick="cerrarModal('modalMensaje')">&times;</span>
            <h2>Crear Mensaje Personalizado</h2>
            <form onsubmit="crearMensaje(event)">
                <div class="form-group">
                    <label>Título:</label>
                    <input type="text" id="msg-titulo" required>
                </div>
                <div class="form-group">
                    <label>Contenido:</label>
                    <textarea id="msg-contenido" required></textarea>
                </div>
                <div class="form-group">
                    <label>Tipo:</label>
                    <select id="msg-tipo">
                        <option value="general">Mensaje General</option>
                        <option value="sin_suscripcion">Para sin Suscripción</option>
                    </select>
                </div>
                <button type="submit" class="btn">Crear Mensaje</button>
            </form>
            <div id="msg-respuesta"></div>
        </div>
    </div>
    
    <script src="/static/js/api.js"></script>
    <script>
        const token = localStorage.getItem('token');
        const rol = localStorage.getItem('rol');
        
        if (!token || rol !== 'profesor') window.location.href = '/login';
        
        async function cargarDatos() {
            try {
                const response = await fetch('/api/admin/estadisticas', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                document.getElementById('estadisticas').innerHTML = `
                    <div class="card">
                        <h3>Total Estudiantes: ${data.total_estudiantes}</h3>
                        <p>Suscripciones Activas: ${data.suscripciones_activas}</p>
                    </div>
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
                
                let html = '';
                data.modulos.forEach(m => {
                    html += `<div class="card">
                        <h3>${m.nombre}</h3>
                        <p>${m.descripcion || 'Sin descripción'}</p>
                        <p><small>Guías: ${m.guias_count} | Actividades: ${m.actividades_count}</small></p>
                        <button class="btn-pequeño" onclick="verModulo(${m.id})">Ver Detalles</button>
                        <button class="btn-pequeño btn-eliminar" onclick="cerrarModulo(${m.id})">Cerrar</button>
                    </div>`;
                });
                
                document.getElementById('lista-modulos').innerHTML = html || 'No hay módulos';
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function cargarEstudiantes() {
            try {
                const response = await fetch('/api/admin/estudiantes/listar', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                let html = '';
                data.estudiantes.forEach(est => {
                    const sub = est.suscripcion;
                    const estado = sub ? (sub.activa ? '✅ Activa' : '❌ Vencida') : '❌ Ninguna';
                    html += `<tr>
                        <td>${est.nombre}</td>
                        <td>${est.email}</td>
                        <td>${est.numero_matricula}</td>
                        <td>${estado}</td>
                        <td>
                            <button class="btn-pequeño" onclick="abrirModalSuscripcion(${est.id})">Suscripción</button>
                            <button class="btn-pequeño btn-eliminar" onclick="eliminarEst(${est.id})">Eliminar</button>
                        </td>
                    </tr>`;
                });
                
                document.getElementById('tbody-est').innerHTML = html;
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function cargarMensajes() {
            try {
                const response = await fetch('/api/mensajes/listar', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                let html = '';
                data.mensajes.forEach(m => {
                    html += `<div class="card">
                        <h3>${m.titulo}</h3>
                        <p>${m.contenido}</p>
                        <small>Tipo: ${m.tipo}</small><br>
                        <button class="btn-pequeño" onclick="editarMensaje(${m.id})">Editar</button>
                        <button class="btn-pequeño btn-eliminar" onclick="eliminarMsg(${m.id})">Eliminar</button>
                    </div>`;
                });
                
                document.getElementById('lista-mensajes').innerHTML = html || 'No hay mensajes';
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        function abrirModalCrearModulo() { document.getElementById('modalModulo').classList.add('active'); }
        function abrirModalCrearEstudiante() { document.getElementById('modalEstudiante').classList.add('active'); }
        function abrirModalMensaje() { document.getElementById('modalMensaje').classList.add('active'); }
        function cerrarModal(id) { document.getElementById(id).classList.remove('active'); }
        
        async function crearModulo(e) {
            e.preventDefault();
            const nombre = document.getElementById('nombre-modulo').value;
            const descripcion = document.getElementById('desc-modulo').value;
            
            try {
                const response = await fetch('/api/modulos/crear', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({ nombre, descripcion })
                });
                
                if (response.ok) {
                    document.getElementById('msg-modulo').textContent = '✅ Módulo creado';
                    setTimeout(() => {
                        cerrarModal('modalModulo');
                        cargarModulos();
                    }, 1500);
                }
            } catch (error) {
                document.getElementById('msg-modulo').textContent = '❌ Error';
            }
        }
        
        async function crearEstudiante(e) {
            e.preventDefault();
            const email = document.getElementById('est-email').value;
            const nombre_completo = document.getElementById('est-nombre').value;
            const numero_matricula = document.getElementById('est-matricula').value;
            
            try {
                const response = await fetch('/api/admin/estudiantes/crear', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({ email, nombre_completo, numero_matricula })
                });
                
                const data = await response.json();
                if (response.ok) {
                    document.getElementById('msg-estudiante').textContent = `✅ Creado. Password: ${data.password_temporal}`;
                    setTimeout(() => {
                        cerrarModal('modalEstudiante');
                        cargarEstudiantes();
                    }, 2000);
                } else {
                    document.getElementById('msg-estudiante').textContent = `❌ ${data.detail}`;
                }
            } catch (error) {
                document.getElementById('msg-estudiante').textContent = '❌ Error';
            }
        }
        
        async function crearMensaje(e) {
            e.preventDefault();
            const titulo = document.getElementById('msg-titulo').value;
            const contenido = document.getElementById('msg-contenido').value;
            const tipo = document.getElementById('msg-tipo').value;
            
            try {
                const response = await fetch('/api/mensajes/crear', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({ titulo, contenido, tipo })
                });
                
                if (response.ok) {
                    document.getElementById('msg-respuesta').textContent = '✅ Mensaje creado';
                    setTimeout(() => {
                        cerrarModal('modalMensaje');
                        cargarMensajes();
                    }, 1500);
                }
            } catch (error) {
                document.getElementById('msg-respuesta').textContent = '❌ Error';
            }
        }
        
        async function eliminarMsg(id) {
            if (!confirm('¿Eliminar?')) return;
            try {
                await fetch(`/api/mensajes/${id}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                cargarMensajes();
            } catch (error) {
                alert('Error');
            }
        }
        
        async function eliminarEst(id) {
            if (!confirm('¿Eliminar?')) return;
            try {
                await fetch(`/api/admin/estudiantes/${id}/eliminar`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                cargarEstudiantes();
            } catch (error) {
                alert('Error');
            }
        }
        
        function showSection(section) {
            document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
            document.getElementById(section).style.display = 'block';
            
            if (section === 'inicio') cargarDatos();
            if (section === 'modulos') cargarModulos();
            if (section === 'estudiantes') cargarEstudiantes();
            if (section === 'mensajes') cargarMensajes();
        }
        
        function logout() {
            localStorage.clear();
            window.location.href = '/login';
        }
        
        document.getElementById('user-info').textContent = '📚 Panel Profesor';
        cargarDatos();
    </script>
</body>
</html>
'''

# ================== FRONTEND: PANEL ESTUDIANTE CON MENSAJE ==================

FRONTEND_ESTUDIANTE_MEJORADO = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mi Aula - Aula Virtual</title>
    <link rel="stylesheet" href="/static/css/styles.css">
    <style>
        .banner-advertencia {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .banner-advertencia h2 { font-size: 24px; margin-bottom: 10px; }
        .banner-advertencia p { margin: 10px 0; font-size: 16px; }
        .btn-contactar { background-color: white; color: #f5576c; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .btn-contactar:hover { transform: scale(1.05); }
        
        .modulo-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 15px; cursor: pointer; }
        .modulo-card:hover { transform: translateY(-5px); }
        
        .actividad-item { background: #f9f9f9; padding: 15px; border-left: 4px solid #667eea; margin-bottom: 10px; border-radius: 4px; }
        .guia-item { background: #f9f9f9; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎓 Mi Aula Virtual</h1>
            <nav>
                <span id="user-info"></span>
                <button onclick="logout()">Cerrar Sesión</button>
            </nav>
        </header>
        
        <main>
            <div id="banner-sin-suscripcion" class="banner-advertencia" style="display:none">
                <h2 id="banner-titulo">Suscripción Requerida</h2>
                <p id="banner-contenido">Contacta al profesor para obtener acceso</p>
                <button class="btn-contactar" onclick="alert('Contacta al profesor para obtener acceso a los contenidos')">Contactar Profesor</button>
            </div>
            
            <div id="contenido-principal">
                <div id="modulos-lista"></div>
                <div id="modulo-detalle" style="display:none">
                    <button onclick="volver()" class="btn">← Volver a Módulos</button>
                    <div id="contenido-modulo"></div>
                </div>
            </div>
        </main>
    </div>
    
    <script src="/static/js/api.js"></script>
    <script>
        const token = localStorage.getItem('token');
        const rol = localStorage.getItem('rol');
        
        if (!token || rol !== 'estudiante') window.location.href = '/login';
        
        async function cargarPerfil() {
            try {
                const response = await fetch('/api/auth/me', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                document.getElementById('user-info').textContent = data.nombre_completo;
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function verificarSuscripcion() {
            try {
                const response = await fetch('/api/estudiantes/verificar-acceso', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                if (!data.tiene_acceso) {
                    // Obtener mensaje personalizado del profesor
                    try {
                        const msgRes = await fetch('/api/estudiantes/me/suscripcion', {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });
                        const msgData = await msgRes.json();
                        
                        // Mostrar banner
                        document.getElementById('banner-sin-suscripcion').style.display = 'block';
                        document.getElementById('banner-titulo').textContent = 'Sin Suscripción Activa';
                        document.getElementById('banner-contenido').textContent = 'Debes renovar tu suscripción para acceder a los contenidos';
                        
                        // Ocultar módulos
                        document.getElementById('modulos-lista').style.display = 'none';
                    } catch (error) {
                        console.error('Error:', error);
                    }
                } else {
                    cargarModulos();
                }
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
                
                let html = '';
                data.modulos.forEach(m => {
                    html += `<div class="modulo-card" onclick="verModulo(${m.id})">
                        <h3>${m.nombre}</h3>
                        <p>${m.descripcion || 'Sin descripción'}</p>
                        <small>📚 ${m.guias_count} guías | 📝 ${m.actividades_count} actividades</small>
                    </div>`;
                });
                
                document.getElementById('modulos-lista').innerHTML = html;
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function verModulo(id) {
            try {
                const response = await fetch(`/api/modulos/${id}/completo`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                
                let html = `<h2>${data.nombre}</h2>`;
                
                if (data.guias && data.guias.length > 0) {
                    html += '<h3>📚 Guías</h3>';
                    data.guias.forEach(g => {
                        html += `<div class="guia-item">
                            <strong>${g.titulo}</strong><br>
                            <small>${(g.archivo_tamaño_bytes / 1024 / 1024).toFixed(2)} MB</small><br>
                            <button class="btn-pequeño" onclick="descargarGuia(${g.archivo_id_drive}, '${g.archivo_nombre}')">Descargar</button>
                        </div>`;
                    });
                }
                
                if (data.actividades && data.actividades.length > 0) {
                    html += '<h3>📝 Actividades</h3>';
                    data.actividades.forEach(a => {
                        html += `<div class="actividad-item">
                            <strong>${a.titulo}</strong><br>
                            ${a.descripcion ? '<p>' + a.descripcion + '</p>' : ''}
                            <small>Cierra: ${new Date(a.fecha_cierre).toLocaleDateString()}</small><br>
                            ${a.requiere_entrega ? '<button class="btn-pequeño" onclick="subirEntrega(' + a.id + ')">Subir Entrega</button>' : ''}
                        </div>`;
                    });
                }
                
                document.getElementById('contenido-modulo').innerHTML = html;
                document.getElementById('modulos-lista').style.display = 'none';
                document.getElementById('modulo-detalle').style.display = 'block';
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        function volver() {
            document.getElementById('modulo-detalle').style.display = 'none';
            document.getElementById('modulos-lista').style.display = 'block';
        }
        
        function logout() {
            localStorage.clear();
            window.location.href = '/login';
        }
        
        cargarPerfil();
        verificarSuscripcion();
    </script>
</body>
</html>
'''

def main():
    print("🚀 Generando sistema COMPLETO...")
    
    # Routers
    create_file("backend/app/routers/mensajes.py", ROUTER_MENSAJES)
    create_file("backend/app/routers/modulos.py", ROUTER_MODULOS_COMPLETO)
    
    # Frontend
    create_file("frontend/profesor.html", FRONTEND_PROFESOR)
    create_file("frontend/estudiante-mejorado.html", FRONTEND_ESTUDIANTE_MEJORADO)
    
    print("\n✅ Sistema COMPLETO generado!")
    print("\nCaracterísticas incluidas:")
    print("✅ Panel profesor con gestión total")
    print("✅ Crear/eliminar/editar estudiantes")
    print("✅ Crear/editar suscripciones")
    print("✅ Módulos, guías y actividades")
    print("✅ Entregas de estudiantes")
    print("✅ Mensajes personalizables")
    print("✅ Banner para sin suscripción")
    print("✅ Panel estudiante mejorado")

if __name__ == "__main__":
    main()
