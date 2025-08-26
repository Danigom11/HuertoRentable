# Configuración de Firebase para HuertoRentable

## ✅ Modo Demo (Funciona Sin Configuración)

**¡La aplicación ya está funcionando!** HuertoRentable incluye un modo demo completo con:

- Datos de ejemplo realistas (tomates, lechugas, zanahorias)
- Todas las funcionalidades visibles
- Gráficas y estadísticas
- Interfaz completamente funcional

**No necesitas configurar nada para probar la aplicación.**

## 🔧 Configuración de Firebase (Solo para Datos Reales)

Si quieres guardar TUS datos reales en lugar de usar los de ejemplo:

### Paso 1: Crear Proyecto Firebase

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Haz clic en "Add project" o "Crear proyecto"
3. Sigue el asistente de configuración

### Paso 2: Configurar Firestore

1. En el proyecto Firebase, ve a "Firestore Database"
2. Haz clic en "Create database"
3. Selecciona "Start in test mode" (para desarrollo)
4. Elige la ubicación más cercana a ti

### Paso 3: Obtener Credenciales

1. Ve a "Project Settings" (icono de engranaje)
2. Ve a la pestaña "Service accounts"
3. Haz clic en "Generate new private key"
4. Descarga el archivo JSON

### Paso 4: Instalar Credenciales

1. Guarda el archivo descargado como `serviceAccountKey.json`
2. Colócalo en la raíz del proyecto HuertoRentable
3. Reinicia la aplicación

### Paso 5: Configurar Reglas de Firestore

En Firestore Database > Rules, usa:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

**Nota**: Estas reglas son solo para desarrollo. En producción usa reglas más restrictivas.

## Verificar Funcionamiento

1. Reinicia la aplicación: `python app.py`
2. Deberías ver: "✅ Firebase inicializado correctamente"
3. Ve a http://127.0.0.1:5000
4. Los datos de ejemplo se crearán automáticamente

## Solución de Problemas

### Error: "No se pudo conectar a Firebase"

- Verifica que `serviceAccountKey.json` esté en la raíz
- Comprueba que el archivo JSON no esté corrupto
- Asegúrate de que el proyecto Firebase esté activo

### Error: "Permission denied"

- Revisa las reglas de Firestore
- Verifica que el Service Account tenga permisos

### La app funciona pero no hay datos

- Los datos de ejemplo se crean solo en el primer arranque
- Ve a Firebase Console > Firestore para ver los datos
- Puedes crear cultivos manualmente desde la interfaz

## Funcionalidades Disponibles

✅ **Dashboard**: Resumen de cultivos y beneficios
✅ **Gestión de Cultivos**: CRUD completo
✅ **Analytics**: Gráficas con Chart.js
✅ **PWA**: Instalable y funciona offline
✅ **Responsive**: Funciona en móviles y escritorio

## Datos de Ejemplo Incluidos

Cuando Firebase esté configurado, se crearán automáticamente:

- **Tomates**: €3.50/kg, con producción diaria
- **Lechugas**: €2.80/kg, con historial de abonos
- **Fechas realistas**: Basadas en temporadas de cultivo
- **Producción variada**: Entre 3-7 kg por recolección
