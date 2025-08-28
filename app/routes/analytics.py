"""
Rutas de analytics y reportes
Gráficas y estadísticas avanzadas
"""
import datetime
import json
import io
import tempfile
import os
from flask import Blueprint, render_template, jsonify, make_response
from app.auth.auth_service import login_required, get_current_user, premium_required
from app.services.crop_service import CropService

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
def dashboard():
    """Dashboard de analytics básico - también funciona en modo demo"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    # Obtener datos según si está autenticado o en modo demo
    if user:
        cultivos = crop_service.get_user_crops(user['uid'])
        total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
        demo_mode = False
    else:
        # Modo demo - mostrar datos de demostración completos
        cultivos = crop_service.get_demo_crops()
        total_kilos, total_beneficios = crop_service.get_demo_totals()
        demo_mode = True
    
    # Preparar datos para gráficas
    datos_cultivos = {}
    for cultivo in cultivos:
        nombre = cultivo['nombre']
        precio_kilo = cultivo.get('precio_por_kilo', 0)
        kilos_total = sum(p.get('kilos', 0) for p in cultivo.get('produccion_diaria', []))
        
        datos_cultivos[nombre] = {
            'kilos': kilos_total,
            'beneficio': kilos_total * precio_kilo
        }
    
    return render_template('analytics/dashboard.html',
                         datos_cultivos=datos_cultivos,
                         total_kilos=total_kilos,
                         total_beneficios=total_beneficios,
                         demo_mode=demo_mode)

@analytics_bp.route('/advanced')
def advanced():
    """Analytics avanzados - funciona en modo demo y para usuarios premium"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    # En modo demo, mostrar todas las funcionalidades premium
    if not user:
        # Modo demo - datos completos de demostración
        cultivos = crop_service.get_demo_crops()
        total_kilos, total_beneficios = crop_service.get_demo_totals()
        demo_mode = True
        plan = 'premium'  # Simular plan premium para mostrar todas las funciones
    else:
        # Usuario autenticado - verificar plan
        from app.auth.auth_service import UserService
        user_service = UserService(current_app.db)
        plan = user_service.get_user_plan(user['uid'])
        
        # Solo premium puede acceder (usuarios reales)
        if plan != 'premium':
            return jsonify({'error': 'Plan premium requerido'}), 403
        
        cultivos = crop_service.get_user_crops(user['uid'])
        total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
        demo_mode = False
    # Preparar datos avanzados para analytics
    # 1. Análisis temporal por meses
    monthly_data = {}
    for cultivo in cultivos:
        for produccion in cultivo.get('produccion_diaria', []):
            fecha = produccion['fecha']
            month_key = f"{fecha.year}-{fecha.month:02d}"
            if month_key not in monthly_data:
                monthly_data[month_key] = {'kilos': 0, 'beneficio': 0}
            monthly_data[month_key]['kilos'] += produccion['kilos']
            monthly_data[month_key]['beneficio'] += produccion['kilos'] * cultivo['precio_por_kilo']
    
    # 2. Ranking de cultivos más rentables
    cultivos_ranking = sorted(cultivos, key=lambda x: x.get('beneficio_total', 0), reverse=True)
    
    # 3. Proyecciones (simuladas para demo)
    proyeccion_anual = total_beneficios * 2.5  # Proyección optimista
    
    return render_template('analytics/advanced.html', 
                         cultivos=cultivos,
                         monthly_data=monthly_data,
                         cultivos_ranking=cultivos_ranking[:5],  # Top 5
                         total_kilos=total_kilos,
                         total_beneficios=total_beneficios,
                         proyeccion_anual=proyeccion_anual,
                         demo_mode=demo_mode,
                         plan=plan)

