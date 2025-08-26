# Guía de Deploy - HuertoRentable

## 🌐 Deployment Options

### 1. Vercel (Recomendado)

```bash
npm install -g vercel
vercel login
vercel
```

### 2. Render

1. Conecta tu GitHub
2. New Web Service
3. Runtime: Python 3
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python app.py`

### 3. Railway

1. railway.app
2. Deploy from GitHub
3. Configuración automática

## 🔧 Variables de Entorno Necesarias

En el servicio de deploy, configurar:

```
FLASK_ENV=production
SECRET_KEY=tu-clave-secreta-super-segura
FIREBASE_TYPE=service_account
FIREBASE_PROJECT_ID=huerto-rentable
FIREBASE_PRIVATE_KEY_ID=tu-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\ntu-clave-privada\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@huerto-rentable.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=tu-client-id
```

## 📱 URLs de Acceso

- **Local**: http://192.168.1.140:5001
- **Producción**: Se asignará automáticamente al deployar

## 🔐 Seguridad

- ✅ serviceAccountKey.json no se sube (está en .gitignore)
- ✅ Variables de entorno para credenciales
- ✅ SECRET_KEY configurable
