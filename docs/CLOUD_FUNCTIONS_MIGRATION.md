# Migración a Google Cloud Functions - HuertoRentable

## 🎯 Estado de la Migración

### ✅ Completado:

1. **Estructura Cloud Functions creada**

   - `functions/package.json` - Configuración Node.js
   - `functions/index.js` - Configuración principal y middleware
   - `functions/crops.js` - Gestión de cultivos
   - `functions/analytics.js` - Analytics y reportes
   - `functions/auth.js` - Autenticación y perfiles

2. **Seguridad implementada**

   - Middleware de verificación de tokens Firebase
   - Aislamiento de usuarios por UID
   - Validación de permisos en cada endpoint

3. **Firebase.json actualizado**
   - Configuración para Node.js 18
   - Directorio correcto para Cloud Functions

### 🔄 En Proceso:

1. **Configuración del proyecto Firebase**
2. **Testing local con emuladores**
3. **Deployment a producción**

## 📋 URLs de las Cloud Functions

Cuando estén desplegadas, las URLs serán:

### Funciones Principales:

- **Health Check**: `https://us-central1-[PROJECT-ID].cloudfunctions.net/health`
- **User Info**: `https://us-central1-[PROJECT-ID].cloudfunctions.net/user`

### Gestión de Cultivos:

- **Listar cultivos**: `GET /crops/list`
- **Crear cultivo**: `POST /crops/create`
- **Obtener cultivo**: `GET /crops/{cropId}`
- **Actualizar cultivo**: `PUT /crops/{cropId}`
- **Eliminar cultivo**: `DELETE /crops/{cropId}`
- **Agregar producción**: `POST /crops/{cropId}/produccion`
- **Agregar abono**: `POST /crops/{cropId}/abono`

### Analytics:

- **Dashboard**: `GET /analytics/dashboard`
- **Producción por cultivo**: `GET /analytics/produccion/{cropId}`
- **Comparativa anual**: `GET /analytics/comparativa`
- **Exportar datos**: `GET /analytics/export`

### Autenticación:

- **Registro inicial**: `POST /auth/register` (sin auth)
- **Obtener perfil**: `GET /auth/profile`
- **Actualizar perfil**: `POST /auth/profile`
- **Obtener planes**: `GET /auth/planes`
- **Verificar límites**: `GET /auth/limits`
- **Upgrade plan**: `POST /auth/upgrade-plan`
- **Eliminar cuenta**: `DELETE /auth/account`

## 🔐 Autenticación

Todas las rutas (excepto `/auth/register` y `/health`) requieren:

```javascript
headers: {
  'Authorization': 'Bearer ' + firebaseIdToken,
  'Content-Type': 'application/json'
}
```

## 📱 Integración con Android

### Ejemplo de llamada desde Android:

```kotlin
// Obtener token de Firebase Auth
val user = FirebaseAuth.getInstance().currentUser
user?.getIdToken(true)?.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val idToken = task.result?.token

        // Hacer request a Cloud Function
        val request = Request.Builder()
            .url("https://us-central1-PROJECT-ID.cloudfunctions.net/crops/list")
            .addHeader("Authorization", "Bearer $idToken")
            .build()

        // Ejecutar request...
    }
}
```

## 🚀 Próximos Pasos

### 1. Configurar Proyecto Firebase

```bash
firebase use --add
# Seleccionar tu proyecto HuertoRentable
```

### 2. Instalar dependencias

```bash
cd functions
npm install
```

### 3. Testing local

```bash
firebase emulators:start --only functions
```

### 4. Deploy a producción

```bash
firebase deploy --only functions
```

## 🔄 Equivalencias Flask → Cloud Functions

| Flask Route       | Cloud Function           | Método         | Auth |
| ----------------- | ------------------------ | -------------- | ---- |
| `/dashboard`      | `/analytics/dashboard`   | GET            | ✅   |
| `/crops`          | `/crops/list`            | GET            | ✅   |
| `/crops/create`   | `/crops/create`          | POST           | ✅   |
| `/api/crops/{id}` | `/crops/{id}`            | GET/PUT/DELETE | ✅   |
| `/analytics`      | `/analytics/comparativa` | GET            | ✅   |
| `/login`          | Frontend + Firebase Auth | -              | -    |
| `/profile`        | `/auth/profile`          | GET/POST       | ✅   |

## 💰 Costos Estimados

### Google Cloud Functions:

- **Primeros 2M invocaciones/mes**: GRATIS
- **Siguientes invocaciones**: $0.40 por millón
- **Tiempo de ejecución**: $0.0000025 por 100ms

### Para HuertoRentable:

- **Usuarios < 1000**: $0/mes
- **Usuarios moderados (5000)**: $1-3/mes
- **Escala grande**: Automática y proporcional

## 🔧 Ventajas de Cloud Functions

✅ **Escalabilidad automática**
✅ **Integración nativa con Firebase**
✅ **Menor latencia global**
✅ **Costos optimizados**
✅ **Mantenimiento mínimo**
✅ **HTTPS automático**
✅ **Monitoreo integrado**

## 📞 Soporte

Las Cloud Functions incluyen:

- Logs automáticos en Firebase Console
- Métricas de rendimiento
- Alertas de errores
- Monitoreo de costos

¡Tu backend está listo para escalar con tu app Android! 🚀
