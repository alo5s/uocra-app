#!/bin/bash

# UOCRA - Script de inicio rápido para desarrollo
# Uso: ./scripts/start-dev.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando UOCRA en modo desarrollo...${NC}"

# Directorio base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo -e "${YELLOW}📁 Directorio base: $BASE_DIR${NC}"

# Función para matar procesos al salir
cleanup() {
    echo -e "\n${RED}🛑 Deteniendo servicios...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${YELLOW}Backend detenido${NC}"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${YELLOW}Frontend detenido${NC}"
    fi
    exit 0
}

# Capturar Ctrl+C
trap cleanup INT TERM

# 1. Iniciar Backend
echo -e "${GREEN}🔧 Iniciando Backend (FastAPI)...${NC}"
cd "$BASE_DIR/backend"

# Verificar entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  No se encontró entorno virtual. Creando...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Verificar .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No se encontró backend/.env. Copiando desde .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}📝 IMPORTANTE: Edita backend/.env con tus credenciales${NC}"
fi

# Iniciar backend en background
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend iniciado en http://localhost:8000${NC}"
echo -e "${GREEN}   Docs disponibles en http://localhost:8000/docs${NC}"

# Esperar a que el backend esté listo
echo -e "${YELLOW}⏳ Esperando a que el backend esté listo...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend listo!${NC}"
        break
    fi
    sleep 1
done

# 2. Iniciar Frontend
echo -e "${GREEN}🎨 Iniciando Frontend (React + Vite)...${NC}"
cd "$BASE_DIR/frontend-v2"

# Verificar node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  No se encontraron node_modules. Instalando...${NC}"
    npm install
fi

# Iniciar frontend en background
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend iniciado${NC}"
echo -e "${GREEN}   URL: http://localhost:5173 (o 5174 según configuración)${NC}"

# Mostrar URLs
echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 UOCRA está listo!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}📍 Accede a:${NC}"
echo -e "   Frontend: http://localhost:5173"
echo -e "   Backend API: http://localhost:8000"
echo -e "   API Docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}🔑 Credenciales por defecto:${NC}"
echo -e "   Usuario: admin"
echo -e "   Contraseña: admin123"
echo -e "   (Configurables en backend/.env)"
echo ""
echo -e "${RED}Presiona Ctrl+C para detener todos los servicios${NC}"

# Esperar a que los procesos terminen
wait $BACKEND_PID $FRONTEND_PID
