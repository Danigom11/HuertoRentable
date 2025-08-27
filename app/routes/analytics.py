"""
Rutas de analytics y reportes
Gráficas y estadísticas avanzadas
"""
import datetime
import json
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
