#!/usr/bin/env python3
"""
Test del flujo completo de autenticación
Simula un registro real para verificar que las sesiones persisten
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_authentication_flow():
    """Test completo del flujo de autenticación"""
    
    print("🧪 TEST DE FLUJO DE AUTENTICACIÓN")
    print("=" * 50)
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    # 1. Obtener página de registro
    print("1️⃣ Solicitando página de registro...")
    try:
        response = session.get(f"{BASE_URL}/auth/register?plan=premium")
        print(f"   Status: {response.status_code}")
        print(f"   Cookies recibidas: {list(response.cookies.keys())}")
        
        if response.status_code != 200:
            print(f"❌ Error obteniendo página de registro: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        return False
    
    # 2. Simular registro con token ficticio
    print("\n2️⃣ Simulando registro con token Firebase...")
    
    # Token ficticio para simular Firebase (en la vida real vendría del frontend)
    fake_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMzQ1IiwidHlwIjoiSldUIn0.TEST_TOKEN"
    
    register_data = {
        "idToken": fake_token,
        "plan": "premium"
    }
    
    try:
        response = session.post(
            f"{BASE_URL}/auth/register",
            json=register_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Cookies enviadas: {list(session.cookies.keys())}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Registro exitoso: {data.get('message', 'Sin mensaje')}")
            
            # Verificar cookies de sesión
            if session.cookies:
                print(f"   🍪 Cookies en sesión: {list(session.cookies.keys())}")
            else:
                print(f"   ⚠️ No hay cookies en la sesión")
        else:
            print(f"   ❌ Error en registro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en registro: {e}")
        return False
    
    # 3. Verificar acceso al dashboard con las cookies
    print("\n3️⃣ Verificando acceso al dashboard...")
    
    try:
        response = session.get(f"{BASE_URL}/dashboard")
        print(f"   Status: {response.status_code}")
        print(f"   Cookies enviadas: {list(session.cookies.keys())}")
        
        if response.status_code == 200:
            print(f"   ✅ Dashboard accesible")
            # Verificar contenido del dashboard
            if "panel de control" in response.text.lower() or "dashboard" in response.text.lower():
                print(f"   ✅ Contenido del dashboard correcto")
                return True
            else:
                print(f"   ⚠️ Dashboard accesible pero contenido inesperado")
                return False
        else:
            print(f"   ❌ Dashboard no accesible: {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error accediendo al dashboard: {e}")
        return False

def test_session_endpoint():
    """Test específico del endpoint de sesión"""
    print("\n🧪 TEST ESPECÍFICO DE SESIÓN")
    print("=" * 50)
    
    session = requests.Session()
    
    try:
        response = session.get(f"{BASE_URL}/auth/session-info")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Información de sesión: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DE AUTENTICACIÓN")
    print("=" * 60)
    
    # Test 1: Flujo completo
    success = test_authentication_flow()
    
    # Test 2: Información de sesión
    test_session_endpoint()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TODOS LOS TESTS PASARON - AUTENTICACIÓN FUNCIONAL")
    else:
        print("❌ TESTS FALLARON - REVISAR CONFIGURACIÓN")
    print("=" * 60)
