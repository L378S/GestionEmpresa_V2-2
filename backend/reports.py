from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import io
import os

def generar_reporte_pdf(datos, titulo, empresa):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    # Titulo
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, alignment=1)
    elements.append(Paragraph(titulo, title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Datos empresa
    empresa_data = [
        [Paragraph(f"<b>{empresa.get('nombre', 'Mi Empresa')}</b>", styles['Normal'])],
        [f"RUC: {empresa.get('ruc', '')}"],
        [f"Direccion: {empresa.get('direccion', '')}"]
    ]
    for info in empresa_data:
        elements.append(Paragraph(info[0], styles['Normal']))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Fecha y usuario
    elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Paragraph(f"Usuario: {datos.get('usuario', '')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Tabla de datos
    if datos.get('tabla') and len(datos['tabla']) > 0:
        table_data = [datos['columnas']] + datos['tabla']
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2E4053')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        elements.append(table)
    
    # Totales
    if datos.get('totales'):
        elements.append(Spacer(1, 0.2*inch))
        total_data = [["Total General", f"$. {datos['totales']:,.2f}"]]
        total_table = Table(total_data, colWidths=[4*inch, 2*inch])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F2C94C')),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('ALIGN', (1,0), (1,0), 'RIGHT')
        ]))
        elements.append(total_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer