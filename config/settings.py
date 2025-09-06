"""
Configuración centralizada para HuertoRentable
Manejo de variables de entorno y configuraciones por ambiente
"""
import os
from datetime import timedelta

class Config:
    """Configuración base"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Session configuration - MÁS AGRESIVA para desarrollo
    SESSION_COOKIE_SECURE = False  # False para desarrollo sin HTTPS
    SESSION_COOKIE_HTTPONLY = False  # Permitir JS para debug
    SESSION_COOKIE_SAMESITE = 'Lax'  # Más compatible que None
    SESSION_COOKIE_DOMAIN = None  # Permitir localhost y 127.0.0.1
    SESSION_COOKIE_PATH = '/'  # Asegurar que funciona en toda la app
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_PERMANENT = True
    SESSION_COOKIE_NAME = 'huerto_session'  # Nombre específico para debug
    SESSION_REFRESH_EACH_REQUEST = True  # Refrescar en cada request
    SESSION_USE_SIGNER = True  # Firmar cookies para seguridad
    
    # Firebase
    FIREBASE_TYPE = os.environ.get('FIREBASE_TYPE')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    FIREBASE_PRIVATE_KEY_ID = os.environ.get('FIREBASE_PRIVATE_KEY_ID')
    FIREBASE_PRIVATE_KEY = os.environ.get('FIREBASE_PRIVATE_KEY')
    FIREBASE_CLIENT_EMAIL = os.environ.get('FIREBASE_CLIENT_EMAIL')
    FIREBASE_CLIENT_ID = os.environ.get('FIREBASE_CLIENT_ID')
    FIREBASE_AUTH_URI = os.environ.get('FIREBASE_AUTH_URI')
    FIREBASE_TOKEN_URI = os.environ.get('FIREBASE_TOKEN_URI')
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL = os.environ.get('FIREBASE_AUTH_PROVIDER_X509_CERT_URL')
    FIREBASE_CLIENT_X509_CERT_URL = os.environ.get('FIREBASE_CLIENT_X509_CERT_URL')
    FIREBASE_UNIVERSE_DOMAIN = os.environ.get('FIREBASE_UNIVERSE_DOMAIN')
    
    # Firebase Web SDK (Frontend) - opcional, para evitar hardcodear claves en JS
    FIREBASE_WEB_API_KEY = os.environ.get('FIREBASE_WEB_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET')
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID')
    
    # Planes de suscripción
    PLAN_GRATUITO = {
        'nombre': 'Gratuito', 
        'precio': 0,
        'cultivos_max': None,  # Ilimitados
        'anuncios': True,
        'backup': True,
        'analytics_avanzados': False
    }
    
    PLAN_PREMIUM = {
        'nombre': 'Premium',
        'precio': 0.99,
        'cultivos_max': None,  # Ilimitados
        'anuncios': False,
        'backup': True,
        'analytics_avanzados': True,
        'recordatorios': True,
        'exportar_datos': True
    }
    
    # JWT para autenticación
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Configuración de anuncios
    ADMOB_APP_ID = os.environ.get('ADMOB_APP_ID')
    ADMOB_BANNER_ID = os.environ.get('ADMOB_BANNER_ID')
    ADMOB_INTERSTITIAL_ID = os.environ.get('ADMOB_INTERSTITIAL_ID')
    
    # Google AdSense (para web)
    ADSENSE_CLIENT_ID = os.environ.get('ADSENSE_CLIENT_ID')
    
    # Analytics
    GA_TRACKING_ID = os.environ.get('GA_TRACKING_ID')

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    FLASK_ENV = 'development'
    
    # Session configuration específica para desarrollo
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_DOMAIN = None
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Session configuration específica para producción (HTTPS)
    SESSION_COOKIE_SECURE = True  # Requiere HTTPS en producción
    SESSION_COOKIE_HTTPONLY = True  # Seguridad: no acceso desde JS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Compatible con navegación normal
    SESSION_COOKIE_DOMAIN = None  # Auto-detectar dominio
    SESSION_COOKIE_PATH = '/'

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    DEBUG = True

# Diccionario de configuraciones disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
