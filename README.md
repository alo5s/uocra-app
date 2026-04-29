# UOCRA - Sistema de Gestión de CVs (v2)

Sistema de gestión de currículums para la **Unión Obrera de la Construcción de la República Argentina (UOCRA)**. Panel administrativo con extracción automática de datos desde PDFs usando IA/OCR.

## 📋 Descripción

Plataforma completa para la gestión de CVs de trabajadores de la construcción. Permite:
- Carga de CVs con extracción automática de datos (OCR + IA)
- Gestión de empresas afiliadas
- Dashboard con estadísticas y gráficos
- Portal público con código QR para que los trabajadores suban sus CVs
- Sistema de notas y seguimiento
- Historial de actividad y notificaciones

## 🔧 Requisitos Previos

- **Python 3.11+** (Backend)
- **Node.js 18+** y npm (Frontend)
- **tesseract-ocr** (para extracción de texto de imágenes)
- **SQLite** (desarrollo) / **PostgreSQL** (producción opcional)

### Instalación de dependencias del sistema (Linux)
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev tesseract-ocr-spa
sudo apt-get install -y libopencv-dev python3-opencv
```

## 🚀 Instalación Paso a Paso

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/uocra-app.git
cd uocra-app
```

### 2. Configurar el Backend
```bash
cd backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales (generar SECRET_KEY con: openssl rand -hex 32)
```

### 3. Configurar el Frontend
```bash
cd frontend-v2

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env.production  # Para producción
# Editar .env.production con tu dominio
```

## 🔧 Configuración de Variables de Entorno

### Backend (`backend/.env`)
```env
SECRET_KEY=tu_clave_generada_con_openssl_rand_hex_32
ADMIN_USERNAME=tu_usuario_admin
ADMIN_PASSWORD=tu_password_seguro
DEBUG=false  # true para desarrollo
DATABASE_URL=sqlite:///./uocra.db
ALLOWED_ORIGINS=http://localhost:5173,https://tu-dominio.com
```

### Frontend (`frontend-v2/.env.production`)
```env
VITE_API_URL=https://tu-dominio.com/api
```

## 🏃 Levantar en Desarrollo

### Opción 1: Script automático
```bash
./scripts/start-dev.sh
```

### Opción 2: Manual

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Terminal 2 - Frontend:**
```bash
cd frontend-v2
npm run dev
# App: http://localhost:5173 (o 5174)
```

## 📁 Estructura del Proyecto

```
uocra-app/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/              # Endpoints REST (auth, cvs, empresas, etc.)
│   │   ├── core/             # Config, DB, Security
│   │   ├── models/           # Modelos SQLAlchemy
│   │   ├── schemas/          # Esquemas Pydantic
│   │   └── utils/            # Utilidades (OCR, PDF, etc.)
│   ├── static/               # Archivos estáticos (uploads, fotos, logos)
│   ├── requirements.txt      # Dependencias Python
│   ├── .env.example         # Variables de entorno (ejemplo)
│   └── Dockerfile           # Imagen Docker
│
├── frontend-v2/              # React + Vite Frontend
│   ├── src/
│   │   ├── api/             # Cliente Axios configurado
│   │   ├── components/      # Componentes reutilizables
│   │   ├── pages/           # Vistas/Páginas
│   │   ├── store/           # Zustand stores (estado global)
│   │   └── types/           # TypeScript types (si aplica)
│   ├── public/              # Archivos públicos
│   ├── nginx.conf           # Configuración Nginx para producción
│   ├── Dockerfile           # Multi-stage build
│   └── package.json
│
├── screenshots/              # Screenshots de la aplicación
├── scripts/                 # Scripts de utilidad
│   └── start-dev.sh        # Inicio rápido desarrollo
├── .gitignore              # Archivos ignorados por Git
├── docker-compose.yml      # Orquestación de servicios
├── GUIA.md                 # Guía de pantallas
└── README.md              # Este archivo
```

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** FastAPI 0.115+
- **ORM:** SQLAlchemy 2.0+
- **Validación:** Pydantic 2.0+
- **Autenticación:** JWT (python-jose)
- **Base de datos:** SQLite (dev) / PostgreSQL (prod)
- **Extracción:** Tesseract OCR, OpenCV, pdfplumber
- **Servidor:** Uvicorn

### Frontend
- **Framework:** React 18
- **Build tool:** Vite 5
- **Estilos:** TailwindCSS 3
- **Estado:** Zustand
- **HTTP Client:** Axios
- **Routing:** React Router DOM 7
- **Icons:** Bootstrap Icons

### Despliegue
- **Contenedores:** Docker + Docker Compose
- **Servidor web:** Nginx (frontend)
- **Orquestación:** Docker Compose

## 🐳 Despliegue con Docker

```bash
# Construir y levantar todos los servicios
docker-compose up --build -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

Accede a:
- Frontend: http://localhost (puerto 80)
- Backend API: http://localhost:8000

## 📝 Funcionalidades Principales

- ✅ Login/Logout con JWT
- ✅ Dashboard con estadísticas y gráficos
- ✅ Gestión de CVs (CRUD completo)
- ✅ Extracción automática de datos desde PDFs (OCR + IA)
- ✅ Aprobar/Rechazar CVs pendientes
- ✅ Gestión de Empresas (CRUD)
- ✅ Gestión de Usuarios (solo admin)
- ✅ Sistema de Notas y Documentos adjuntos
- ✅ Historial de actividad
- ✅ Notificaciones en tiempo real
- ✅ Portal público para subir CVs (QR)
- ✅ Filtros avanzados y búsqueda

## 🔒 Seguridad

- Credenciales almacenadas en `.env` (NUNCA se suben al repositorio)
- Contraseñas hasheadas con bcrypt
- Autenticación JWT con expiración
- CORS configurado por origen
- Variables sensibles en `.env.example` con valores de ejemplo

## 📄 Licencia

UOCRA - Unión Obrera de la Construcción de la República Argentina

---

**Equipo de Gestión de Ricardo Treuquil**
