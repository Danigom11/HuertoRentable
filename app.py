"""
HuertoRentable - Aplicación Flask PWA para gestión de huertos rentables
Usa Firebase Firestore como base de datos y Bootstrap 5 para el frontend
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Cargar variables de entorno
load_dotenv()

# Configuración de Firebase
import firebase_admin
from firebase_admin import credentials, firestore

def crear_app():
    """
    Función factory para crear la aplicación Flask de forma modular
    Permite configuración diferente para development y production
    """
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-cambiar-en-produccion')
    
    # Configuración por entornos - buena práctica para educación
    if os.environ.get('FLASK_ENV') == 'production':
        app.config['DEBUG'] = False
        print("🚀 Ejecutándose en modo PRODUCCIÓN")
        # En producción usar variables de entorno para Firebase
        cred_dict = {
            "type": os.environ.get('FIREBASE_TYPE'),
            "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
            "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": os.environ.get('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
            "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        cred = credentials.Certificate(cred_dict)
    else:
        app.config['DEBUG'] = True
        print("🔧 Ejecutándose en modo DESARROLLO")
        # En desarrollo usar archivo local
        try:
            cred = credentials.Certificate('serviceAccountKey.json')
            print("✅ Credenciales Firebase cargadas desde serviceAccountKey.json")
        except FileNotFoundError:
            print("⚠️  IMPORTANTE: Falta el archivo 'serviceAccountKey.json'")
            print("   Descárgalo desde Firebase Console > Project Settings > Service Accounts")
            print("   Ejecutándose en MODO DEMO mientras tanto...")
            return app, None
    
    # Inicializar Firebase una sola vez - previene errores de duplicación
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        print("✅ Firebase inicializado correctamente")
    
    return app, firestore.client()

# Crear aplicación y cliente de base de datos
app, db = crear_app()

# Si no se pudo conectar a Firebase, mostrar error educativo
if db is None:
    print("❌ No se pudo conectar a Firebase Firestore")
    print("   Revisa la configuración de credenciales")

# =====================================
# FUNCIONES AUXILIARES Y UTILITARIOS
# =====================================

def obtener_datos_demo():
    """
    Datos de ejemplo para mostrar cuando Firebase no está disponible
    Permite probar la aplicación sin configurar la base de datos
    """
    from datetime import datetime, timedelta
    
    ahora = datetime.now()
    
    cultivos_demo = [
        {
            'id': 'demo_1',
            'nombre': 'tomates',
            'fecha_siembra': ahora - timedelta(days=90),
            'fecha_siembra_legible': (ahora - timedelta(days=90)).strftime('%d/%m/%Y'),
            'dias_desde_siembra': 90,
            'fecha_cosecha': None,
            'precio_por_kilo': 3.5,
            'plantas_sembradas': 12,
            'unidades_recolectadas': 95,
            'kilos_totales': 45.2,
            'beneficio_total': 158.2,
            'activo': True,
            'produccion_diaria': [
                {'fecha': ahora - timedelta(days=5), 'kilos': 2.5},
                {'fecha': ahora - timedelta(days=3), 'kilos': 3.1},
                {'fecha': ahora - timedelta(days=1), 'kilos': 2.8}
            ],
            'abonos': [
                {'fecha': ahora - timedelta(days=30), 'descripcion': 'Humus de lombriz'},
                {'fecha': ahora - timedelta(days=15), 'descripcion': 'Compost orgánico'}
            ]
        },
        {
            'id': 'demo_2',
            'nombre': 'lechugas',
            'fecha_siembra': ahora - timedelta(days=60),
            'fecha_siembra_legible': (ahora - timedelta(days=60)).strftime('%d/%m/%Y'),
            'dias_desde_siembra': 60,
            'fecha_cosecha': None,
            'precio_por_kilo': 2.8,
            'plantas_sembradas': 24,
            'unidades_recolectadas': 48,
            'kilos_totales': 28.7,
            'beneficio_total': 80.36,
            'activo': True,
            'produccion_diaria': [
                {'fecha': ahora - timedelta(days=4), 'kilos': 1.5},
                {'fecha': ahora - timedelta(days=2), 'kilos': 2.2},
            ],
            'abonos': [
                {'fecha': ahora - timedelta(days=25), 'descripcion': 'Fertilizante líquido'}
            ]
        },
        {
            'id': 'demo_3',
            'nombre': 'zanahorias',
            'fecha_siembra': ahora - timedelta(days=120),
            'fecha_siembra_legible': (ahora - timedelta(days=120)).strftime('%d/%m/%Y'),
            'dias_desde_siembra': 120,
            'fecha_cosecha': ahora - timedelta(days=10),
            'precio_por_kilo': 1.9,
            'plantas_sembradas': 50,
            'unidades_recolectadas': 127,
            'kilos_totales': 52.3,
            'beneficio_total': 99.37,
            'activo': False,
            'produccion_diaria': [
                {'fecha': ahora - timedelta(days=15), 'kilos': 8.5},
                {'fecha': ahora - timedelta(days=12), 'kilos': 12.3},
                {'fecha': ahora - timedelta(days=10), 'kilos': 9.8}
            ],
            'abonos': [
                {'fecha': ahora - timedelta(days=80), 'descripcion': 'Estiércol compostado'}
            ]
        }
    ]
    
    # Calcular estadísticas de los cultivos activos
    cultivos_activos = [c for c in cultivos_demo if c['activo']]
    
    # Asegurar que todos los cultivos tengan los campos necesarios
    for cultivo in cultivos_activos:
        if 'kilos_totales' not in cultivo:
            cultivo['kilos_totales'] = sum(p.get('kilos', 0) for p in cultivo.get('produccion_diaria', []))
        if 'beneficio_total' not in cultivo:
            cultivo['beneficio_total'] = cultivo['kilos_totales'] * cultivo.get('precio_por_kilo', 0)
    
    estadisticas = {
        'total_cultivos': len(cultivos_activos),
        'kilos_totales': sum(c.get('kilos_totales', 0) for c in cultivos_activos),
        'beneficio_total': sum(c.get('beneficio_total', 0) for c in cultivos_activos),
        'promedio_beneficio': sum(c.get('beneficio_total', 0) for c in cultivos_activos) / len(cultivos_activos) if cultivos_activos else 0
    }
    
    return {
        'cultivos': cultivos_activos,
        'estadisticas': estadisticas
    }

def generar_datos_chart_demo(cultivos_demo):
    """
    Genera datos de ejemplo para las gráficas Chart.js en modo demo
    Procesa los cultivos demo para crear estadísticas realistas
    """
    from datetime import datetime
    
    datos_por_ano = {}
    beneficios_por_ano = {}
    produccion_por_cultivo = {}
    
    # Procesar cultivos demo (incluir activos e inactivos para histórico)
    todos_cultivos = cultivos_demo + [
        {
            'nombre': 'pimientos',
            'precio_por_kilo': 4.2,
            'produccion_diaria': [
                {'fecha': datetime(2024, 8, 15), 'kilos': 3.5},
                {'fecha': datetime(2024, 9, 20), 'kilos': 4.2}
            ]
        },
        {
            'nombre': 'calabacines',
            'precio_por_kilo': 2.1,
            'produccion_diaria': [
                {'fecha': datetime(2023, 7, 10), 'kilos': 5.8},
                {'fecha': datetime(2023, 8, 25), 'kilos': 6.2}
            ]
        }
    ]
    
    for cultivo in todos_cultivos:
        nombre = cultivo.get('nombre', 'Sin nombre')
        
        for produccion in cultivo.get('produccion_diaria', []):
            fecha = produccion.get('fecha')
            kilos = produccion.get('kilos', 0)
            
            if fecha:
                ano = fecha.year
                
                # Agrupar por año
                if ano not in datos_por_ano:
                    datos_por_ano[ano] = 0
                    beneficios_por_ano[ano] = 0
                
                datos_por_ano[ano] += kilos
                beneficios_por_ano[ano] += kilos * cultivo.get('precio_por_kilo', 0)
                
                # Agrupar por cultivo
                if nombre not in produccion_por_cultivo:
                    produccion_por_cultivo[nombre] = 0
                produccion_por_cultivo[nombre] += kilos
    
    return {
        'anos': list(datos_por_ano.keys()),
        'produccion_anual': list(datos_por_ano.values()),
        'beneficios_anuales': list(beneficios_por_ano.values()),
        'cultivos': list(produccion_por_cultivo.keys()),
        'produccion_por_cultivo': list(produccion_por_cultivo.values())
    }

# =====================================
# FUNCIONES FIREBASE FIRESTORE
# =====================================

def obtener_cultivos_firebase():
    """
    Obtiene todos los cultivos activos desde Firebase Firestore
    Incluye cálculos de estadísticas y validación de datos
    """
    if db is None:
        return None
    
    try:
        # Obtener cultivos activos (temporalmente sin order_by hasta que el índice esté listo)
        cultivos_ref = db.collection('cultivos')\
                        .where('activo', '==', True)
        
        cultivos_docs = cultivos_ref.stream()
        cultivos_lista = []
        
        for doc in cultivos_docs:
            cultivo = doc.to_dict()
            cultivo['id'] = doc.id
            
            # Calcular estadísticas del cultivo
            produccion_diaria = cultivo.get('produccion_diaria', [])
            kilos_totales = sum(prod.get('kilos', 0) for prod in produccion_diaria)
            precio_por_kilo = cultivo.get('precio_por_kilo', 0)
            beneficio_total = kilos_totales * precio_por_kilo
            
            # Añadir campos calculados
            cultivo['kilos_totales'] = round(kilos_totales, 2)
            cultivo['beneficio_total'] = round(beneficio_total, 2)
            cultivo['unidades_recolectadas'] = len(produccion_diaria)
            
            # Formatear fecha de siembra si existe
            if 'fecha_siembra' in cultivo:
                fecha_siembra = cultivo['fecha_siembra']
                if hasattr(fecha_siembra, 'strftime'):
                    cultivo['fecha_siembra_legible'] = fecha_siembra.strftime('%d/%m/%Y')
                    # Por ahora no calcular días hasta resolver timezone
                    cultivo['dias_desde_siembra'] = 0
            
            cultivos_lista.append(cultivo)
        
        # Por ahora sin ordenamiento hasta resolver timezone
        # cultivos_lista.sort(key=lambda c: c.get('fecha_siembra', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
            
        return cultivos_lista
        
    except Exception as e:
        print(f"❌ Error al obtener cultivos desde Firebase: {e}")
        return None

def crear_cultivo_firebase(datos_cultivo):
    """
    Crea un nuevo cultivo en Firebase Firestore
    Valida los datos antes de guardar
    """
    if db is None:
        return False, "Base de datos no disponible"
    
    try:
        # Validar datos obligatorios
        if not datos_cultivo.get('nombre'):
            return False, "El nombre del cultivo es obligatorio"
        
        # Preparar estructura del cultivo
        cultivo_nuevo = {
            'nombre': datos_cultivo['nombre'].lower().strip(),
            'fecha_siembra': firestore.SERVER_TIMESTAMP,
            'fecha_cosecha': None,
            'precio_por_kilo': float(datos_cultivo.get('precio_por_kilo', 0)),
            'plantas_sembradas': int(datos_cultivo.get('plantas_sembradas', 0)),
            'abonos': [],
            'produccion_diaria': [],
            'activo': True,
            'fecha_creacion': firestore.SERVER_TIMESTAMP
        }
        
        # Guardar en Firestore
        doc_ref = db.collection('cultivos').add(cultivo_nuevo)
        print(f"✅ Cultivo '{datos_cultivo['nombre']}' creado con ID: {doc_ref[1].id}")
        return True, "Cultivo creado exitosamente"
        
    except Exception as e:
        print(f"❌ Error al crear cultivo: {e}")
        return False, f"Error al crear cultivo: {str(e)}"

def actualizar_produccion_firebase(cultivo_id, kilos):
    """
    Añade una nueva entrada de producción diaria a un cultivo
    """
    if db is None:
        return False, "Base de datos no disponible"
    
    try:
        # Referencia al documento del cultivo
        cultivo_ref = db.collection('cultivos').document(cultivo_id)
        
        # Nueva entrada de producción
        nueva_produccion = {
            'fecha': firestore.SERVER_TIMESTAMP,
            'kilos': float(kilos)
        }
        
        # Actualizar usando arrayUnion para añadir al array
        cultivo_ref.update({
            'produccion_diaria': firestore.ArrayUnion([nueva_produccion])
        })
        
        print(f"✅ Producción actualizada: {kilos}kg añadidos al cultivo {cultivo_id}")
        return True, "Producción registrada exitosamente"
        
    except Exception as e:
        print(f"❌ Error al actualizar producción: {e}")
        return False, f"Error al registrar producción: {str(e)}"

def obtener_datos_analytics_firebase():
    """
    Obtiene datos para gráficas desde Firebase
    Procesa la información para Chart.js
    """
    if db is None:
        return None
    
    try:
        # Obtener todos los cultivos (activos e inactivos para histórico)
        cultivos_ref = db.collection('cultivos')
        cultivos_docs = cultivos_ref.stream()
        
        datos_por_ano = {}
        beneficios_por_ano = {}
        produccion_por_cultivo = {}
        
        for doc in cultivos_docs:
            cultivo = doc.to_dict()
            nombre = cultivo.get('nombre', 'sin_nombre')
            precio_por_kilo = cultivo.get('precio_por_kilo', 0)
            
            # Procesar producción diaria
            for produccion in cultivo.get('produccion_diaria', []):
                fecha = produccion.get('fecha')
                kilos = produccion.get('kilos', 0)
                
                if fecha and hasattr(fecha, 'year'):
                    ano = fecha.year
                    
                    # Agrupar por año
                    if ano not in datos_por_ano:
                        datos_por_ano[ano] = 0
                        beneficios_por_ano[ano] = 0
                    
                    datos_por_ano[ano] += kilos
                    beneficios_por_ano[ano] += kilos * precio_por_kilo
                    
                    # Agrupar por cultivo
                    if nombre not in produccion_por_cultivo:
                        produccion_por_cultivo[nombre] = 0
                    produccion_por_cultivo[nombre] += kilos
        
        return {
            'anos': sorted(datos_por_ano.keys()),
            'produccion_anual': [datos_por_ano[ano] for ano in sorted(datos_por_ano.keys())],
            'beneficios_anuales': [beneficios_por_ano[ano] for ano in sorted(beneficios_por_ano.keys())],
            'cultivos': list(produccion_por_cultivo.keys()),
            'produccion_por_cultivo': list(produccion_por_cultivo.values())
        }
        
    except Exception as e:
        print(f"❌ Error al obtener datos de analytics: {e}")
        return None

# =====================================
# RUTAS PRINCIPALES DE LA APLICACIÓN
# =====================================

@app.route('/')
def dashboard():
    """
    Dashboard principal - muestra resumen de cultivos y beneficios
    Esta es la página principal donde el usuario ve el estado general
    """
    try:
        # Verificar si Firebase está disponible
        if db is None:
            print("⚠️  Modo DEMO activo - Firebase no disponible")
            # Modo demo: mostrar datos de ejemplo sin Firebase
            datos_demo = obtener_datos_demo()
            
            # Verificar que los datos demo sean válidos
            if not datos_demo or 'estadisticas' not in datos_demo:
                # Crear datos demo básicos si fallan
                datos_demo = {
                    'cultivos': [],
                    'estadisticas': {
                        'total_cultivos': 0,
                        'kilos_totales': 0.0,
                        'beneficio_total': 0.0,
                        'promedio_beneficio': 0.0
                    }
                }
                
            return render_template('dashboard.html', 
                                 cultivos=datos_demo.get('cultivos', []), 
                                 estadisticas=datos_demo.get('estadisticas', {}),
                                 modo_demo=True)
        
        # MODO FIREBASE: Obtener datos reales desde Firestore
        print("🔥 Obteniendo datos desde Firebase Firestore...")
        cultivos_firebase = obtener_cultivos_firebase()
        
        if cultivos_firebase is None:
            # Si falla Firebase, usar modo demo como fallback
            print("⚠️  Firebase falló, usando datos demo como respaldo")
            datos_demo = obtener_datos_demo()
            return render_template('dashboard.html', 
                                 cultivos=datos_demo.get('cultivos', []), 
                                 estadisticas=datos_demo.get('estadisticas', {}),
                                 modo_demo=True)
        
        # Calcular estadísticas de los cultivos de Firebase
        kilos_totales = sum(c.get('kilos_totales', 0) for c in cultivos_firebase)
        beneficio_total = sum(c.get('beneficio_total', 0) for c in cultivos_firebase)
        total_cultivos = len(cultivos_firebase)
        promedio_beneficio = beneficio_total / total_cultivos if total_cultivos > 0 else 0
        
        estadisticas = {
            'total_cultivos': total_cultivos,
            'kilos_totales': round(kilos_totales, 2),
            'beneficio_total': round(beneficio_total, 2),
            'promedio_beneficio': round(promedio_beneficio, 2)
        }
        
        print(f"✅ Dashboard cargado: {total_cultivos} cultivos, {kilos_totales}kg, €{beneficio_total}")
        return render_template('dashboard.html', 
                             cultivos=cultivos_firebase, 
                             estadisticas=estadisticas,
                             modo_demo=False)
        
        
    except Exception as error:
        print(f"❌ Error en dashboard: {error}")
        flash(f'Error al cargar el dashboard: {str(error)}', 'error')
        # En caso de error, mostrar datos demo como fallback
        datos_demo = obtener_datos_demo()
        return render_template('dashboard.html', 
                             cultivos=datos_demo['cultivos'], 
                             estadisticas=datos_demo['estadisticas'],
                             modo_demo=True)

@app.route('/login')
def login():
    """
    Página de inicio de sesión con Firebase Authentication
    En este ejemplo usamos plantilla simple, en producción integrar Firebase Auth
    """
    return render_template('login.html')

@app.route('/crops', methods=['GET', 'POST'])
def gestionar_cultivos():
    """
    Gestiona el CRUD de cultivos de forma educativa
    GET: Lista todos los cultivos existentes
    POST: Añade un nuevo cultivo con validación completa
    """
    # Verificar si Firebase está disponible
    if db is None:
        if request.method == 'POST':
            flash('⚠️ Funcionalidad no disponible en modo demo. Configura Firebase para guardar datos.', 'warning')
        
        # Mostrar datos demo (incluir todos los cultivos para ver histórico)
        datos_demo = obtener_datos_demo()
        # Incluir también los cultivos inactivos para mostrar histórico
        todos_cultivos_demo = datos_demo['cultivos'] + [
            {
                'id': 'demo_3',
                'nombre': 'zanahorias',
                'fecha_siembra': datetime.now() - timedelta(days=120),
                'fecha_siembra_legible': (datetime.now() - timedelta(days=120)).strftime('%d/%m/%Y'),
                'dias_desde_siembra': 120,
                'fecha_cosecha': datetime.now() - timedelta(days=10),
                'precio_por_kilo': 1.9,
                'numero_plantas': 50,
                'kilos_totales': 52.3,
                'beneficio_total': 99.37,
                'activo': False,
            }
        ]
        return render_template('crops.html', cultivos=todos_cultivos_demo, modo_demo=True)
    
    # MODO FIREBASE
    if request.method == 'POST':
        print("🌱 Creando nuevo cultivo...")
        
        # Validar datos del formulario antes de guardar
        nombre_cultivo = request.form.get('nombre', '').strip()
        precio_str = request.form.get('precio', '0')
        numero_plantas_str = request.form.get('numero_plantas', '1')
        
        if not nombre_cultivo:
            flash('❌ El nombre del cultivo es obligatorio', 'error')
            return redirect(url_for('gestionar_cultivos'))
        
        try:
            precio = float(precio_str)
            if precio < 0:
                flash('❌ El precio no puede ser negativo', 'error')
                return redirect(url_for('gestionar_cultivos'))
        except ValueError:
            flash('❌ El precio debe ser un número válido', 'error')
            return redirect(url_for('gestionar_cultivos'))
            
        try:
            numero_plantas = int(numero_plantas_str)
            if numero_plantas < 1:
                flash('❌ El número de plantas debe ser al menos 1', 'error')
                return redirect(url_for('gestionar_cultivos'))
        except ValueError:
            flash('❌ El número de plantas debe ser un número entero', 'error')
            return redirect(url_for('gestionar_cultivos'))
        
        # Crear cultivo usando la función de Firebase
        datos_cultivo = {
            'nombre': nombre_cultivo,
            'precio_por_kilo': precio,
            'plantas_sembradas': numero_plantas
        }
        
        exito, mensaje = crear_cultivo_firebase(datos_cultivo)
        if exito:
            flash(f'✅ {mensaje}', 'success')
        else:
            flash(f'❌ {mensaje}', 'error')
        
        return redirect(url_for('gestionar_cultivos'))
    
    # GET request: Mostrar lista de cultivos
    print("📋 Obteniendo lista de cultivos desde Firebase...")
    cultivos_firebase = obtener_cultivos_firebase()
    
    if cultivos_firebase is None:
        flash('⚠️ Error al conectar con la base de datos', 'warning')
        # Fallback a datos demo
        datos_demo = obtener_datos_demo()
        return render_template('crops.html', cultivos=datos_demo['cultivos'], modo_demo=True)
    
    return render_template('crops.html', cultivos=cultivos_firebase, modo_demo=False)

@app.route('/analytics')
def analytics():
    """
    Página de análisis con gráficas Chart.js
    Muestra estadísticas de producción y beneficios por año
    """
    try:
        # Verificar si Firebase está disponible
        if db is None:
            # Modo demo: generar datos de ejemplo para las gráficas
            datos_demo = obtener_datos_demo()
            chart_data = generar_datos_chart_demo(datos_demo['cultivos'])
            return render_template('analytics.html', 
                                 chart_data=json.dumps(chart_data),
                                 modo_demo=True)
        
        # Obtener datos para gráficas - agrupados por año
        cultivos_ref = db.collection('cultivos').where('activo', '==', True)
        cultivos_docs = cultivos_ref.stream()
        
        # Estructuras para datos de gráficas
        datos_por_ano = {}
        beneficios_por_ano = {}
        produccion_por_cultivo = {}
        
        for doc in cultivos_docs:
            cultivo = doc.to_dict()
            nombre = cultivo.get('nombre', 'Sin nombre')
            
            # Procesar producción diaria para estadísticas
            for produccion in cultivo.get('produccion_diaria', []):
                fecha = produccion.get('fecha')
                kilos = produccion.get('kilos', 0)
                
                if fecha:
                    ano = fecha.year
                    
                    # Agrupar por año
                    if ano not in datos_por_ano:
                        datos_por_ano[ano] = 0
                        beneficios_por_ano[ano] = 0
                    
                    datos_por_ano[ano] += kilos
                    beneficios_por_ano[ano] += kilos * cultivo.get('precio_por_kilo', 0)
                    
                    # Agrupar por cultivo
                    if nombre not in produccion_por_cultivo:
                        produccion_por_cultivo[nombre] = 0
                    produccion_por_cultivo[nombre] += kilos
        
        # Preparar datos para Chart.js - formato JSON
        chart_data = {
            'anos': list(datos_por_ano.keys()),
            'produccion_anual': list(datos_por_ano.values()),
            'beneficios_anuales': list(beneficios_por_ano.values()),
            'cultivos': list(produccion_por_cultivo.keys()),
            'produccion_por_cultivo': list(produccion_por_cultivo.values())
        }
        
        return render_template('analytics.html', 
                             chart_data=json.dumps(chart_data),
                             modo_demo=False)
        
    except Exception as error:
        print(f"Error en analytics: {error}")
        flash(f'❌ Error al cargar análisis: {str(error)}', 'error')
        # En caso de error, mostrar datos demo
        datos_demo = obtener_datos_demo()
        chart_data = generar_datos_chart_demo(datos_demo['cultivos'])
        return render_template('analytics.html', 
                             chart_data=json.dumps(chart_data),
                             modo_demo=True)

# =====================================
# RUTAS API PARA FUNCIONES AVANZADAS
# =====================================

@app.route('/api/agregar-produccion', methods=['POST'])
def agregar_produccion():
    """
    API para añadir producción diaria a un cultivo
    Permite AJAX desde el frontend para mejor experiencia
    """
    try:
        data = request.get_json()
        cultivo_id = data.get('cultivo_id')
        kilos = float(data.get('kilos', 0))
        fecha_str = data.get('fecha')
        
        # Validaciones
        if not cultivo_id or kilos <= 0:
            return jsonify({'error': 'Datos inválidos'}), 400
        
        # Convertir fecha string a timestamp
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        
        # Actualizar cultivo en Firestore - usar arrayUnion para eficiencia
        cultivo_ref = db.collection('cultivos').document(cultivo_id)
        cultivo_ref.update({
            'produccion_diaria': firestore.ArrayUnion([{
                'fecha': fecha,
                'kilos': kilos
            }])
        })
        
        return jsonify({'success': 'Producción añadida correctamente'})
        
    except Exception as error:
        print(f"Error API producción: {error}")
        return jsonify({'error': str(error)}), 500

# =====================================
# FUNCIÓN PARA CREAR DATOS DE EJEMPLO
# =====================================

def crear_datos_ejemplo():
    """
    Crea datos de ejemplo para probar la aplicación
    Solo se ejecuta si Firebase está disponible
    """
    if not db:
        print("ℹ️  Modo demo activado - usando datos de ejemplo locales")
        return
    
    try:
        # Verificar si ya existen cultivos
        existing = list(db.collection('cultivos').limit(1).stream())
        if existing:
            print("✅ Ya existen datos en Firebase")
            return
        
        # Datos de ejemplo realistas
        cultivos_ejemplo = [
            {
                'nombre': 'tomates',
                'precio_por_kilo': 3.50,
                'fecha_siembra': datetime.now() - timedelta(days=90),
                'activo': True,
                'produccion_diaria': [
                    {'fecha': datetime.now() - timedelta(days=10), 'kilos': 5.2},
                    {'fecha': datetime.now() - timedelta(days=8), 'kilos': 7.1},
                    {'fecha': datetime.now() - timedelta(days=5), 'kilos': 6.8},
                ],
                'abonos': [
                    {'fecha': datetime.now() - timedelta(days=60), 'descripcion': 'Compost orgánico'},
                    {'fecha': datetime.now() - timedelta(days=30), 'descripcion': 'Fertilizante líquido'}
                ]
            },
            {
                'nombre': 'lechugas',
                'precio_por_kilo': 2.80,
                'fecha_siembra': datetime.now() - timedelta(days=45),
                'activo': True,
                'produccion_diaria': [
                    {'fecha': datetime.now() - timedelta(days=7), 'kilos': 3.5},
                    {'fecha': datetime.now() - timedelta(days=3), 'kilos': 4.2},
                ],
                'abonos': [
                    {'fecha': datetime.now() - timedelta(days=20), 'descripcion': 'Humus de lombriz'}
                ]
            }
        ]
        
        # Insertar datos de ejemplo
        for cultivo in cultivos_ejemplo:
            db.collection('cultivos').add(cultivo)
        
        print("✅ Datos de ejemplo creados correctamente")
        
    except Exception as error:
        print(f"Error creando datos de ejemplo: {error}")

# =====================================
# RUTAS PARA GESTIÓN DE RECOLECCIÓN
# =====================================

@app.route('/cultivo/<cultivo_id>/recolectar', methods=['POST'])
def añadir_recoleccion(cultivo_id):
    """
    Añade kilos recolectados a un cultivo específico
    Actualiza automáticamente las estadísticas del cultivo
    """
    try:
        # Verificar modo demo
        if db is None:
            return jsonify({
                'success': False, 
                'error': 'Funcionalidad no disponible en modo demo'
            }), 400
        
        # Obtener datos del formulario
        kilos = request.form.get('kilos', type=float)
        
        if not kilos or kilos <= 0:
            return jsonify({
                'success': False, 
                'error': 'Debe especificar un peso válido en kilos'
            }), 400
        
        # Usar la función de Firebase para actualizar producción
        exito, mensaje = actualizar_produccion_firebase(cultivo_id, kilos)
        
        if exito:
            return jsonify({
                'success': True,
                'message': mensaje,
                'kilos_añadidos': kilos
            })
        else:
            return jsonify({
                'success': False,
                'error': mensaje
            }), 400
        
    except Exception as error:
        print(f"❌ Error en recolección: {error}")
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(error)}'
        }), 500

@app.route('/demo/cultivo/<cultivo_id>/recolectar', methods=['POST'])
def añadir_recoleccion_demo(cultivo_id):
    """
    Versión demo de añadir recolección (solo simula la operación)
    """
    try:
        kilos = request.form.get('kilos', type=float)
        
        if not kilos or kilos <= 0:
            return jsonify({
                'success': False, 
                'error': 'Debe especificar un peso válido en kilos'
            }), 400
        
        # En modo demo, simular actualización exitosa
        return jsonify({
            'success': True,
            'message': f'✅ (DEMO) Se registraron {kilos}kg',
            'kilos_añadidos': kilos
        })
        
    except Exception as error:
        return jsonify({
            'success': False, 
            'error': str(error)
        }), 500
        return jsonify({
            'success': True,
            'nuevas_unidades': unidades,  # Simular nuevas unidades
            'message': f'DEMO: Se simula añadir {unidades} unidades',
            'modo_demo': True
        })
        
    except Exception as error:
        return jsonify({
            'success': False, 
            'error': str(error)
        }), 500

# =====================================
# EJECUCIÓN DE LA APLICACIÓN
# =====================================

if __name__ == '__main__':
    print("🌱 Iniciando HuertoRentable...")
    
    # Crear datos de ejemplo en desarrollo
    if app.config.get('DEBUG'):
        crear_datos_ejemplo()
    
    # Ejecutar aplicación en puerto 5001 para evitar conflictos
    port = int(os.environ.get('PORT', 5001))
    print(f"🔗 Aplicación disponible en: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))
