# 🚀 Guía de Deploy Web - HuertoRentable

## Resumen del Deploy

Tu aplicación HuertoRentable está lista para desplegarse en Firebase Hosting como una PWA completa. Aquí tienes las opciones disponibles:

## 🎯 Opciones de Deploy

### Opción 1: Script Automático (Recomendado)

```bash
# Ejecutar deploy automático
python deploy_completo.py

# O usar el script de Windows
deploy_web.bat
```

### Opción 2: Deploy Manual Paso a Paso

#### 1. Preparar archivos

```bash
python build.py
```

#### 2. Instalar dependencias

```bash
cd functions
npm install
cd ..
```

#### 3. Login en Firebase (solo primera vez)

```bash
firebase login
```

#### 4. Deploy por partes

```bash
# Solo hosting (más rápido)
firebase deploy --only hosting

# Solo funciones
firebase deploy --only functions

# Deploy completo
firebase deploy
```

## 📦 Estructura del Deploy

### Firebase Hosting

- **Carpeta**: `dist/` (generada por `build.py`)
- **Contenido**: Archivos estáticos, PWA assets, templates
- **URL**: `https://huerto-rentable.web.app`

### Cloud Functions

- **Carpeta**: `functions/`
- **Función principal**: `flaskApp` (maneja todas las rutas web)
- **Funciones API**: `crops`, `analytics`, `auth` (para Android)

### Firestore Database

- **Reglas**: `firestore.rules`
- **Índices**: `firestore.indexes.json`

## 🔧 Configuración Actual

### firebase.json

```json
{
  "hosting": {
    "public": "dist",
    "rewrites": [
      {
        "source": "**",
        "function": "flaskApp"
      }
    ]
  },
  "functions": {
    "source": "functions",
    "runtime": "nodejs20"
  }
}
```

### Rutas Disponibles

- `/` → Dashboard principal
- `/login` → Autenticación Firebase
- `/crops` → Gestión de cultivos
- `/analytics` → Gráficas y análisis
- `/static/**` → Archivos estáticos (CSS, JS, imágenes)

## 🌐 URLs de Producción

Una vez desplegado, tu aplicación estará disponible en:

- **Principal**: `https://huerto-rentable.web.app`
- **Alternativa**: `https://huerto-rentable.firebaseapp.com`
- **API Cloud Functions**: `https://us-central1-huerto-rentable.cloudfunctions.net/`

## 📱 Características PWA

### Service Worker

- Cache offline de recursos estáticos
- Funcionalidad básica sin conexión
- Actualización automática de la app

### Manifest.json

- Instalable como app nativa
- Iconos personalizados
- Pantalla completa en móviles

### Bootstrap 5 + Chart.js

- Interfaz responsive
- Gráficas interactivas
- Experiencia móvil optimizada

## 🔒 Autenticación

### Firebase Authentication

- Google Sign-In
- Email/Password
- Verificación automática de tokens
- Sesiones persistentes

### Firestore Security

- Reglas por usuario (solo ven sus datos)
- Validación de tipos de datos
- Rate limiting básico

## 🚀 Deploy de Producción

### Primer Deploy

1. Ejecutar: `python build.py`
2. Ejecutar: `deploy_web.bat` (Windows) o `python deploy_completo.py`
3. Seleccionar "Solo Hosting" para probar
4. Verificar en: `https://huerto-rentable.web.app`

### Actualizaciones

```bash
# Build + Deploy rápido
python build.py && firebase deploy --only hosting

# Con funciones actualizadas
python build.py && firebase deploy
```

## 📊 Monitoreo Post-Deploy

### Firebase Console

- **Hosting**: Métricas de tráfico y rendimiento
- **Functions**: Logs y uso de recursos
- **Firestore**: Uso de base de datos
- **Authentication**: Usuarios activos

### URLs de Monitoreo

- **Console**: `https://console.firebase.google.com/project/huerto-rentable`
- **Hosting**: `https://console.firebase.google.com/project/huerto-rentable/hosting`
- **Functions**: `https://console.firebase.google.com/project/huerto-rentable/functions`

## 🐛 Troubleshooting

### Error: "Firebase CLI not found"

```bash
npm install -g firebase-tools
firebase login
```

### Error: "Permission denied"

```bash
firebase login
firebase projects:list
firebase use huerto-rentable
```

### Error en Cloud Functions

```bash
cd functions
npm install
cd ..
firebase deploy --only functions
```

### Error en Hosting

```bash
python build.py
firebase deploy --only hosting
```

## 🎉 ¡Listo para Producción!

Tu aplicación HuertoRentable está configurada como:

✅ **PWA completa** con service worker y manifest  
✅ **Firebase Hosting** para entrega global rápida  
✅ **Cloud Functions** para backend escalable  
✅ **Firestore** para base de datos NoSQL  
✅ **Firebase Auth** para autenticación segura  
✅ **Bootstrap 5** para diseño responsive  
✅ **Chart.js** para analytics visuales

**¡Ejecuta el deploy y tu huerto rentable estará online! 🌱**
