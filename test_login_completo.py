#!/usr/bin/env python3
"""
Test completo del flujo de login - HuertoRentable
Simula el proceso completo de inicio de sesión
"""
import requests
import json
import time

# Configuración
BASE_URL = "http://127.0.0.1:5000"

def test_complete_login_flow():
    """Test completo del flujo de login"""
    session = requests.Session()
    
    print("🔍 VERIFICACIÓN COMPLETA DEL SISTEMA DE LOGIN")
    print("=" * 50)
    
    # 1. Verificar que el servidor esté ejecutándose
    try:
        response = session.get(f"{BASE_URL}/")
        print(f"✅ Servidor disponible (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        return False
    
    # 2. Verificar página de login
    try:
        response = session.get(f"{BASE_URL}/auth/login")
        print(f"✅ Página de login accesible (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error accediendo a login: {e}")
        return False
    
    # 3. Simular login con token válido (ejemplo)
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJ0ZXN0X3VzZXJfMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwibmFtZSI6IlRlc3QgVXNlciIsInBsYW4iOiJncmF0dWl0byIsImV4cCI6OTk5OTk5OTk5OSwiaWF0IjoxNzU3MTU0NTAwfQ.fake_signature"
    
    print("\n🔐 Intentando login...")
    try:
        login_data = {
            "idToken": fake_token
        }
        
        response = session.post(
            f"{BASE_URL}/auth/login",
            headers={'Content-Type': 'application/json'},
            json=login_data
        )
        
        print(f"Login response status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Login exitoso: {data.get('success', False)}")
                if 'redirect_url' in data:
                    print(f"   - Redirect URL: {data['redirect_url']}")
                if 'user' in data:
                    print(f"   - Usuario: {data['user']['email']}")
            except:
                print("✅ Login exitoso (respuesta HTML)")
        else:
            print(f"❌ Login falló: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return False
    
    # 4. Verificar acceso al dashboard
    print("\n🏠 Verificando acceso al dashboard...")
    try:
        response = session.get(f"{BASE_URL}/dashboard")
        print(f"Dashboard response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Acceso al dashboard exitoso")
        elif response.status_code == 302:
            print("⚠️ Dashboard redirige (posible problema de sesión)")
            print(f"   - Redirect a: {response.headers.get('Location', 'No especificado')}")
        else:
            print(f"❌ Error accediendo al dashboard: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Error verificando dashboard: {e}")
    
    # 5. Verificar estado de sesión con debug endpoint
    print("\n🔍 Verificando estado de sesión...")
    try:
        response = session.get(f"{BASE_URL}/debug-session-info")
        if response.status_code == 200:
            session_info = response.json()
            print("Estado de la sesión:")
            print(f"   - Autenticado: {session_info.get('is_authenticated', False)}")
            print(f"   - Usuario UID: {session_info.get('user_uid', 'No especificado')}")
            print(f"   - Timestamp login: {session_info.get('login_timestamp', 0)}")
            print(f"   - Edad sesión (horas): {session_info.get('session_age_hours', 0)}")
            print(f"   - Sesión válida: {session_info.get('session_valid', False)}")
        else:
            print(f"❌ Error obteniendo info de sesión: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verificando sesión: {e}")
    
    # 6. Prueba de navegación a otras páginas
    print("\n🧭 Probando navegación a otras páginas...")
    
    test_urls = [
        ("/crops/", "Gestión de cultivos"),
        ("/analytics/", "Analytics")
    ]
    
    for url, name in test_urls:
        try:
            response = session.get(f"{BASE_URL}{url}")
            status = "✅" if response.status_code == 200 else "⚠️" if response.status_code == 302 else "❌"
            print(f"   {status} {name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test de login completado")
    return True

if __name__ == "__main__":
    test_complete_login_flow()
