# Test de Cloud Functions - HuertoRentable

## 🎯 URLs de Testing Local

### Funciones Base:

- **Health Check**: http://127.0.0.1:5001/huerto-rentable/us-central1/health
- **User Info**: http://127.0.0.1:5001/huerto-rentable/us-central1/user (requiere auth)

### Gestión de Cultivos:

- **Listar cultivos**: GET http://127.0.0.1:5001/huerto-rentable/us-central1/crops/list
- **Crear cultivo**: POST http://127.0.0.1:5001/huerto-rentable/us-central1/crops/create
- **Obtener cultivo**: GET http://127.0.0.1:5001/huerto-rentable/us-central1/crops/{id}

### Analytics:

- **Dashboard**: GET http://127.0.0.1:5001/huerto-rentable/us-central1/analytics/dashboard
- **Exportar**: GET http://127.0.0.1:5001/huerto-rentable/us-central1/analytics/export

### Autenticación:

- **Perfil**: GET http://127.0.0.1:5001/huerto-rentable/us-central1/auth/profile
- **Planes**: GET http://127.0.0.1:5001/huerto-rentable/us-central1/auth/planes

## 🧪 Comandos de Testing

### 1. Health Check (Sin autenticación)

```bash
curl http://127.0.0.1:5001/huerto-rentable/us-central1/health
```

### 2. Obtener planes (Sin autenticación)

```bash
curl http://127.0.0.1:5001/huerto-rentable/us-central1/auth/planes
```

### 3. Con autenticación (necesitas token Firebase)

```bash
curl -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
     http://127.0.0.1:5001/huerto-rentable/us-central1/crops/list
```

## 🚀 Próximo Paso: Deploy a Producción

Una vez que funcionen bien localmente:

```bash
firebase deploy --only functions
```

## 📱 URLs Finales para Android

Cuando estén desplegadas, las URLs serán:

- **Base URL**: https://us-central1-huerto-rentable.cloudfunctions.net/
- **Ejemplo**: https://us-central1-huerto-rentable.cloudfunctions.net/crops/list

## ✅ Estado Actual

- [x] Cloud Functions creadas
- [x] Dependencias instaladas
- [x] Emulador funcionando
- [x] Todas las funciones cargadas
- [ ] Testing manual
- [ ] Deploy a producción

¡Tu backend está listo para Android! 🎉
