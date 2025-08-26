# Instrucciones para Copilot - HuertoRentable

## Filosofía del Proyecto

HuertoRentable es una aplicación Flask PWA para gestión de huertos rentables con Firebase Firestore. Todo el código debe ser educativo, claro y funcional para personas en formación.

## Stack Tecnológico Obligatorio

- **Backend**: Flask con Firebase Admin SDK
- **Base de datos**: Firebase Firestore (NO SQLAlchemy)
- **Frontend**: Bootstrap 5 + Chart.js para gráficas
- **PWA**: Service Worker + Manifest.json
- **Autenticación**: Firebase Authentication

## Estructura de Proyecto EXACTA

```
HuertoRentable/
├── app.py                    # aplicación Flask principal
├── requirements.txt          # dependencias Python
├── manifest.json             # manifiesto PWA
├── service-worker.js         # service worker para offline
├── templates/                # plantillas HTML Jinja2
│   ├── base.html             # layout base con Bootstrap 5
│   ├── dashboard.html        # panel con resumen de cultivos y beneficios
│   ├── crops.html            # gestión de cultivos
│   ├── analytics.html        # gráficas comparativas por años
│   └── login.html            # inicio de sesión
└── static/
    ├── css/styles.css
    ├── js/app.js
    └── img/icon.png
```

## Estándares de Desarrollo Obligatorios

### Estructura y Organización

- **Estructura modular**: Aunque sea app.py plano, usar funciones y clases organizadas
- **Configuración por entornos**: Separar development/production con variables de entorno
- **Nombres en español**: Variables y funciones descriptivas en español cuando sea posible
- **Comentarios educativos**: Explicar el "por qué" del código, no solo el "qué"
- **Ejemplos funcionales**: Siempre código ejecutable, nunca pseudocódigo

### Frontend Consistente

- **Diseño simple y accesible**: Priorizar usabilidad y accesibilidad web
- **Estructura consistente**: Layout base coherente en todas las páginas
- **Bootstrap 5 sistemático**: Usar clases Bootstrap de forma consistente

## Rutas y Funcionalidades Requeridas

### Rutas Principales

- `"/"` → dashboard.html (resumen cultivos y beneficios totales)
- `"/login"` → login.html (autenticación Firebase)
- `"/crops"` → crops.html (CRUD cultivos)
- `"/analytics"` → analytics.html (gráficas Chart.js)

### Modelo de Datos Firestore

Cada cultivo debe almacenar:

- **nombre**: String (ej. "tomates")
- **fecha_siembra**: Timestamp
- **fecha_cosecha**: Timestamp
- **abonos**: Array [{fecha: Timestamp, descripcion: String}]
- **produccion_diaria**: Array [{fecha: Timestamp, kilos: Number}]
- **precio_por_kilo**: Number

### Dashboard Obligatorio

- Total kilos recogidos por cultivo
- Beneficio calculado (kilos × precio_por_kilo)
- Enlaces a analytics para gráficas comparativas

### Analytics con Chart.js

- Gráfica producción anual por cultivo
- Gráfica beneficios por año
- Comparativas entre diferentes años

## Configuración PWA Obligatoria

### Service Worker

- Cachear recursos estáticos (CSS, JS, imágenes)
- Página offline básica cuando no hay conexión
- Estrategia cache-first para assets estáticos

### Manifest.json

- Configuración completa con iconos
- Orientación y tema
- Capacidad de instalación

## Dependencias Permitidas

```python
# requirements.txt - ESTAS son las únicas permitidas
Flask==2.3.3
firebase-admin==6.2.0
python-dotenv==1.0.0
```

## Reglas de Desarrollo

### Dependencias Estrictas

- **SOLO usar las dependencias listadas**: Flask, firebase-admin, python-dotenv
- **NO añadir SQLAlchemy, Werkzeug adicional, etc.**
- **Preguntar antes de añadir**: Si falta algo, explicar opciones antes de proceder

### Calidad del Código Educativo

- **Código ejecutable**: Nunca pseudocódigo, siempre funcional
- **Buenas prácticas**: PEP 8 para Python, ES6+ para JavaScript
- **Datos de prueba realistas**: Cultivos con fechas y producciones creíbles
- **Comentarios educativos**: Explicar "por qué", no solo "qué"
- **Estructura modular**: Funciones y clases bien organizadas

