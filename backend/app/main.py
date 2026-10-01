from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import auth, estudiantes
import os

# Inicializar BD
init_db()

app = FastAPI(
    title="Aula Virtual API",
    version="0.1.0",
    description="API para plataforma de educación virtual"
)

# CORS: permitir solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(estudiantes.router)

# Rutas simples
@app.get("/")
async def root():
    return {"message": "Bienvenido a Aula Virtual API", "version": "0.1.0"}

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
