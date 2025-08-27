# 📚 **Documentación Técnica - HuertoRentable v2.0**

Documentación completa de la arquitectura, APIs y funcionalidades del sistema.

## 📋 **Índice**

1. [Arquitectura del Sistema](#arquitectura)
2. [Modelos de Datos](#modelos)
3. [API Endpoints](#api)
4. [Sistema de Autenticación](#auth)
5. [Servicios](#servicios)
6. [Frontend](#frontend)
7. [Configuración](#configuracion)

---

## 🏗️ **Arquitectura del Sistema** {#arquitectura}

### **Patrón Factory**

```python
# app/__init__.py
def create_app(config_name=None):
    """Factory pattern para crear la aplicación Flask"""
    app = Flask(__name__)

    # Configuración
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    # Inicializar Firebase
    init_firebase()

    # Registrar Blueprints
    register_blueprints(app)

    return app
```

### **Blueprints**

| Blueprint   | Prefijo      | Descripción                             |
| ----------- | ------------ | --------------------------------------- |
| `main`      | `/`          | Rutas principales (dashboard, home)     |
| `auth`      | `/auth`      | Autenticación (login, register, logout) |
| `crops`     | `/crops`     | Gestión de cultivos (CRUD)              |
| `analytics` | `/analytics` | Reportes y estadísticas                 |
| `api`       | `/api`       | RESTful API endpoints                   |

### **Capas de la Aplicación**

```
┌─────────────────┐
│   Templates     │ ← Jinja2 + Bootstrap 5
├─────────────────┤
│   Blueprints    │ ← Rutas y controladores
├─────────────────┤
│   Services      │ ← Lógica de negocio
├─────────────────┤
│   Auth Service  │ ← Autenticación y autorización
├─────────────────┤
│   Firebase      │ ← Firestore + Authentication
└─────────────────┘
```

---

## 📊 **Modelos de Datos** {#modelos}

### **Usuario (Firebase Auth)**

```python
{
    "uid": "string",           # ID único Firebase
    "email": "string",         # Email del usuario
    "displayName": "string",   # Nombre público
    "emailVerified": "boolean", # Email verificado
    "plan": "string",          # Plan: invitado|gratuito|premium
    "created_at": "timestamp", # Fecha de registro
    "subscription": {          # Datos suscripción (premium)
        "stripe_customer_id": "string",
        "subscription_id": "string",
        "status": "active|canceled",
        "expires_at": "timestamp"
    }
}
```

### **Cultivo (Firestore)**

```python
{
    "id": "auto_generated",
    "user_id": "string",       # ID del usuario propietario
    "nombre": "string",        # Nombre del cultivo
    "precio_kg": "number",     # Precio por kilogramo (€)
    "fecha_siembra": "date",   # Fecha de siembra
    "fecha_cosecha": "date",   # Fecha estimada/real cosecha
    "estado": "string",        # activo|cosechado|pausado
    "produccion": [            # Array de producciones
        {
            "fecha": "date",
            "cantidad": "number", # Kilogramos
            "notas": "string"     # Notas opcionales
        }
    ],
    "gastos": [               # Array de gastos
        {
            "fecha": "date",
            "concepto": "string",
            "cantidad": "number"  # Euros
        }
    ],
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

### **Plan Limits (Config)**

```python
PLAN_LIMITS = {
    'invitado': {
        'max_crops': 3,
        'firebase_backup': False,
        'ads': True,
        'analytics': 'basic',
        'export': False,
        'notifications': False
    },
    'gratuito': {
        'max_crops': float('inf'),
        'firebase_backup': True,
        'ads': True,
        'analytics': 'basic',
        'export': False,
        'notifications': False
    },
    'premium': {
        'max_crops': float('inf'),
        'firebase_backup': True,
        'ads': False,
        'analytics': 'advanced',
        'export': True,
        'notifications': True
    }
}
```

---

## 🔗 **API Endpoints** {#api}

### **Autenticación**

```http
POST /auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123"
}

Response:
{
    "success": true,
    "token": "jwt_token_here",
    "user": {
        "uid": "user_id",
        "email": "user@example.com",
        "plan": "gratuito"
    }
}
```

```http
POST /auth/register
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123",
    "display_name": "Usuario Nombre"
}
```

```http
POST /auth/logout
Authorization: Bearer jwt_token_here
```

### **Cultivos**

```http
GET /api/crops
Authorization: Bearer jwt_token_here

Response:
{
    "success": true,
    "crops": [
        {
            "id": "crop_id",
            "nombre": "Tomates Cherry",
            "precio_kg": 4.50,
            "total_produccion": 25.3,
            "beneficio_total": 113.85
        }
    ]
}
```

```http
POST /api/crops
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
    "nombre": "Lechugas",
    "precio_kg": 2.80,
    "fecha_siembra": "2025-01-15"
}
```

```http
POST /api/crops/{crop_id}/produccion
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
    "fecha": "2025-01-20",
    "cantidad": 1.5,
    "notas": "Primera cosecha"
}
```

### **Analytics**

```http
GET /api/analytics/summary
Authorization: Bearer jwt_token_here

Response:
{
    "total_crops": 18,
    "total_production": 241.2,
    "total_revenue": 795.69,
    "active_crops": 12
}
```

```http
GET /api/analytics/charts
Authorization: Bearer jwt_token_here

Response:
{
    "production_by_crop": [...],
    "revenue_by_month": [...],
    "top_performers": [...]
}
```

---

## 🔐 **Sistema de Autenticación** {#auth}

### **AuthService**

```python
class AuthService:
    @staticmethod
    def verify_firebase_token(id_token):
        """Verificar token de Firebase Auth"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            raise AuthError(f"Token inválido: {str(e)}")

    @staticmethod
    def create_custom_token(user_data):
        """Crear JWT personalizado para sesiones"""
        payload = {
            'user_id': user_data['uid'],
            'email': user_data['email'],
            'plan': user_data.get('plan', 'invitado'),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'])
```

### **Decoradores**

```python
@login_required
def protected_route():
    """Requiere autenticación"""
    return jsonify({"user": g.current_user})

@premium_required
def premium_feature():
    """Requiere plan premium"""
    return jsonify({"advanced_analytics": "..."})
```

### **Middleware de Autenticación**

```python
@app.before_request
def load_user():
    """Cargar usuario actual en cada request"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'])
            g.current_user = UserService.get_user_by_id(payload['user_id'])
        except jwt.InvalidTokenError:
            g.current_user = None
```

---

## ⚙️ **Servicios** {#servicios}

### **CropService**

```python
class CropService:
    @staticmethod
    def get_user_crops(user_id, plan='gratuito'):
        """Obtener cultivos del usuario con límites de plan"""
        crops_ref = db.collection('crops').where('user_id', '==', user_id)
        crops = list(crops_ref.stream())

        # Aplicar límites según plan
        if plan == 'invitado':
            crops = crops[:PLAN_LIMITS['invitado']['max_crops']]

        return [crop.to_dict() for crop in crops]

    @staticmethod
    def create_crop(user_id, crop_data, plan='gratuito'):
        """Crear nuevo cultivo verificando límites"""
        # Verificar límites del plan
        current_crops = CropService.get_user_crops(user_id, plan)
        if plan == 'invitado' and len(current_crops) >= 3:
            raise PlanLimitError("Límite de cultivos alcanzado")

        # Crear cultivo
        crop_data['user_id'] = user_id
        crop_data['created_at'] = firestore.SERVER_TIMESTAMP

        doc_ref = db.collection('crops').document()
        doc_ref.set(crop_data)

        return doc_ref.id
```

### **UserService**

```python
class UserService:
    @staticmethod
    def get_user_plan(user_id):
        """Obtener plan del usuario"""
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()

        if user_doc.exists:
            return user_doc.to_dict().get('plan', 'invitado')
        return 'invitado'

    @staticmethod
    def upgrade_to_premium(user_id, stripe_data):
        """Actualizar usuario a premium tras pago"""
        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'plan': 'premium',
            'subscription': stripe_data,
            'upgraded_at': firestore.SERVER_TIMESTAMP
        })
```

---

## 🎨 **Frontend** {#frontend}

### **Templates Structure**

```
templates/
├── base.html              # Layout base con Bootstrap 5
├── auth/
│   ├── login.html         # Formulario de login
│   └── register.html      # Formulario de registro
├── dashboard/
│   └── index.html         # Dashboard principal
├── crops/
│   ├── index.html         # Lista de cultivos
│   ├── create.html        # Crear cultivo
│   └── detail.html        # Detalle de cultivo
└── analytics/
    └── index.html         # Gráficas y reportes
```

### **JavaScript Architecture**

```javascript
// static/js/app.js
class HuertoApp {
  constructor() {
    this.auth = new AuthManager();
    this.crops = new CropManager();
    this.analytics = new AnalyticsManager();
  }

  init() {
    this.setupEventListeners();
    this.loadInitialData();
  }
}

class AuthManager {
  async login(email, password) {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    if (data.success) {
      localStorage.setItem("auth_token", data.token);
      window.location.href = "/dashboard";
    }
  }
}
```

### **PWA Configuration**

```javascript
// service-worker.js
const CACHE_NAME = "huerto-rentable-v2";
const urlsToCache = [
  "/",
  "/static/css/styles.css",
  "/static/js/app.js",
  "/static/img/icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
  );
});
```

---

## ⚙️ **Configuración** {#configuracion}

### **Environment Configs**

```python
# config/settings.py
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'

