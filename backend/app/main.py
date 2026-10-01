from fastapi import FastAPI
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
