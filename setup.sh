#!/bin/bash

echo "🚀 Setup Aula Virtual - Instalación Automática"
echo "================================================"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Crear entorno virtual
echo -e "${BLUE}1. Creando entorno virtual Python...${NC}"
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
echo -e "${BLUE}2. Instalando dependencias...${NC}"
pip install -r requirements.txt

# 3. Verificar PostgreSQL
echo -e "${BLUE}3. Verificando PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL no está instalado${NC}"
    echo "Instala con: sudo apt install postgresql -y"
    exit 1
fi

# 4. Crear BD si no existe
echo -e "${BLUE}4. Configurando base de datos...${NC}"
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'aula_db'" | grep -q 1 || \
psql -U postgres << EOF
CREATE USER aula_user WITH PASSWORD 'aula_password';
CREATE DATABASE aula_db OWNER aula_user;
GRANT ALL PRIVILEGES ON DATABASE aula_db TO aula_user;
EOF

# 5. Configurar service_account.json
echo -e "${BLUE}5. Configurando Google Drive...${NC}"
if [ ! -f "service_account.json" ]; then
    echo -e "${RED}⚠️  Falta service_account.json${NC}"
    echo "Pasos:"
    echo "1. Ve a https://console.cloud.google.com/"
    echo "2. Crea un proyecto llamado 'aula-virtual'"
    echo "3. Habilita Google Drive API"
    echo "4. Crea un Service Account"
    echo "5. Descarga el JSON y cópialo aquí como 'service_account.json'"
    echo ""
    read -p "Presiona Enter cuando hayas copiado el archivo..."
fi

# 6. Crear carpetas en Google Drive (manual por ahora)
echo -e "${BLUE}6. Google Drive listo para usar${NC}"
echo "Crea esta estructura en Google Drive:"
echo "AULA_VIRTUAL/"
echo "├── MODULO_01/"
echo "│   ├── GUIAS/"
echo "│   └── ENTREGAS/"
echo "├── MODULO_02/..."
echo ""

# 7. Inicializar BD
echo -e "${BLUE}7. Inicializando base de datos...${NC}"
cd backend
python3 << 'EOFPYTHON'
from app.database import init_db
init_db()
print("✅ Base de datos inicializada")
EOFPYTHON
cd ..

echo ""
echo -e "${GREEN}✅ Setup completado!${NC}"
echo ""
echo "Para iniciar el servidor:"
echo "  cd backend"
echo "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "URL: http://localhost:8000"
