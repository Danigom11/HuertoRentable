#!/usr/bin/env python3
"""
Script para crear un usuario de prueba en Firestore
"""
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

def create_test_user():
    try:
        # Inicializar Firebase si no está inicializado
        if not firebase_admin._apps:
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
            
        db = firestore.client()
        
        # ID de usuario de prueba (reemplaza con tu UID real de Firebase Auth)
        test_uid = "test_user_123"
        
        user_doc = {
            'uid': test_uid,
            'email': 'test@example.com',
            'name': 'Usuario de Prueba',
            'plan': 'gratuito',
            'fecha_registro': datetime.datetime.utcnow(),
            'ultimo_acceso': datetime.datetime.utcnow(),
            'configuracion': {
                'notificaciones': True,
                'analytics': True,
                'backup_automatico': True
            }
        }
        
        # Crear el usuario en Firestore
        db.collection('usuarios').document(test_uid).set(user_doc)
        print(f"✅ Usuario de prueba creado con UID: {test_uid}")
        print(f"📋 Plan asignado: {user_doc['plan']}")
        
        # Verificar que se creó
        doc = db.collection('usuarios').document(test_uid).get()
        if doc.exists:
            print("✅ Usuario verificado en Firestore")
            data = doc.to_dict()
            print(f"📊 Datos: {data}")
        else:
            print("❌ Error: Usuario no encontrado después de crear")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_user()
