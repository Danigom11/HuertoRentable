# 🌱 HuertoRentable v2.0

**Aplicación web PWA profesional para gestión de huertos rentables**

Transforma tu huerto en un negocio rentable con analytics, seguimiento de producción y monetización integrada.

![Estado](https://img.shields.io/badge/Estado-Producción-brightgreen)
![Versión](https://img.shields.io/badge/Versión-2.0-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-orange)
![Firebase](https://img.shields.io/badge/Firebase-✅-yellow)

## 🚀 **Demo en Vivo**

**🌐 Web App**: [https://huertorentable.onrender.com](https://huertorentable.onrender.com)

## ✨ **Características Principales**

### 🎯 **Gestión Completa**

- 📊 Dashboard con resumen de cultivos y beneficios
- 🌱 CRUD completo de cultivos con seguimiento temporal
- � Analytics básicos y avanzados (premium)
- 💰 Cálculo automático de ROI y rentabilidad

### 🔐 **Sistema Multi-Usuario**

- 🔑 Autenticación con Firebase Authentication
- 👥 Datos privados por usuario con Firestore
- 📱 Sincronización multi-dispositivo
- ☁️ Backup automático en la nube

### 💳 **Modelos de Monetización**

- 🆓 **Plan Invitado**: 3 cultivos máximo, datos locales
- 🌟 **Plan Gratuito**: Cultivos ilimitados, backup en nube
- 💎 **Plan Premium (€0.99/mes)**: Sin anuncios + analytics avanzados

### 📱 **PWA Completa**

- ⚡ Funciona offline
- 🏠 Instalable como app nativa
- 📱 Optimizada para móviles
- 🔔 Notificaciones push (premium)

## 🛠️ **Stack Tecnológico**

### **Backend**

- **Flask 2.3.3**: Framework web Python
- **Firebase Firestore**: Base de datos NoSQL
- **Firebase Authentication**: Sistema de usuarios
- **JWT**: Tokens de sesión personalizados

### **Frontend**

- **Bootstrap 5**: Framework CSS moderno
- **Chart.js**: Gráficas interactivas
- **PWA**: Service Worker + Manifest
- **JavaScript ES6+**: Interactividad

### **DevOps & Deploy**

- **Render.com**: Hosting en la nube
- **GitHub Actions**: CI/CD (planeado)
- **Environment Variables**: Configuración segura

## 🏗️ **Arquitectura Profesional**

```
HuertoRentable/
├── 📁 app/                    # Aplicación principal
│   ├── 📁 routes/             # Blueprints organizados
│   │   ├── main.py            # Rutas principales
│   │   ├── auth.py            # Autenticación
│   │   ├── crops.py           # Gestión cultivos
│   │   ├── analytics.py       # Analytics y reportes
│   │   └── api.py             # API RESTful
│   ├── 📁 services/           # Lógica de negocio
│   │   └── crop_service.py    # Servicio de cultivos
│   ├── 📁 auth/               # Sistema autenticación
│   │   └── auth_service.py    # Firebase Auth + JWT
│   ├── 📁 utils/              # Utilidades
│   │   └── helpers.py         # Funciones auxiliares
│   └── __init__.py            # Factory pattern
├── 📁 config/                 # Configuraciones
│   └── settings.py            # Config por entornos
├── 📁 templates/              # Templates Jinja2
├── 📁 static/                 # CSS, JS, imágenes
├── 📁 tests/                  # Tests unitarios
├── 📁 docs/                   # Documentación
├── run.py                     # Punto de entrada
└── requirements.txt           # Dependencias
```

## � **Instalación y Deploy**

### **Desarrollo Local**

```bash
# 1. Clonar repositorio
git clone https://github.com/Danigom11/HuertoRentable.git
cd HuertoRentable

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar Firebase
# Descargar serviceAccountKey.json de Firebase Console
# Colocar en la raíz del proyecto

# 5. Ejecutar aplicación
python run.py
```

### **Deploy en Producción**

Ver [DEPLOY.md](DEPLOY.md) para instrucciones completas de deploy en:

- ✅ **Render.com** (recomendado)
- ⚡ **Railway.app**
- 🔥 **Vercel**

## 📊 **Planes de Suscripción**

| Característica     | Invitado      | Gratuito      | Premium         |
| ------------------ | ------------- | ------------- | --------------- |
| **Cultivos**       | 3 máximo      | ♾️ Ilimitados | ♾️ Ilimitados   |
| **Backup nube**    | ❌            | ✅            | ✅              |
| **Anuncios**       | ✅ Frecuentes | ✅ Banner     | ❌ Sin anuncios |
| **Analytics**      | 📊 Básicos    | 📊 Básicos    | 📈 Avanzados    |
| **Exportar datos** | ❌            | ❌            | ✅ PDF/Excel    |
| **Recordatorios**  | ❌            | ❌            | ✅ Push         |
| **Precio**         | Gratis        | Gratis        | €0.99/mes       |

## 🎯 **Roadmap 2025**

### **Q1 2025** ✅

- [x] Reestructuración profesional
- [x] Sistema de autenticación
- [x] Multi-usuario con Firebase
- [x] Planes de suscripción

### **Q2 2025** 🚧

- [ ] Sistema de anuncios (AdMob/AdSense)
- [ ] Pasarela de pagos (Stripe)
- [ ] App Android nativa (React Native)
- [ ] Analytics avanzados

### **Q3 2025** 📋

- [ ] Notificaciones push
- [ ] Modo offline completo
- [ ] Exportación PDF/Excel
- [ ] Sistema de recomendaciones

### **Q4 2025** 🌟

- [ ] IA para predicciones
- [ ] Marketplace de productos
- [ ] API pública
- [ ] Versión iOS

## 🤝 **Contribuir**

1. Fork del proyecto
2. Crea feature branch (`git checkout -b feature/NuevaCaracteristica`)
3. Commit changes (`git commit -m 'Añadir nueva característica'`)
4. Push to branch (`git push origin feature/NuevaCaracteristica`)
5. Crear Pull Request

## 📄 **Licencia**

Este proyecto está bajo licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 👨‍💻 **Autor**

**Daniel Gómez** - [Danigom11](https://github.com/Danigom11)

---

### 🌟 **¿Te gusta el proyecto?**

⭐ **¡Dale una estrella en GitHub!**  
💬 **Comparte feedback y sugerencias**  
🚀 **Contribuye al desarrollo**

---

_Hecho con ❤️ en España 🇪🇸_

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
