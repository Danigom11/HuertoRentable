# Deploy Script para Cloud Functions - HuertoRentable

## 🚀 Comandos de Deploy

### Verificar configuración

```bash
firebase --version
firebase projects:list
firebase use
```

### Deploy a producción

```bash
firebase deploy --only functions
```

### Deploy específico por función (si hay problemas)

```bash
firebase deploy --only functions:health
firebase deploy --only functions:crops
firebase deploy --only functions:analytics
firebase deploy --only functions:auth
firebase deploy --only functions:user
```

### Verificar deploy

```bash
firebase functions:list
```

## 🎯 URLs Finales después del Deploy

Una vez desplegado, las URLs serán:

### Funciones Base:

- **Health Check**: https://us-central1-huerto-rentable.cloudfunctions.net/health
- **User Info**: https://us-central1-huerto-rentable.cloudfunctions.net/user

### Gestión de Cultivos:

- **Base URL**: https://us-central1-huerto-rentable.cloudfunctions.net/crops
- **Listar cultivos**: GET /crops/list
- **Crear cultivo**: POST /crops/create
- **Obtener cultivo**: GET /crops/{id}
- **Actualizar cultivo**: PUT /crops/{id}
- **Eliminar cultivo**: DELETE /crops/{id}
- **Agregar producción**: POST /crops/{id}/produccion
- **Agregar abono**: POST /crops/{id}/abono

### Analytics:

- **Base URL**: https://us-central1-huerto-rentable.cloudfunctions.net/analytics
- **Dashboard**: GET /analytics/dashboard
- **Producción**: GET /analytics/produccion/{id}
- **Comparativa**: GET /analytics/comparativa
- **Exportar**: GET /analytics/export

### Autenticación:

- **Base URL**: https://us-central1-huerto-rentable.cloudfunctions.net/auth
- **Registro**: POST /auth/register (sin auth)
- **Perfil**: GET/POST /auth/profile
- **Planes**: GET /auth/planes
- **Límites**: GET /auth/limits
- **Upgrade**: POST /auth/upgrade-plan
- **Eliminar cuenta**: DELETE /auth/account

## 📱 Para la App Android

### Configuración base en Android:

```kotlin
const val BASE_URL = "https://us-central1-huerto-rentable.cloudfunctions.net/"
```

### Ejemplo de request:

```kotlin
// Headers requeridos
headers["Authorization"] = "Bearer $firebaseToken"
headers["Content-Type"] = "application/json"

// Request a crops
val url = "${BASE_URL}crops/list"
```

## ✅ Checklist Post-Deploy

- [ ] Verificar health check funciona
- [ ] Probar autenticación con token real
- [ ] Verificar CORS para Android
- [ ] Comprobar logs en Firebase Console
- [ ] Actualizar URLs en documentación Android

## 🚨 Si hay errores

### Ver logs:

```bash
firebase functions:log
```

### Ver logs específicos:

```bash
firebase functions:log --only crops
```

### Re-deploy función específica:

```bash
firebase deploy --only functions:health
```

¡Tu backend estará listo para Android en minutos! 🎉
