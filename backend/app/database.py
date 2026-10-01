from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base
from app.config import settings

# Crear engine (conexión a PostgreSQL)
engine = create_engine(
    settings.database_url,
    echo=False,  # Cambiar a True si quieres ver SQL queries en terminal
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear todas las tablas
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency para obtener sesión en endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
