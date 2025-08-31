#!/usr/bin/env python3
"""
Script de prueba para verificar conectividad con Firestore
"""
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

def test_firestore():
    try:
        # Inicializar Firebase si no está inicializado
        if not firebase_admin._apps:
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
            
        db = firestore.client()
        
        print("✅ Conexión a Firestore establecida")
        
        # Probar escribir un documento de prueba
        test_doc = {
            'test': True,
            'timestamp': datetime.datetime.utcnow(),
            'message': 'Prueba de conectividad'
        }
        
        doc_ref = db.collection('test').document('connectivity_test')
        doc_ref.set(test_doc)
        print("✅ Documento de prueba creado")
        
        # Leer el documento
        doc = doc_ref.get()
        if doc.exists:
            print(f"✅ Documento leído: {doc.to_dict()}")
        
        # Limpiar
        doc_ref.delete()
        print("✅ Documento de prueba eliminado")
        
        # Verificar si existe algún usuario
        users_ref = db.collection('usuarios')
        users = list(users_ref.limit(1).stream())
        
        if users:
            print(f"✅ Encontrados {len(users)} usuarios en la base de datos")
            user_data = users[0].to_dict()
            print(f"📋 Ejemplo de usuario: plan={user_data.get('plan', 'No especificado')}")
        else:
            print("⚠️ No se encontraron usuarios en la colección 'usuarios'")
            
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a Firestore: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_firestore()