@analytics_bp.route('/api/chart-data')
def api_chart_data():
    """API para datos de gráficas - funciona en modo demo"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    # Obtener datos según si está autenticado o en modo demo
    if user:
        cultivos = crop_service.get_user_crops(user['uid'])
    else:
        cultivos = crop_service.get_demo_crops()
    
    # Preparar datos para Chart.js
    labels = []
    kilos_data = []
    beneficios_data = []
    
    for cultivo in cultivos:
        labels.append(cultivo['nombre'].title())
        
        kilos_total = sum(p.get('kilos', 0) for p in cultivo.get('produccion_diaria', []))
        precio_kilo = cultivo.get('precio_por_kilo', 0)
        
        kilos_data.append(kilos_total)
        beneficios_data.append(kilos_total * precio_kilo)
    
    return jsonify({
        'labels': labels,
        'datasets': [
            {
                'label': 'Kilogramos producidos',
                'data': kilos_data,
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 2
            },
            {
                'label': 'Beneficios (€)',
                'data': beneficios_data,
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 2
            }
        ]
    })

@analytics_bp.route('/export/csv')
def export_csv():
    """Exportar datos a CSV - funciona en modo demo"""
    from flask import current_app
    import csv
    import io
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    # Obtener datos según si está autenticado o en modo demo
    if user:
        cultivos = crop_service.get_user_crops(user['uid'])
        filename = f"huerto_datos_{user['uid'][:8]}.csv"
    else:
        cultivos = crop_service.get_demo_crops()
        filename = "huerto_demo_datos.csv"
    
    # Crear CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Cabeceras
    writer.writerow(['Cultivo', 'Fecha Siembra', 'Plantas', 'Precio/kg (€)', 
                    'Kilos Totales', 'Beneficio Total (€)', 'Estado'])
    
    # Datos
    for cultivo in cultivos:
        writer.writerow([
            cultivo['nombre'].title(),
            cultivo['fecha_siembra'].strftime('%Y-%m-%d'),
            cultivo.get('plantas_sembradas', 0),
            f"{cultivo.get('precio_por_kilo', 0):.2f}",
            f"{cultivo.get('kilos_totales', 0):.1f}",
            f"{cultivo.get('beneficio_total', 0):.2f}",
            'Activo' if cultivo.get('activo', True) else 'Cosechado'
        ])
    
    # Crear respuesta HTTP
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@analytics_bp.route('/export/json')
def export_json():
    """Exportar datos a JSON - funciona en modo demo"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    # Obtener datos según si está autenticado o en modo demo
    if user:
        cultivos = crop_service.get_user_crops(user['uid'])
        total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
    else:
        cultivos = crop_service.get_demo_crops()
        total_kilos, total_beneficios = crop_service.get_demo_totals()
    
    # Preparar datos para exportar
    export_data = {
        'resumen': {
            'total_cultivos': len(cultivos),
            'total_kilos': total_kilos,
            'total_beneficios': total_beneficios,
            'fecha_exportacion': datetime.datetime.now().isoformat()
        },
        'cultivos': []
    }
    
    for cultivo in cultivos:
        cultivo_data = {
            'nombre': cultivo['nombre'],
            'fecha_siembra': cultivo['fecha_siembra'].isoformat(),
            'plantas_sembradas': cultivo.get('plantas_sembradas', 0),
            'precio_por_kilo': cultivo.get('precio_por_kilo', 0),
            'kilos_totales': cultivo.get('kilos_totales', 0),
            'beneficio_total': cultivo.get('beneficio_total', 0),
            'activo': cultivo.get('activo', True),
            'produccion_detallada': [
                {
                    'fecha': p['fecha'].isoformat(),
                    'kilos': p['kilos']
                } for p in cultivo.get('produccion_diaria', [])
            ]
        }
        export_data['cultivos'].append(cultivo_data)
    
    filename = f"huerto_datos_{'demo' if not user else user['uid'][:8]}.json"
    
    # Crear respuesta HTTP
    response = make_response(json.dumps(export_data, indent=2, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@analytics_bp.route('/export/excel')
def export_excel():
    """Exportar datos a Excel con múltiples hojas - funciona en modo demo"""
    from flask import current_app
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.chart import BarChart, Reference
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    # Obtener datos según si está autenticado o en modo demo
    if user:
        cultivos = crop_service.get_user_crops(user['uid'])
        total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
        filename = f"huerto_analisis_{user['uid'][:8]}.xlsx"
    else:
        cultivos = crop_service.get_demo_crops()
        total_kilos, total_beneficios = crop_service.get_demo_totals()
        filename = "huerto_demo_analisis.xlsx"
    
    # Crear libro Excel
    wb = Workbook()
    
    # === HOJA 1: RESUMEN ===
    ws1 = wb.active
    ws1.title = "Resumen General"
    
    # Estilo para encabezados
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="198754", end_color="198754", fill_type="solid")
    
    # Título principal
    ws1['A1'] = "🌱 HuertoRentable - Análisis Completo"
    ws1['A1'].font = Font(bold=True, size=16, color="198754")
    ws1.merge_cells('A1:D1')
    
    # Resumen general
    ws1['A3'] = "Resumen General"
    ws1['A3'].font = header_font
    ws1['A3'].fill = header_fill
    ws1.merge_cells('A3:B3')
    
    ws1['A4'] = "Total Cultivos:"
    ws1['B4'] = len(cultivos)
    ws1['A5'] = "Producción Total:"
    ws1['B5'] = f"{total_kilos:.1f} kg"
    ws1['A6'] = "Beneficios Totales:"
    ws1['B6'] = f"€{total_beneficios:.2f}"
    ws1['A7'] = "Fecha Reporte:"
    ws1['B7'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # === HOJA 2: DETALLE CULTIVOS ===
    ws2 = wb.create_sheet(title="Detalle Cultivos")
    
    # Encabezados
    headers = ['Cultivo', 'Fecha Siembra', 'Plantas', 'Precio/kg (€)', 
               'Kilos Totales', 'Beneficio Total (€)', 'Estado']
    
    for col, header in enumerate(headers, 1):
        cell = ws2.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    
    # Datos de cultivos
    for row, cultivo in enumerate(cultivos, 2):
        ws2.cell(row=row, column=1, value=cultivo['nombre'].title())
        ws2.cell(row=row, column=2, value=cultivo['fecha_siembra'].strftime('%Y-%m-%d'))
        ws2.cell(row=row, column=3, value=cultivo.get('plantas_sembradas', 0))
        ws2.cell(row=row, column=4, value=cultivo.get('precio_por_kilo', 0))
        ws2.cell(row=row, column=5, value=cultivo.get('kilos_totales', 0))
        ws2.cell(row=row, column=6, value=cultivo.get('beneficio_total', 0))
        ws2.cell(row=row, column=7, value='Activo' if cultivo.get('activo', True) else 'Cosechado')
    
    # Ajustar anchos de columna
    for col in ws2.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 20)
        ws2.column_dimensions[column].width = adjusted_width
    
    # === HOJA 3: PRODUCCIÓN DETALLADA ===
    if cultivos and any(cultivo.get('produccion_diaria', []) for cultivo in cultivos):
        ws3 = wb.create_sheet(title="Producción Diaria")
        
        ws3['A1'] = "Producción Detallada por Día"
        ws3['A1'].font = header_font
        ws3['A1'].fill = header_fill
        ws3.merge_cells('A1:C1')
        
        headers_prod = ['Cultivo', 'Fecha', 'Kilos']
        for col, header in enumerate(headers_prod, 1):
            cell = ws3.cell(row=2, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        row = 3
        for cultivo in cultivos:
            for produccion in cultivo.get('produccion_diaria', []):
                ws3.cell(row=row, column=1, value=cultivo['nombre'].title())
                ws3.cell(row=row, column=2, value=produccion['fecha'].strftime('%Y-%m-%d'))
                ws3.cell(row=row, column=3, value=produccion['kilos'])
                row += 1
    
    # Guardar en memoria
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Crear respuesta HTTP
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@analytics_bp.route('/export/pdf')
def export_pdf():
    """Exportar reporte completo a PDF con reportlab - funciona en modo demo"""
    from flask import current_app
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    # Obtener datos según si está autenticado o en modo demo
    if user:
        cultivos = crop_service.get_user_crops(user['uid'])
        total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
        filename = f"huerto_reporte_{user['uid'][:8]}.pdf"
        titulo_usuario = f"Usuario: {user.get('email', 'Premium')}"
    else:
        cultivos = crop_service.get_demo_crops()
        total_kilos, total_beneficios = crop_service.get_demo_totals()
        filename = "huerto_demo_reporte.pdf"
        titulo_usuario = "Modo Demo"
    
    # Crear PDF en memoria
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Preparar estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#198754'),
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#198754')
    )
    
    # Contenido del PDF
    story = []
    
    # Título principal
    story.append(Paragraph("🌱 HuertoRentable", title_style))
    story.append(Paragraph("Reporte Completo de Análisis", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Información del usuario y fecha
    story.append(Paragraph(f"<b>{titulo_usuario}</b>", styles['Normal']))
    story.append(Paragraph(f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Resumen ejecutivo
    story.append(Paragraph("📊 Resumen Ejecutivo", heading_style))
    
    # Tabla de resumen
    resumen_data = [
        ['Métrica', 'Valor'],
        ['Total de Cultivos', str(len(cultivos))],
        ['Producción Total', f"{total_kilos:.1f} kg"],
        ['Beneficios Totales', f"€{total_beneficios:.2f}"],
        ['Beneficio Promedio', f"€{(total_beneficios/len(cultivos) if cultivos else 0):.2f} por cultivo"]
    ]
    
    resumen_table = Table(resumen_data, colWidths=[3*inch, 2*inch])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(resumen_table)
    story.append(Spacer(1, 20))
    
    # Detalle de cultivos
    if cultivos:
        story.append(Paragraph("🌱 Detalle de Cultivos", heading_style))
        
        # Tabla de cultivos
        cultivos_data = [['Cultivo', 'Fecha Siembra', 'Plantas', 'Precio/kg', 'Kilos', 'Beneficio', 'Estado']]
        
        for cultivo in cultivos:
            cultivos_data.append([
                cultivo['nombre'].title(),
                cultivo['fecha_siembra'].strftime('%d/%m/%Y'),
                str(cultivo.get('plantas_sembradas', 0)),
                f"€{cultivo.get('precio_por_kilo', 0):.2f}",
                f"{cultivo.get('kilos_totales', 0):.1f} kg",
                f"€{cultivo.get('beneficio_total', 0):.2f}",
                'Activo' if cultivo.get('activo', True) else 'Cosechado'
            ])
        
        cultivos_table = Table(cultivos_data, colWidths=[0.8*inch, 0.8*inch, 0.6*inch, 0.7*inch, 0.7*inch, 0.8*inch, 0.7*inch])
        cultivos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(cultivos_table)
        story.append(Spacer(1, 20))
        
        # Análisis de rentabilidad
        story.append(Paragraph("💹 Análisis de Rentabilidad", heading_style))
        
        if cultivos:
            cultivo_top = max(cultivos, key=lambda x: x.get('beneficio_total', 0))
            story.append(Paragraph(f"<b>🏆 Cultivo Más Rentable:</b> {cultivo_top['nombre'].title()}", styles['Normal']))
            story.append(Paragraph(f"Beneficio: €{cultivo_top.get('beneficio_total', 0):.2f}", styles['Normal']))
            story.append(Paragraph(f"Producción: {cultivo_top.get('kilos_totales', 0):.1f} kg", styles['Normal']))
            story.append(Spacer(1, 12))
            
            activos = len([c for c in cultivos if c.get('activo', True)])
            cosechados = len(cultivos) - activos
            story.append(Paragraph(f"<b>📊 Estadísticas:</b>", styles['Normal']))
            story.append(Paragraph(f"• Cultivos activos: {activos}", styles['Normal']))
            story.append(Paragraph(f"• Cultivos cosechados: {cosechados}", styles['Normal']))
            if total_kilos > 0:
                story.append(Paragraph(f"• Rentabilidad: €{(total_beneficios/total_kilos):.2f}/kg", styles['Normal']))
    else:
        story.append(Paragraph("No hay cultivos registrados", styles['Normal']))
    
    # Pie de página
    story.append(Spacer(1, 30))
    story.append(Paragraph("🌱 <b>HuertoRentable</b> - Gestión inteligente de huertos rentables", styles['Normal']))
    story.append(Paragraph(f"Reporte generado el {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    
    # Crear respuesta HTTP
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response
    
    return response
