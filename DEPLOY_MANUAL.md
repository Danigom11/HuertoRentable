# 🚀 INSTRUCCIONES MANUALES DE DEPLOY

## ⚠️ El deploy necesita ejecutarse manualmente

### 📋 Pasos para hacer el deploy:

1. **Abre una nueva terminal PowerShell**

   ```
   Presiona Win + X → Windows PowerShell
   ```

2. **Navega al directorio del proyecto**

   ```powershell
   cd "C:\Users\danig\Documentos\GitHub\HuertoRentable"
   ```

3. **Verifica que Firebase esté configurado**

   ```powershell
   firebase --version
   firebase use
   ```

4. **Ejecuta el deploy**
   ```powershell
   firebase deploy --only functions
   ```

## 🎯 ¿Qué va a pasar?

El comando tardará 2-5 minutos y mostrará:

- ✅ Subiendo código de las 5 funciones
- ✅ Creando/actualizando funciones en Google Cloud
- ✅ URLs finales para cada función

## 📱 URLs Finales

Después del deploy exitoso obtendrás:

### Base URL para Android:

```
https://us-central1-huerto-rentable.cloudfunctions.net/
```

### Funciones específicas:

- `/health` - Health check
- `/crops/list` - Listar cultivos
- `/crops/create` - Crear cultivo
- `/analytics/dashboard` - Dashboard
- `/auth/profile` - Perfil de usuario

## ✅ Verificar que funciona

Después del deploy, prueba:

```
https://us-central1-huerto-rentable.cloudfunctions.net/health
```

Debería responder:

```json
{
  "status": "healthy",
  "service": "HuertoRentable Cloud Functions",
  "version": "1.0.0",
  "firebase": "connected"
}
```

## 🎉 ¡Ya tienes tu backend listo para Android!

### Lo que has logrado:

- ✅ Backend 100% seguro con Firebase Auth
- ✅ 5 Cloud Functions desplegadas
- ✅ Escalabilidad automática
- ✅ Costos optimizados (gratis hasta 2M requests/mes)
- ✅ URLs listas para la app Android

### Próximo paso:

**Desarrollar la app Android** con estas URLs como backend.

---

### 📞 Si hay problemas:

**Error de autenticación:**

```powershell
firebase login
```

**Error de proyecto:**

```powershell
firebase use huerto-rentable
```

**Ver logs si falla:**

```powershell
firebase functions:log
```

¡Tu sistema está completamente listo! 🚀