### Comunicación y Estilo

- **Todo en español**: Documentación, comentarios, variables cuando sea posible
- **Explicaciones sencillas**: Para personas en formación
- **Diseño accesible**: Priorizar usabilidad en todas las interfaces
- **Confirmar antes de proceder**: Si algo no está claro, preguntar la mejor opción

## Ejemplos de Patrones Requeridos

### Conexión Firebase con Configuración por Entornos

```python
# app.py - Inicialización modular y por entornos
import os
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask

def crear_app():
    """Función factory para crear la aplicación Flask de forma modular"""
    app = Flask(__name__)

    # Configuración por entornos
    if os.environ.get('FLASK_ENV') == 'production':
        app.config['DEBUG'] = False
        # En producción usar variables de entorno para Firebase
        cred = credentials.Certificate({
            "type": os.environ.get('FIREBASE_TYPE'),
            "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
            # ... resto de configuración
        })
    else:
        app.config['DEBUG'] = True
        # En desarrollo usar archivo local
        cred = credentials.Certificate('serviceAccountKey.json')

    # Inicializar Firebase una sola vez
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    return app, firestore.client()

# Crear aplicación de forma modular
app, db = crear_app()
```

### Template Bootstrap 5 PWA

```html
<!-- base.html - Estructura obligatoria -->
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <!-- Bootstrap 5 CDN -->
    <link
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
      rel="stylesheet"
    />
    <!-- PWA manifest -->
    <link rel="manifest" href="/manifest.json" />
    <title>HuertoRentable</title>
  </head>
  <body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-success">
      <!-- Navegación Bootstrap -->
    </nav>
    <main class="container mt-4">{% block content %}{% endblock %}</main>
    <!-- Chart.js para analytics -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Service Worker -->
    <script>
      if ("serviceWorker" in navigator) {
        navigator.serviceWorker.register("/service-worker.js");
      }
    </script>
  </body>
</html>
```

### Operaciones Firestore con Comentarios Educativos

```python
# Ejemplo CRUD cultivos con estructura modular
@app.route('/crops', methods=['GET', 'POST'])
def gestionar_cultivos():
    """
    Gestiona el CRUD de cultivos de forma educativa
    GET: Lista todos los cultivos existentes
    POST: Añade un nuevo cultivo con validación
    """
    if request.method == 'POST':
        # Validar datos del formulario antes de guardar
        nombre_cultivo = request.form.get('nombre', '').strip()
        if not nombre_cultivo:
            flash('El nombre del cultivo es obligatorio', 'error')
            return redirect(url_for('gestionar_cultivos'))

        try:
            # Crear estructura de datos del cultivo
            datos_cultivo = {
                'nombre': nombre_cultivo.lower(),  # Nombres en minúsculas para consistencia
                'fecha_siembra': firestore.SERVER_TIMESTAMP,
                'fecha_cosecha': None,  # Se actualizará cuando termine el cultivo
                'precio_por_kilo': float(request.form.get('precio', 0)),
                'abonos': [],  # Lista de objetos {fecha, descripcion}
                'produccion_diaria': [],  # Lista de objetos {fecha, kilos}
                'activo': True  # Para soft delete
            }

            # Guardar en Firestore con manejo de errores
            doc_ref = db.collection('cultivos').add(datos_cultivo)
            flash(f'Cultivo "{nombre_cultivo}" añadido exitosamente', 'success')

        except Exception as error:
            # Manejo de errores educativo
            flash(f'Error al guardar cultivo: {str(error)}', 'error')
            print(f"Error Firebase: {error}")  # Para debugging

    # Obtener todos los cultivos activos ordenados por fecha
    try:
        cultivos_query = db.collection('cultivos')\
                          .where('activo', '==', True)\
                          .order_by('fecha_siembra', direction=firestore.Query.DESCENDING)
        cultivos = [doc.to_dict() for doc in cultivos_query.stream()]
    except Exception as error:
        cultivos = []
        flash(f'Error al cargar cultivos: {str(error)}', 'error')

    return render_template('crops.html', cultivos=cultivos)
```
