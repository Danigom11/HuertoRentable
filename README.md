# HuertoRentable 🌱

Una aplicación web progresiva (PWA) para la gestión inteligente y rentable de huertos, construida con Flask y Firebase Firestore.

## 🚀 Características Principales

- **📱 PWA Completa**: Funciona offline, instalable como app nativa
- **🔥 Firebase Firestore**: Base de datos en tiempo real
- **📊 Análisis Avanzados**: Gráficas con Chart.js para producción y beneficios
- **🎨 Bootstrap 5**: Diseño responsivo y accesible
- **🌐 Multiidioma**: Interfaz en español, código educativo
- **⚡ Tiempo Real**: Sincronización automática de datos

## 🛠️ Tecnologías Utilizadas

- **Backend**: Flask 2.3.3
- **Base de Datos**: Firebase Firestore
- **Frontend**: Bootstrap 5 + Chart.js
- **PWA**: Service Worker + Manifest.json
- **Autenticación**: Firebase Authentication (próximamente)

## 📁 Estructura del Proyecto

```
HuertoRentable/
├── app.py                    # Aplicación Flask principal
├── requirements.txt          # Dependencias Python
├── manifest.json             # Manifiesto PWA
├── service-worker.js         # Service worker para offline
├── .env.example             # Variables de entorno de ejemplo
├── templates/                # Plantillas HTML Jinja2
│   ├── base.html             # Layout base con Bootstrap 5
│   ├── dashboard.html        # Panel de resumen
│   ├── crops.html            # Gestión de cultivos
│   ├── analytics.html        # Gráficas comparativas
│   └── login.html            # Inicio de sesión
└── static/
    ├── css/styles.css        # Estilos personalizados
    ├── js/app.js             # JavaScript principal
    └── img/icon.png          # Icono de la PWA
```

## 🔧 Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Danigom11/HuertoRentable.git
cd HuertoRentable
```

### 2. Configurar Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Firebase

#### Opción A: Archivo JSON (Recomendado para desarrollo)

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Selecciona tu proyecto o crea uno nuevo
3. Ve a **Project Settings > Service Accounts**
4. Haz clic en **Generate new private key**
5. Descarga el archivo JSON y guárdalo como `serviceAccountKey.json` en la raíz del proyecto

#### Opción B: Variables de Entorno (Para producción)

1. Copia `.env.example` a `.env`
2. Completa las variables con los datos de tu proyecto Firebase

### 5. Crear Base de Datos Firestore

1. En Firebase Console, ve a **Firestore Database**
2. Haz clic en **Create database**
3. Selecciona **Start in test mode** (para desarrollo)
4. Elige la ubicación más cercana

### 6. Ejecutar la Aplicación

```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## 📊 Funcionalidades

### Dashboard

- Resumen de todos los cultivos activos
- Estadísticas de producción total y beneficios
- Tarjetas informativas con métricas clave
- Enlaces rápidos a otras secciones

### Gestión de Cultivos

- Añadir nuevos cultivos con nombre y precio por kilo
- Registrar producción diaria
- Historial de abonos y tratamientos
- Vista responsiva para móviles y escritorio

### Analytics

- Gráficas de producción anual
- Análisis de beneficios por año
- Comparativa entre diferentes cultivos
- Exportación de datos a CSV

### PWA Features

- **Instalación**: Se puede instalar como app nativa
- **Offline**: Funciona sin conexión a internet
- **Caché inteligente**: Recursos estáticos cacheados
- **Actualizaciones**: Service worker para actualizaciones automáticas

## 🎯 Rutas de la API

- `GET /` - Dashboard principal
- `GET /login` - Página de inicio de sesión
- `GET|POST /crops` - Gestión de cultivos
- `GET /analytics` - Página de análisis
- `POST /api/agregar-produccion` - API para añadir producción

## 🔒 Seguridad

- Variables de entorno para credenciales
- Validación de datos en formularios
- Autenticación (próximamente con Firebase Auth)
- HTTPS en producción (recomendado)

## 🚀 Despliegue

### Desarrollo Local

```bash
python app.py
```

### Producción

1. Configura las variables de entorno en tu servidor
2. Usa un servidor WSGI como Gunicorn:

```bash
pip install gunicorn
gunicorn app:app
```

### Heroku (Ejemplo)

1. Crea `Procfile`:

```
web: gunicorn app:app
```

2. Configura las variables de entorno en Heroku
3. Despliega con Git

## 📝 Datos de Ejemplo

La aplicación incluye datos de ejemplo que se crean automáticamente en el primer arranque:

- **Tomates**: Cultivo con producción diaria y abonos
- **Lechugas**: Segundo cultivo con datos de ejemplo
- **Precios realistas**: €2.80 - €3.50 por kilo
- **Fechas reales**: Basadas en fechas de siembra típicas

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Resolución de Problemas

### Error de Firebase

- Verifica que `serviceAccountKey.json` esté en la raíz del proyecto
- Comprueba que las reglas de Firestore permitan lectura/escritura
- Asegúrate de que el proyecto Firebase esté activo

### Error de PWA

- Verifica que `manifest.json` sea accesible
- Comprueba que el Service Worker se registre correctamente
- Usa HTTPS para funcionalidades PWA completas

### Error de Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/Danigom11/HuertoRentable/issues)
- **Documentación**: Este README y comentarios en el código
- **Firebase Docs**: [Firebase Documentation](https://firebase.google.com/docs)

---

**HuertoRentable** - Hecho con ❤️ para la gestión inteligente de cultivos
