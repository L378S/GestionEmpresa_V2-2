import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def enviar_notificacion(destinatario, asunto, mensaje):
    # Configuracion de email (usar variables de entorno en produccion)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_USER = "tu_email@gmail.com"
    EMAIL_PASSWORD = "tu_contraseña"
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = destinatario
        msg['Subject'] = asunto
        
        msg.attach(MIMEText(mensaje, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False

def notificar_nuevo_ingreso(ingreso, usuario_creador, admin_emails):
    asunto = f"Nuevo Ingreso Registrado - {ingreso.numero_factura}"
    mensaje = f"""
    <h3>Nuevo Ingreso Registrado</h3>
    <p><strong>Factura:</strong> {ingreso.numero_factura}</p>
    <p><strong>Cliente:</strong> {ingreso.cliente}</p>
    <p><strong>Concepto:</strong> {ingreso.concepto}</p>
    <p><strong>Monto:</strong> S/. {ingreso.monto:,.2f}</p>
    <p><strong>Registrado por:</strong> {usuario_creador}</p>
    <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    """
    
    for email in admin_emails:
        enviar_notificacion(email, asunto, mensaje)