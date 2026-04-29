from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session
import io
import urllib.request
import urllib.parse

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="", tags=["public"])


@router.get("/publico/subir-cv")
def pagina_subir_cv():
    from fastapi.responses import HTMLResponse
    html_content = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subir mi CV - UOCRA</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        .card-form {
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { color: #1e3c72; font-size: 1.8rem; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: 500; color: #333; }
        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
        }
        .btn {
            width: 100%;
            padding: 15px;
            background: #1e3c72;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
        }
        .btn:hover { background: #2a5298; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card-form">
            <h1><i class="bi bi-file-earmark-person"></i> Subir mi CV</h1>
            <form id="cvForm">
                <div class="form-group">
                    <label>Nombre *</label>
                    <input type="text" name="nombre" required>
                </div>
                <div class="form-group">
                    <label>Apellido *</label>
                    <input type="text" name="apellido" required>
                </div>
                <div class="form-group">
                    <label>DNI</label>
                    <input type="text" name="dni">
                </div>
                <div class="form-group">
                    <label>Teléfono</label>
                    <input type="tel" name="telefono">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email">
                </div>
                <div class="form-group">
                    <label>Fecha de nacimiento</label>
                    <input type="date" name="fecha_nacimiento">
                </div>
                <div class="form-group">
                    <label>Oficios (separados por coma)</label>
                    <input type="text" name="oficios" placeholder="Ej: Electricista, Soldador">
                </div>
                <button type="submit" class="btn">Enviar CV</button>
            </form>
        </div>
    </div>
    <script>
        document.getElementById('cvForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            try {
                const response = await fetch('/api/cvs/public', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                if (response.ok) {
                    alert('CV enviado exitosamente. Un administrador lo revisará.');
                    e.target.reset();
                } else {
                    alert('Error al enviar CV');
                }
            } catch (error) {
                alert('Error al enviar CV');
            }
        });
    </script>
</body>
</html>'''
    return HTMLResponse(content=html_content)


@router.get("/bienvenido/pdf")
def generar_bienvenido_pdf(
    db: Session = Depends(get_db)
):
    base_url = settings.BASE_URL
    qr_url = f"{base_url}/subir-cv" if base_url else "http://localhost:5173/subir-cv"
    
    buffer = io.BytesIO()
    page_width, page_height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # Header azul
    margin_top = 5
    header_h = 95
    padding_top = 30
    center_x = page_width / 2
    
    c.setFillColor(HexColor('#1e3c72'))
    c.rect(0, page_height - (header_h + margin_top), page_width, header_h + margin_top, fill=True, stroke=False)
    
    # Texto header
    top_y = page_height - margin_top - padding_top
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 26)
    c.drawCentredString(center_x, top_y, 'UOCRA')
    c.setFont('Helvetica', 9)
    c.drawCentredString(center_x, top_y - 11, 'Unión Obrera de la Construcción de la República Argentina')
    c.setFont('Helvetica', 11)
    c.drawCentredString(center_x, top_y - 30, 'Secretario General Z.N.S.C ')
    c.drawCentredString(center_x, top_y - 44, 'Ricardo Treuquil')
    
    # Bienvenida
    c.setFillColor(black)
    base_y = page_height - (header_h + margin_top)
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(center_x, base_y - 35, 'Bienvenido')
    c.setFont('Helvetica', 12)
    c.drawCentredString(center_x, base_y - 55, 'Carga tu curriculum vitae y forma parte de')
    c.drawCentredString(center_x, base_y - 70, 'nuestra base de datos de trabajadores')
    
    # Card QR
    card_h = 270
    card_y = base_y - 360
    c.setFillColor(HexColor('#f5f7fa'))
    c.roundRect(50, card_y, page_width - 100, card_h, 16, fill=True, stroke=False)
    c.setFillColor(black)
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(center_x, card_y + card_h - 40, 'Escanea el código QR para subir tu CV')
    
    # QR Code
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
    
    # Instrucciones
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
    
    # Footer
    c.setFont('Helvetica', 8)
    c.setFillColor(HexColor('#999999'))
    c.drawCentredString(center_x, 40, 'Generado automáticamente por UOCRA')
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type='application/pdf',
        headers={'Content-Disposition': 'attachment; filename=uocra_bienvenida.pdf'}
    )


@router.get("/bienvenido")
def bienvenido_html():
    from fastapi.responses import HTMLResponse
    qr_url = "/subir-cv"
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
        }
        .welcome-header h4 { font-size: 2.2rem; color: #1e3c72; margin-bottom: 8px; font-weight: 700; letter-spacing: 1px; }
        .organization { font-size: 2rem; color: #c62828; font-weight: 700; margin: 5px 0; text-transform: uppercase; letter-spacing: 2px; }
        .position { font-size: 1rem; color: #333; font-weight: 500; margin-top: 15px; text-transform: uppercase; padding-bottom: 20px; border-bottom: 2px solid #1e3c72; display: inline-block; }
        .welcome-header p { font-size: 1.1rem; color: #6c757d; margin-bottom: 30px; }
        .qr-section { background: #f5f7fa; border-radius: 16px; padding: 30px; margin: 20px 0; }
        .qr-section h3 { margin-bottom: 15px; color: #333333; }
        .qr-code { display: inline-block; padding: 15px; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .qr-code img { display: block; }
        .btn { display: inline-block; padding: 15px 40px; border-radius: 30px; text-decoration: none; font-size: 1.1rem; font-weight: 600; transition: all 0.3s; margin: 10px 5px; }
        .btn-primary { background: #1e3c72; color: white; }
        .btn-primary:hover { background: #2a5298; transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,0,0,0.3); }
        .btn-success { background: #28a745; color: white; }
        .btn-success:hover { background: #218838; transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,0,0,0.3); }
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
            <div class="qr-section">
                <h3>Escaneá el código QR para subir tu CV</h3>
                <div class="qr-code">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=/subir-cv" alt="Código QR para subir tu CV">
                </div>
            </div>
            <a href="/subir-cv" class="btn btn-primary" target="_blank">Subir mi CV</a>
            <a href="/bienvenido/pdf" class="btn btn-success" download>Descargar PDF</a>
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