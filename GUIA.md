# GUÍA DE PANTALLAS - UOCRA APP

## Login
- **Ruta:** /login
- **Screenshot:** ![login](./screenshots/login.png)
- **Descripción:** Pantalla de inicio de sesión para acceder al panel administrativo. Permite ingresar con usuario y contraseña.
- **Funcionalidades principales:**
  - Ingreso de usuario y contraseña
  - Visualización de logo UOCRA con animación
  - Opción para mostrar/ocultar contraseña
  - Validación de credenciales
- **Quién la usa:** admin

## Dashboard
- **Ruta:** /home
- **Screenshot:** ![dashboard](./screenshots/dashboard.png)
- **Descripción:** Panel principal con estadísticas generales del sistema, gráficos y resumen de actividad.
- **Funcionalidades principales:**
  - Tarjetas de estadísticas (Total CVs, Afiliados, Empresas, Notas)
  - Gráficos de distribución por oficio y categoría
  - Listado de empresas afiliadas recientes
  - Fecha y hora actual
  - Accesos rápidos a secciones principales
- **Quién la usa:** admin

## Listado de CVs
- **Ruta:** /cvs
- **Screenshot:** ![cvs](./screenshots/cvs.png)
- **Descripción:** Catálogo de currículums vitae con filtros avanzados y múltiples modos de visualización.
- **Funcionalidades principales:**
  - Vista de tarjetas o tabla
  - Filtros por nombre, categoría, oficio, género, afiliación y empresa
  - Selección múltiple para acciones en lote
  - Posibilidad de editar, ver o eliminar CVs
  - Paginación
- **Quién la usa:** admin

## Nuevo CV
- **Ruta:** /cv/nuevo
- **Screenshot:** ![cvs-nuevo](./screenshots/cvs-nuevo.png)
- **Descripción:** Formulario para cargar un nuevo CV mediante archivo PDF, con extracción automática de datos.
- **Funcionalidades principales:**
  - Carga de archivo PDF (máx 16MB)
  - Extracción automática de datos del PDF
  - Modo manual para carga de datos
  - Vista previa del PDF
  - Extracción de datos con IA (OCR)
- **Quién la usa:** admin

## Empresas
- **Ruta:** /empresas
- **Screenshot:** ![empresas](./screenshots/empresas.png)
- **Descripción:** Gestión de empresas constructoras, permite administrar la información de las empresas afiliadas y no afiliadas.
- **Funcionalidades principales:**
  - Listado de empresas en vista tarjetas o tabla
  - Filtros por nombre y estado de afiliación
  - Crear, editar y eliminar empresas
  - Subir logo de empresa
  - Ver detalles de cada empresa
- **Quién la usa:** admin

## Notas
- **Ruta:** /notas
- **Screenshot:** ![notas](./screenshots/notas.png)
- **Descripción:** Sistema de notas para adjuntar información a CVs o empresas, con soporte para archivos adjuntos.
- **Funcionalidades principales:**
  - Crear, editar y eliminar notas
  - Asociar notas a CVs o empresas
  - Adjuntar archivos
  - Filtros por tipo (asociadas a CV, empresa o generales)
  - Búsqueda de notas
- **Quién la usa:** admin

## Historial de Actividad
- **Ruta:** /actividad
- **Screenshot:** ![actividad](./screenshots/actividad.png)
- **Descripción:** Registro de todas las acciones realizadas en el sistema con notificaciones.
- **Funcionalidades principales:**
  - Historial completo de acciones
  - Notificaciones del sistema
  - Marcar notificaciones como leídas
  - Filtros por tipo de acción
  - Fecha y hora de cada evento
- **Quién la usa:** admin

## Portal QR (Bienvenido)
- **Ruta:** /cv/qr
- **Screenshot:** ![bienvenido](./screenshots/bienvenido.png)
- **Descripción:** Página pública con código QR para que los trabajadores puedan acceder a la carga de CVs.
- **Funcionalidades principales:**
  - Código QR descargable
  - Acceso directo a formulario de carga de CV
  - Interfaz pública sin autenticación
  - Información sobre el sistema UOCRA
- **Quién la usa:** público
