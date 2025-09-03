# 🔒 Configuración de Reglas de Seguridad Firebase - HuertoRentable

## 📋 Pasos para Configurar Reglas de Seguridad

### 1. **Instalar Firebase CLI**

```bash
npm install -g firebase-tools
```

### 2. **Autenticarse en Firebase**

```bash
firebase login
```

### 3. **Configurar el proyecto**

```bash
# Si es primera vez
firebase init

# O conectar proyecto existente
firebase use --add
```

### 4. **Desplegar reglas de seguridad**

```bash
# Opción 1: Manual
firebase deploy --only firestore:rules
firebase deploy --only storage

# Opción 2: Usando nuestro script
python scripts/deploy_firestore_rules.py
```

---

## 🛡️ Reglas de Seguridad Implementadas

### **Firestore Database**

#### ✅ **Colección: `cultivos`**

- **Lectura/Escritura**: Solo el propietario (`user_uid == request.auth.uid`)
- **Creación**: Requiere `user_uid` que coincida con el usuario autenticado
- **Validación**: Campos obligatorios (`nombre`, `user_uid`, `fecha_siembra`)

```javascript
// Ejemplo de regla
match /cultivos/{cropId} {
  allow read, write: if isAuthenticated()
    && resource.data.user_uid == request.auth.uid;
}
```

#### ✅ **Colección: `usuarios`**

- **Acceso**: Solo el propio usuario puede ver/modificar sus datos
- **Aislamiento**: Imposible ver datos de otros usuarios

#### ✅ **Subcolecciones: `producciones` y `abonos`**

- **Herencia**: Permisos heredados del cultivo padre
- **Validación**: Verificación del `user_uid` del cultivo principal

#### ✅ **Colección: `planes`**

- **Lectura**: Usuarios autenticados (información pública)
- **Escritura**: Solo administradores (requiere custom claims)

### **Firebase Storage**

#### ✅ **Imágenes de cultivos**: `/users/{userId}/crops/{cropId}/{filename}`

- **Acceso**: Solo el propietario
- **Validación**: Solo imágenes, máximo 5MB

#### ✅ **Avatares**: `/users/{userId}/avatar/{filename}`

- **Acceso**: Solo el usuario propietario
- **Validación**: Solo imágenes, máximo 2MB

#### ✅ **Exports**: `/exports/{userId}/{filename}`

- **Acceso**: Solo el usuario propietario
- **Formatos**: CSV, JSON, PDF, Excel
- **Tamaño**: Máximo 10MB

---

## 🔍 Validación de Seguridad

### **Casos de Prueba Críticos**

1. **❌ Usuario A no puede ver cultivos de Usuario B**
2. **❌ Peticiones sin autenticación son rechazadas**
3. **❌ Tokens expirados son rechazados**
4. **❌ Modificación de `user_uid` es imposible**
5. **✅ Solo datos propios son accesibles**

### **Testing de Reglas**

```bash
# Instalar emulador
firebase emulators:start --only firestore

# Ejecutar tests (crear archivo de pruebas)
firebase emulators:exec --only firestore "npm test"
```

---

## ⚡ Índices de Rendimiento

### **Consultas Optimizadas**

1. **Cultivos por usuario ordenados por fecha**

   ```
   user_uid ASC + fecha_siembra DESC
   ```

2. **Cultivos activos por usuario**

   ```
   user_uid ASC + activo ASC + fecha_siembra DESC
   ```

3. **Producciones recientes**
   ```
   user_uid ASC + fecha DESC
   ```

---

## 🚨 Puntos Críticos de Seguridad

### ✅ **Lo que SÍ está protegido:**

- ✅ Aislamiento total de datos por usuario
- ✅ Verificación de tokens Firebase en cada operación
- ✅ Validación de tipos de archivo en Storage
- ✅ Límites de tamaño de archivo
- ✅ Solo propietarios pueden acceder a sus datos

### ❌ **Vulnerabilidades eliminadas:**

- ❌ Acceso cruzado entre usuarios
- ❌ Lectura de datos sin autenticación
- ❌ Modificación de `user_uid` por parte del cliente
- ❌ Subida de archivos maliciosos
- ❌ Ataques de enumeración de datos

---

## 📊 Monitoreo de Seguridad

### **Firebase Console**

1. **Firestore → Rules**: Ver reglas activas
2. **Storage → Rules**: Ver reglas de almacenamiento
3. **Authentication → Users**: Monitorear usuarios
4. **Usage**: Verificar patrones de acceso anómalos

### **Logs de Seguridad**

```bash
# Ver logs en tiempo real
firebase functions:log --only hosting

# Logs de reglas de Firestore
firebase firestore:logs
```

---

## 🔧 Comandos Útiles

```bash
# Ver reglas actuales
firebase firestore:rules get

# Hacer backup de reglas
firebase firestore:rules get > firestore.rules.backup

# Validar reglas localmente
firebase firestore:rules --dry-run

# Desplegar solo reglas
firebase deploy --only firestore:rules

# Desplegar todo el proyecto
firebase deploy
```

---

## 🆘 Resolución de Problemas

### **Error: "Missing or insufficient permissions"**

- ✅ Verificar que el usuario esté autenticado
- ✅ Comprobar que el token no haya expirado
- ✅ Asegurar que `user_uid` coincida con `request.auth.uid`

### **Error: "Permission denied"**

- ✅ Verificar reglas de Firestore
- ✅ Comprobar estructura de datos
- ✅ Validar que los campos requeridos estén presentes

### **Error en Storage**

- ✅ Verificar tipo de archivo
- ✅ Comprobar tamaño del archivo
- ✅ Asegurar que la ruta incluya el `userId` correcto

---

## ✅ Checklist Final

- [ ] Reglas de Firestore desplegadas
- [ ] Reglas de Storage desplegadas
- [ ] Índices configurados
- [ ] Tests de seguridad ejecutados
- [ ] Monitoring configurado
- [ ] Backup de reglas anteriores realizado

**🎯 Una vez completado, tu base de datos estará 100% segura y lista para producción.**