class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
```

### **Firebase Configuration**

```python
def init_firebase():
    """Inicializar Firebase con credenciales"""
    try:
        # Intentar archivo JSON primero
        if os.path.exists('serviceAccountKey.json'):
            cred = credentials.Certificate('serviceAccountKey.json')
        else:
            # Usar variables de entorno
            firebase_config = {
                "type": os.environ.get("FIREBASE_TYPE"),
                "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
                "private_key": os.environ.get("FIREBASE_PRIVATE_KEY"),
                # ... más configuración
            }
            cred = credentials.Certificate(firebase_config)

        firebase_admin.initialize_app(cred)

    except Exception as e:
        print(f"Error inicializando Firebase: {e}")
```

---

## 🧪 **Testing**

### **Unit Tests**

```python
# tests/test_crop_service.py
class TestCropService(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def test_create_crop_with_limit(self):
        """Test límite de cultivos para plan invitado"""
        user_id = "test_user"
        plan = "invitado"

        # Crear 3 cultivos (límite)
        for i in range(3):
            CropService.create_crop(user_id, {"nombre": f"Cultivo {i}"}, plan)

        # El cuarto debe fallar
        with self.assertRaises(PlanLimitError):
            CropService.create_crop(user_id, {"nombre": "Cultivo 4"}, plan)
```

### **Integration Tests**

```python
# tests/test_api.py
class TestAPI(unittest.TestCase):
    def test_auth_flow(self):
        """Test complete authentication flow"""
        # Register
        response = self.client.post('/auth/register', json={
            'email': 'test@example.com',
            'password': 'test123'
        })
        self.assertEqual(response.status_code, 201)

        # Login
        response = self.client.post('/auth/login', json={
            'email': 'test@example.com',
            'password': 'test123'
        })
        self.assertEqual(response.status_code, 200)

        token = response.json['token']

        # Access protected route
        response = self.client.get('/api/crops', headers={
            'Authorization': f'Bearer {token}'
        })
        self.assertEqual(response.status_code, 200)
```

---

## 📈 **Performance**

### **Optimizaciones**

1. **Caché de Firebase**: Implementar Redis para caché de consultas frecuentes
2. **Lazy Loading**: Cargar cultivos bajo demanda con paginación
3. **CDN**: Servir assets estáticos desde CDN
4. **Compresión**: Gzip en todas las respuestas
5. **Database Indexing**: Índices en Firestore para consultas optimizadas

### **Monitoring**

```python
# Métricas de rendimiento
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    diff = time.time() - g.start_time
    if diff > 1.0:  # Log requests lentas
        app.logger.warning(f"Slow request: {request.endpoint} took {diff:.2f}s")
    return response
```

---

**📚 Esta documentación se actualiza con cada release. Para dudas: [GitHub Issues](https://github.com/Danigom11/HuertoRentable/issues)**
