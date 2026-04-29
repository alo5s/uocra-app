import os
import re
import random
import string
import uuid
import shutil
from datetime import datetime
from typing import Optional, List
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import CV, User, Historial, Notificacion, CVEmpresa, Empresa
from app.schemas.schemas import (
    CVCreate, CVUpdate, CVResponse, CVPublicCreate, MessageResponse
)
from app.utils.pdf_extractor import extraer_datos_cv, guardar_pdf_temp, limpiar_temp

router = APIRouter(prefix="/cvs", tags=["cvs"])


def sanitize_input(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = re.sub(r'[<>]', '', text)
    return text.strip()


def get_upload_path() -> str:
    ahora = datetime.now()
    carpeta = os.path.join('static', 'uploads', str(ahora.year), f'{ahora.month:02d}')
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def get_temp_path() -> str:
    carpeta = os.path.join('static', 'temp')
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def get_photos_path() -> str:
    carpeta = os.path.join('static', 'photos')
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def guardar_pdf_temp(file: UploadFile) -> tuple[str, str]:
    carpeta = get_temp_path()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    filename = f"temp_{timestamp}_{random_str}.pdf"
    filepath = os.path.join(carpeta, filename)
    
    with open(filepath, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    
    return filepath, filename


def mover_pdf_a_uploads(temp_path: str, dni: str = '') -> str:
    carpeta = get_upload_path()
    ahora = datetime.now()
    
    if dni:
        nombre_limpio = sanitize_input(dni) or ''
        new_filename = f"{nombre_limpio}_{ahora.strftime('%Y%m%d_%H%M')}.pdf"
    else:
        safe = os.path.basename(temp_path).replace('.pdf', '')
        new_filename = f"{safe}_{ahora.strftime('%Y%m%d_%H%M')}.pdf"
    
    new_path = os.path.join(carpeta, new_filename)
    shutil.move(temp_path, new_path)
    return new_path


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.lower().endswith('.pdf')


def registrar_historial(db: Session, accion: str, tipo: str, descripcion: str, entidad_id: int = None, user_id: int = None):
    historial = Historial(
        accion=accion,
        tipo=tipo,
        descripcion=descripcion,
        entidad_id=entidad_id,
        user_id=user_id
    )
    db.add(historial)
    db.commit()


def crear_notificacion(db: Session, tipo: str, titulo: str, mensaje: str, user_id: int = None):
    notificacion = Notificacion(
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        user_id=user_id
    )
    db.add(notificacion)
    db.commit()


def crear_notificacion_a_todos_admin(db: Session, tipo: str, titulo: str, mensaje: str):
    admins = db.query(User).filter(User.is_admin == True, User.is_active == True).all()
    for admin in admins:
        notificacion = Notificacion(
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            user_id=admin.id
        )
        db.add(notificacion)
    db.commit()


# ==================== ENDPOINTS ====================

@router.get("", response_model=dict)
def get_cvs(
    nombre: str = Query(None),
    categoria: str = Query(None),
    oficio: str = Query(None),
    genero: str = Query(None),
    afiliado: str = Query(None),
    sin_experiencia: bool = Query(None),
    empresa: int = Query(None),
    estado: str = Query("aprobado"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(CV).filter(CV.estado == estado)
    
    if nombre:
        query = query.filter(
            or_(
                CV.nombre.ilike(f'%{nombre}%'),
                CV.dni.ilike(f'%{nombre}%')
            )
        )
    if categoria:
        query = query.filter(CV.area == categoria)
    if oficio:
        query = query.filter(CV.oficios.ilike(f'%{oficio}%'))
    if genero:
        query = query.filter(CV.genero == genero)
    if afiliado:
        query = query.filter(CV.afiliado == afiliado)
    if sin_experiencia:
        cv_con_empresa = db.query(CVEmpresa.cv_id).distinct().subquery()
        query = query.filter(
            CV.sin_experiencia == True,
            ~CV.id.in_(cv_con_empresa)
        )
    if empresa:
        query = query.join(CVEmpresa).filter(CVEmpresa.empresa_id == empresa)
    
    total = query.count()
    cvs = query.order_by(CV.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "items": [CVResponse.model_validate(cv) for cv in cvs],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }


@router.get("/{cv_id}", response_model=CVResponse)
def get_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    return CVResponse.model_validate(cv)


@router.post("", response_model=CVResponse)
def create_cv(
    file: UploadFile = File(None),
    nombre: str = Form(None),
    dni: str = Form(None),
    fecha_nacimiento: str = Form(None),
    genero: str = Form(None),
    domicilio: str = Form(None),
    email: str = Form(None),
    telefono: str = Form(None),
    oficios: str = Form(None),
    area: str = Form(None),
    afiliado: str = Form("no"),
    fue_afiliado: str = Form("false"),
    apodo: str = Form(None),
    sin_experiencia: str = Form("false"),
    tiene_documentacion: str = Form("false"),
    tiene_licencia: str = Form("false"),
    linea_conducir: str = Form(None),
    modo_deteccion: str = Form("automatico"),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear CV")
    
    final_path = None
    foto_final = None
    filename = None
    
    if file and allowed_file(file.filename):
        temp_path, temp_filename = guardar_pdf_temp(file)
        filename = file.filename
        final_path = mover_pdf_a_uploads(temp_path, dni or '')
    
    foto_final = None
    if foto and foto.filename:
        photos_folder = get_photos_path()
        os.makedirs(photos_folder, exist_ok=True)
        ext = foto.filename.rsplit('.', 1)[1].lower() if '.' in foto.filename else 'jpg'
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        foto_filename = f"foto_{dni or timestamp}_{timestamp}.{ext}"
        foto_path = os.path.join(photos_folder, foto_filename)
        
        with open(foto_path, 'wb') as f:
            shutil.copyfileobj(foto.file, f)
        
        foto_final = f"static/photos/{foto_filename}"
    
    fue_afiliado_bool = fue_afiliado.lower() == "true" if fue_afiliado else False
    sin_experiencia_bool = sin_experiencia.lower() == "true" if sin_experiencia else False
    tiene_documentacion_bool = tiene_documentacion.lower() == "true" if tiene_documentacion else False
    tiene_licencia_bool = tiene_licencia.lower() == "true" if tiene_licencia else False
    
    cv = CV(
        filename=sanitize_input(filename),
        path=sanitize_input(final_path),
        nombre=sanitize_input(nombre),
        dni=sanitize_input(dni),
        fecha_nacimiento=sanitize_input(fecha_nacimiento),
        genero=sanitize_input(genero),
        domicilio=sanitize_input(domicilio),
        email=sanitize_input(email),
        telefono=sanitize_input(telefono),
        oficios=sanitize_input(oficios),
        area=sanitize_input(area),
        foto=foto_final,
        afiliado=afiliado,
        fue_afiliado=fue_afiliado_bool,
        apodo=sanitize_input(apodo),
        sin_experiencia=sin_experiencia_bool,
        tiene_documentacion=tiene_documentacion_bool,
        tiene_licencia=tiene_licencia_bool,
        linea_conducir=sanitize_input(linea_conducir),
        modo_deteccion=modo_deteccion,
        estado='aprobado',
        origen='web',
        user_id=current_user.id
    )
    
    db.add(cv)
    db.commit()
    db.refresh(cv)
    
    registrar_historial(db, 'crear', 'CV', f'Creó CV: {nombre or "Sin nombre"}', cv.id, current_user.id)
    crear_notificacion(db, 'cv', 'Nuevo CV', f'Se agregó un nuevo CV: {nombre or "Sin nombre"}')
    
    return CVResponse.model_validate(cv)


@router.put("/{cv_id}", response_model=CVResponse)
def update_cv(
    cv_id: int,
    nombre: str = Form(None),
    dni: str = Form(None),
    fecha_nacimiento: str = Form(None),
    genero: str = Form(None),
    domicilio: str = Form(None),
    email: str = Form(None),
    telefono: str = Form(None),
    oficios: str = Form(None),
    area: str = Form(None),
    afiliado: str = Form(None),
    fue_afiliado: bool = Form(None),
    apodo: str = Form(None),
    sin_experiencia: bool = Form(None),
    tiene_documentacion: bool = Form(None),
    tiene_licencia: bool = Form(None),
    linea_conducir: str = Form(None),
    modo_deteccion: str = Form(None),
    estado: str = Form(None),
    foto: UploadFile = File(None),
    activo: bool = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar CV")
    
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    
    if nombre is not None:
        cv.nombre = sanitize_input(nombre)
    if dni is not None:
        cv.dni = sanitize_input(dni)
    if fecha_nacimiento is not None:
        cv.fecha_nacimiento = sanitize_input(fecha_nacimiento)
    if genero is not None:
        cv.genero = sanitize_input(genero)
    if domicilio is not None:
        cv.domicilio = sanitize_input(domicilio)
    if email is not None:
        cv.email = sanitize_input(email)
    if telefono is not None:
        cv.telefono = sanitize_input(telefono)
    if oficios is not None:
        cv.oficios = sanitize_input(oficios)
    if area is not None:
        cv.area = sanitize_input(area)
    if afiliado is not None:
        cv.afiliado = afiliado
    if fue_afiliado is not None:
        cv.fue_afiliado = fue_afiliado
    if apodo is not None:
        cv.apodo = sanitize_input(apodo)
    if sin_experiencia is not None:
        cv.sin_experiencia = sin_experiencia
    if tiene_documentacion is not None:
        cv.tiene_documentacion = tiene_documentacion
    if linea_conducir is not None:
        cv.linea_conducir = sanitize_input(linea_conducir)
    if modo_deteccion is not None:
        cv.modo_deteccion = modo_deteccion
    if estado is not None:
        cv.estado = estado
    if tiene_licencia is not None:
        cv.tiene_licencia = tiene_licencia
    if activo is not None:
        cv.activo = activo
    
    if foto and foto.filename:
        photos_folder = get_photos_path()
        os.makedirs(photos_folder, exist_ok=True)
        ext = foto.filename.rsplit('.', 1)[1].lower() if '.' in foto.filename else 'jpg'
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        foto_filename = f"foto_{cv.dni or cv.id}_{timestamp}.{ext}"
        foto_path = os.path.join(photos_folder, foto_filename)
        
        with open(foto_path, 'wb') as f:
            shutil.copyfileobj(foto.file, f)
        
        if cv.foto and os.path.exists(cv.foto.replace('static/', 'backend/')):
            try:
                os.remove(cv.foto.replace('static/', 'backend/'))
            except:
                pass
        
        cv.foto = f"static/photos/{foto_filename}"
    
    db.commit()
    db.refresh(cv)
    
    action = "aprobar" if estado == "aprobado" else "editar"
    registrar_historial(db, action, 'CV', f'Editó/Aprobó CV: {cv.nombre}', cv.id, current_user.id)
    
    if estado == "aprobado":
        crear_notificacion_a_todos_admin(db, 'cv', 'CV Aprobado', f'El CV de {cv.nombre} ha sido aprobado.')
    
    return CVResponse.model_validate(cv)


@router.delete("/{cv_id}", response_model=MessageResponse)
def delete_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar CV")
    
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    
    nombre_cv = cv.nombre
    
    if cv.path and os.path.exists(cv.path):
        os.remove(cv.path)
    if cv.foto and os.path.exists(cv.foto):
        try:
            os.remove(cv.foto)
        except:
            pass
    
    db.delete(cv)
    db.commit()
    
    registrar_historial(db, 'eliminar', 'CV', f'Eliminó CV: {nombre_cv}', user_id=current_user.id)
    crear_notificacion(db, 'cv', 'CV Eliminado', f'Se eliminó el CV: {nombre_cv}')
    
    return MessageResponse(message="CV eliminado exitosamente")


@router.post("/{cv_id}/aprobar", response_model=CVResponse)
def aprobar_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    
    cv.estado = "aprobado"
    db.commit()
    db.refresh(cv)
    
    crear_notificacion_a_todos_admin(db, 'cv', 'CV Aprobado', f'El CV de {cv.nombre} ha sido aprobado.')
    registrar_historial(db, 'aprobar', 'CV', f'Aprobó CV: {cv.nombre}', cv.id, current_user.id)
    
    return CVResponse.model_validate(cv)


@router.post("/{cv_id}/rechazar", response_model=MessageResponse)
def rechazar_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    
    nombre_cv = cv.nombre
    
    if cv.path and os.path.exists(cv.path):
        os.remove(cv.path)
    if cv.foto and os.path.exists(cv.foto):
        try:
            os.remove(cv.foto)
        except:
            pass
    
    db.delete(cv)
    db.commit()
    
    crear_notificacion_a_todos_admin(db, 'cv', 'CV Rechazado', f'El CV de {nombre_cv} ha sido rechazado y eliminado.')
    
    return MessageResponse(message=f"CV de {nombre_cv} rechazado y eliminado")


@router.post("/public", response_model=MessageResponse)
def crear_cv_publico(
    nombre: str = Form(...),
    apellido: str = Form(...),
    dni: str = Form(None),
    fecha_nacimiento: str = Form(None),
    telefono: str = Form(None),
    email: str = Form(None),
    oficios: str = Form(None),
    file: UploadFile = File(None),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    final_path = None
    foto_final = None
    
    if file and allowed_file(file.filename):
        temp_dir = get_temp_path()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        safe_dni = sanitize_input(dni) or 'cv'
        pdf_filename = f"{safe_dni}_{timestamp}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        with open(pdf_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        final_path = mover_pdf_a_uploads(pdf_path, safe_dni)
    
    if foto and foto.filename:
        photos_folder = get_photos_path()
        ext = foto.filename.rsplit('.', 1)[1].lower() if '.' in foto.filename else 'jpg'
        foto_filename = f"foto_{dni or timestamp}_{timestamp}.{ext}"
        foto_path = os.path.join(photos_folder, foto_filename)
        
        with open(foto_path, 'wb') as f:
            shutil.copyfileobj(foto.file, f)
        
        foto_final = f"static/photos/{foto_filename}"
    
    nombre_completo = f"{nombre} {apellido}".strip()
    
    cv = CV(
        filename=f"CV_{dni}.pdf" if dni else "CV.pdf",
        path=final_path,
        nombre=nombre_completo,
        dni=dni,
        fecha_nacimiento=fecha_nacimiento,
        telefono=telefono,
        email=email,
        oficios=oficios,
        foto=foto_final,
        estado='pendiente',
        origen='qr',
        user_id=None
    )
    
    db.add(cv)
    db.commit()
    db.refresh(cv)
    
    crear_notificacion_a_todos_admin(db, 'cv_pendiente', 'Nuevo CV Pendiente', f'{nombre_completo} quiere subir su CV.')
    
    return MessageResponse(message="CV enviado exitosamente. Será revisado por un administrador.", success=True)


@router.get("/oficios/list", response_model=list[str])
def get_lista_oficios():
    from app.utils.oficios import get_all_oficios
    return get_all_oficios()


@router.post("/extraer", response_model=dict)
def extraer_datos_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para extraer datos")
    
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
    
    temp_path, temp_filename = guardar_pdf_temp(file)
    
    try:
        datos = extraer_datos_cv(temp_path)
    except Exception as e:
        print(f"Error extrayendo datos del PDF: {e}")
        datos = {
            "nombre": "", "dni": "", "fecha_nacimiento": "",
            "edad": "", "domicilio": "", "domicilios_opciones": [],
            "email": "", "telefono": "", "telefonos_opciones": [],
            "oficio": "", "oficios_detectados": [],
        }
    finally:
        limpiar_temp(temp_path)
    
    return datos


@router.get("/{cv_id}/empresas", response_model=list[dict])
def get_empresas_del_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cv_empresas = db.query(CVEmpresa).filter(CVEmpresa.cv_id == cv_id).order_by(CVEmpresa.fecha_ingreso.desc()).all()
    
    result = []
    for ce in cv_empresas:
        empresa = db.query(Empresa).filter(Empresa.id == ce.empresa_id).first()
        if empresa:
            result.append({
                "id": ce.id,
                "empresa_id": empresa.id,
                "empresa_nombre": empresa.nombre,
                "empresa_eliminada": empresa.deleted_at is not None,
                "fecha_eliminacion": empresa.deleted_at.isoformat() if empresa.deleted_at else None,
                "fecha_ingreso": ce.fecha_ingreso,
                "fecha_salida": ce.fecha_salida,
                "activo": ce.activo,
            })
        else:
            result.append({
                "id": ce.id,
                "empresa_id": ce.empresa_id,
                "empresa_nombre": "[Empresa eliminada]",
                "empresa_eliminada": True,
                "fecha_eliminacion": None,
                "fecha_ingreso": ce.fecha_ingreso,
                "fecha_salida": ce.fecha_salida,
                "activo": ce.activo,
            })
    
    return result


@router.post("/exportar-pdf")
def exportar_cvs_pdf(
    cv_ids: List[int] = Body(...),
    oficio_filtro: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    cvs = db.query(CV).filter(CV.id.in_(cv_ids), CV.estado == 'aprobado').all()
    
    if not cvs:
        raise HTTPException(status_code=404, detail="No se encontraron CVs")
    
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3c72'),
        alignment=1,
        spaceAfter=5,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1e3c72'),
        alignment=1,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    elements = []
    elements.append(Paragraph("LISTA DE TRABAJADORES", title_style))
    elements.append(Paragraph("UOCRA - Unión Obrera de la Construcción", subtitle_style))
    elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Total: {len(cvs)} trabajadores", styles['Normal']))
    elements.append(Spacer(1, 10))
    
    data = [['Nombre', 'DNI', 'Teléfono', 'Oficio', 'Categoría']]
    
    for cv in cvs:
        oficios = cv.oficios if cv.oficios else '-'
        if oficio_filtro:
            oficios = oficio_filtro
        else:
            if len(oficios) > 35:
                oficios = oficios[:35] + '...'
        
        data.append([
            cv.nombre or '-',
            cv.dni or '-',
            cv.telefono or '-',
            oficios,
            cv.area or '-'
        ])
    
    table = Table(data, colWidths=[50*mm, 25*mm, 28*mm, 50*mm, 25*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=12*mm, leftMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm)
    doc.build(elements)
    
    buffer.seek(0)
    filename = f"lista_trabajadores_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    return Response(
        content=buffer.getvalue(),
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@router.get("/bienvenido-pdf")
def bienvenido_pdf(
    db: Session = Depends(get_db)
):
    base_url = settings.BASE_URL
    qr_url = f"{base_url}/publico/subir-cv" if base_url else "http://localhost:8000/publico/subir-cv"
    
    buffer = io.BytesIO()
    page_width, page_height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    
    margin_top = 5
    header_h = 95
    padding_top = 30
    center_x = page_width / 2
    
    c.setFillColor(HexColor('#1e3c72'))
    c.rect(0, page_height - (header_h + margin_top), page_width, header_h + margin_top, fill=True, stroke=False)
    
    top_y = page_height - margin_top - padding_top
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 26)
    c.drawCentredString(center_x, top_y, 'UOCRA')
    c.setFont('Helvetica', 9)
    c.drawCentredString(center_x, top_y - 11, 'Unión Obrera de la Construcción de la República Argentina')
    c.setFont('Helvetica', 11)
    c.drawCentredString(center_x, top_y - 30, 'Secretario General Z.N.S.C ')
    c.drawCentredString(center_x, top_y - 44, 'Ricardo Treuquil')
    
    c.setFillColor(black)
    base_y = page_height - (header_h + margin_top)
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(center_x, base_y - 35, 'Bienvenido')
    c.setFont('Helvetica', 12)
    c.drawCentredString(center_x, base_y - 55, 'Carga tu curriculum vitae y forma parte de')
    c.drawCentredString(center_x, base_y - 70, 'nuestra base de datos de trabajadores')
    
    card_h = 270
    card_y = base_y - 360
    c.setFillColor(HexColor('#f5f7fa'))
    c.roundRect(50, card_y, page_width - 100, card_h, 16, fill=True, stroke=False)
    
    c.setFillColor(black)
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(center_x, card_y + card_h - 40, 'Escanea el código QR para subir tu CV')
    
    import urllib.request, urllib.parse
    qr_api_url = f'https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(qr_url)}'
    
    try:
        with urllib.request.urlopen(qr_api_url, timeout=10) as response:
            qr_data = response.read()
        qr_image = ImageReader(io.BytesIO(qr_data))
        qr_size = 170
        qr_x = center_x - qr_size / 2
        qr_y = card_y + 40
        c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size, preserveAspectRatio=True)
    except:
        c.setFillColor(white)
        c.roundRect(center_x - 85, card_y + 40, 170, 170, 12, fill=True, stroke=True)
        c.setFillColor(black)
        c.setFont('Helvetica', 10)
        c.drawCentredString(center_x, card_y + 120, 'QR Code')
    
    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(HexColor('#1e3c72'))
    c.drawCentredString(center_x, card_y - 20, '¿Cómo funciona?')
    
    instrucciones = [
        '1. Escanea el código QR con tu celular',
        '2. Completa tus datos personales',
        '3. Sube una foto tipo carnet (opcional)',
        '4. Un administrador revisará tu información'
    ]
    
    c.setFont('Helvetica', 11)
    c.setFillColor(black)
    y_pos = card_y - 50
    for ins in instrucciones:
        c.drawCentredString(center_x, y_pos, ins)
        y_pos -= 22
    
    c.setFont('Helvetica', 8)
    c.setFillColor(HexColor('#999999'))
    c.drawCentredString(center_x, 40, 'Generado automáticamente por UOCRA')
    
    c.save()
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type='application/pdf',
        headers={'Content-Disposition': 'attachment; filename=uocra_bienvenida.pdf'}
    )


@router.get("/bienvenido")
def bienvenido_html():
    from fastapi.responses import HTMLResponse
    html_content = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenido a UOCRA - Sube tu CV</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .welcome-container { max-width: 600px; width: 100%; text-align: center; }
        .welcome-header {
            background: white;
            padding: 50px 30px;
            border-radius: 20px 20px 0 0;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        .welcome-header h4 { font-size: 2.2rem; color: #1e3c72; margin-bottom: 8px; font-weight: 700; letter-spacing: 1px; }
        .organization { font-size: 2rem; color: #c62828; font-weight: 700; margin: 5px 0; text-transform: uppercase; letter-spacing: 2px; }
        .position { font-size: 1rem; color: #333; font-weight: 500; margin-top: 15px; text-transform: uppercase; padding-bottom: 20px; border-bottom: 2px solid #1e3c72; display: inline-block; }
        .welcome-header p { font-size: 1.1rem; color: #6c757d; margin-bottom: 30px; }
        .qr-section { background: #f5f7fa; border-radius: 16px; padding: 30px; margin: 20px 0; }
        .qr-section h3 { margin-bottom: 15px; color: #333333; }
        .qr-code { display: inline-block; padding: 15px; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .btn { display: inline-block; padding: 15px 40px; border-radius: 30px; text-decoration: none; font-size: 1.1rem; font-weight: 600; transition: all 0.3s; margin: 10px 5px; }
        .btn-primary { background: #1e3c72; color: white; }
        .btn-primary:hover { background: #2a5298; transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,0,0,0.3); }
        .instrucciones { background: white; padding: 30px; border-radius: 0 0 20px 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        .instrucciones h4 { color: #1e3c72; margin-bottom: 15px; }
        .instrucciones ol { text-align: left; padding-left: 25px; color: #555555; }
        .instrucciones li { margin-bottom: 10px; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="welcome-container">
        <div class="welcome-header">
            <h4>RICARDO TRUQUIL</h4>
            <p class="organization">UOCRA</p>
            <p class="position">SECRETARIO GENERAL</p>
            <div class="qr-section ">
                <h3>Escaneá el código QR para subir tu CV backend</h3>
                <div class="qr-code">
                    <img src="/api/cvs/bienvenido-pdf" alt="Código QR para descargar" onclick="window.location.href='/api/cvs/bienvenido-pdf'" style="cursor:pointer">
                </div>
            </div>
            <a href="/publico/subir-cv" class="btn btn-primary" target="_blank">Subir mi CV</a>
        </div>
        <div class="instrucciones">
            <h4>¿Cómo funciona?</h4>
            <ol>
                <li>Escaneá el código QR con tu celular o hacé clic en "Subir mi CV"</li>
                <li>Completá tus datos personales</li>
                <li>Subí una foto tipo carnet (opcional)</li>
                <li>¡Listo! Un administrador revisará tu información</li>
            </ol>
        </div>
    </div>
</body>
</html>'''
    return HTMLResponse(content=html_content)
