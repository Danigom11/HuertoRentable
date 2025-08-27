# 🚀 **Guía de Deploy - HuertoRentable**

Instrucciones completas para desplegar HuertoRentable en diferentes plataformas de hosting.

## 📋 **Prerrequisitos**

- ✅ Proyecto Firebase configurado
- ✅ Credenciales Firebase (`serviceAccountKey.json`)
- ✅ Repositorio Git configurado
- ✅ Variables de entorno definidas

## 🌐 **Render.com (Recomendado)**

### **1. Preparar el Proyecto**

Asegúrate de tener estos archivos en tu repositorio:

```bash
HuertoRentable/
├── run.py                 # ✅ Punto de entrada
├── requirements.txt       # ✅ Dependencias
├── Procfile              # ✅ Comando de inicio
└── serviceAccountKey.json # ❌ NO subir a Git
```

### **2. Configurar Variables de Entorno**

En lugar de subir `serviceAccountKey.json`, configura estas variables en Render:

```env
FLASK_ENV=production
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria

# Firebase Configuration
FIREBASE_TYPE=service_account
FIREBASE_PROJECT_ID=tu-proyecto-id
FIREBASE_PRIVATE_KEY_ID=clave-privada-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nTU_CLAVE_PRIVADA\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@tu-proyecto.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=cliente-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40tu-proyecto.iam.gserviceaccount.com

# JWT Configuration
JWT_SECRET_KEY=otra-clave-secreta-diferente-para-jwt
JWT_ACCESS_TOKEN_EXPIRES=3600
```

### **3. Deploy en Render**

1. **Conectar repositorio**:

   - Ve a [Render.com](https://render.com)
   - Conecta tu cuenta GitHub
   - Selecciona el repositorio `HuertoRentable`

2. **Configurar servicio**:

   ```
   Name: huertorentable
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python run.py
   ```

3. **Variables de entorno**:

   - Copia todas las variables de arriba
   - Ve a Environment → Add environment variables

4. **Deploy automático**:
   - ✅ Auto-Deploy: ON
   - Cada push a `main` desplegará automáticamente

### **4. Verificar Deploy**

- URL será: `https://huertorentable.onrender.com`
- Verificar logs en Render Dashboard
- Probar autenticación y Firebase

---

## ⚡ **Railway.app**

### **1. Configuración**

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Inicializar en el proyecto
railway init
```

### **2. Variables de entorno**

```bash
# Configurar variables
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=tu-clave-secreta
# ... (mismas variables que Render)
```

### **3. Deploy**

```bash
# Deploy
railway up

# Ver logs
railway logs
```

---

## 🔥 **Vercel**

### **1. Configurar vercel.json**

```json
{
  "version": 2,
  "builds": [
    {
      "src": "run.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "run.py"
    }
  ]
}
```

### **2. Deploy**

```bash
# Instalar Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

---

## 🐳 **Docker**

### **1. Crear Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "run.py"]
```

### **2. Build y Run**

```bash
# Build
docker build -t huertorentable .

# Run
docker run -p 5001:5001 --env-file .env huertorentable
```

---

## ☁️ **Google Cloud Platform**

### **1. App Engine**

Crear `app.yaml`:

```yaml
runtime: python311

env_variables:
  FLASK_ENV: production
  SECRET_KEY: tu-clave-secreta
  # ... otras variables

automatic_scaling:
  min_instances: 0
  max_instances: 10
```

### **2. Deploy**

```bash
gcloud app deploy
```

---

## 📱 **Mobile Access**

### **1. PWA Installation**

Una vez desplegado, los usuarios pueden:

1. **En móvil (Chrome/Safari)**:

   - Visitar la URL
   - Tocar "Añadir a pantalla de inicio"
   - ✅ App instalada como nativa

2. **En escritorio**:
   - Chrome → ⋮ → "Instalar HuertoRentable"
   - ✅ App en dock/escritorio

### **2. Dominio Personalizado**

Para un dominio propio:

1. **Comprar dominio** (ej: `mipersonalhuerto.com`)
2. **Configurar DNS**:
   ```
   CNAME www.mipersonalhuerto.com → huertorentable.onrender.com
   ```
3. **SSL automático** ✅ (incluido en Render)

---

## 🔧 **Troubleshooting**

### **Error: No module named 'app'**

```bash
# Verificar que run.py existe y es el punto de entrada
# Cambiar Start Command a: python run.py
```

### **Error: Firebase credentials**

```bash
# Verificar variables de entorno
# Comprobar formato de FIREBASE_PRIVATE_KEY (con \n)
```

### **Error: Port binding**

```bash
# run.py debe usar puerto del entorno:
port = int(os.environ.get('PORT', 5001))
app.run(host='0.0.0.0', port=port)
```

### **Error: Static files 404**

```bash
# Verificar estructura de carpetas
# Flask debe encontrar /static y /templates
```

---

## 📊 **Monitoreo**

### **Logs en Render**

- Dashboard → Service → Logs
- Ver errores en tiempo real
- Filtrar por tipo de log

### **Firebase Console**

- Firestore usage
- Authentication statistics
- Performance monitoring

### **Analytics**

- Google Analytics (opcional)
- User behavior tracking
- Performance metrics

---

## 🔄 **CI/CD Pipeline**

### **GitHub Actions** (Futuro)

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v3
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/
```

---

## ✅ **Checklist de Deploy**

### **Pre-Deploy**

- [ ] Variables de entorno configuradas
- [ ] Firebase project creado
- [ ] Tests passing localmente
- [ ] Git repository configurado

### **Durante Deploy**

- [ ] Build successful
- [ ] Start command correcto
- [ ] Port binding configurado
- [ ] Static files serving

### **Post-Deploy**

- [ ] URL accesible
- [ ] Firebase conectando
- [ ] PWA instalable
- [ ] Mobile responsive
- [ ] SSL certificate activo

---

**🎉 ¡Felicidades! Tu HuertoRentable está live en producción!**

Para soporte: [Issues GitHub](https://github.com/Danigom11/HuertoRentable/issues)
