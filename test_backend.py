"""
Test directo del sistema de registro Firebase
Para diagnosticar el problema de "ha ocurrido un error inesperado"
"""

# Test de importaciones
try:
    print("🔍 Testing imports...")
    from app.auth.auth_service import AuthService, UserService
    print("✅ AuthService importado correctamente")
    
    from firebase_admin import auth as firebase_auth
    print("✅ Firebase Auth importado correctamente")
    
    import firebase_admin
    print(f"✅ Firebase Admin disponible, apps: {len(firebase_admin._apps)}")
    
except Exception as e:
    print(f"❌ Error en imports: {e}")

# Test de configuración Firebase
try:
    print("\n🔍 Testing Firebase config...")
    
    # Verificar que Firebase esté inicializado
    if firebase_admin._apps:
        print("✅ Firebase está inicializado en el backend")
        
        # Test de verificación de token
        print("\n🔍 Testing token verification...")
        try:
            # Intentar verificar un token inválido (debería fallar gracefully)
            result = AuthService.verify_firebase_token("invalid-token")
            print(f"✅ verify_firebase_token funcionando: {result}")
        except Exception as token_error:
            print(f"⚠️ Token verification error (esperado): {token_error}")
    else:
        print("❌ Firebase NO está inicializado en el backend")
        
except Exception as e:
    print(f"❌ Error en Firebase config: {e}")

print("\n🎯 Test completado")
