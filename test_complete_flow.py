#!/usr/bin/env python3
"""
Test automatizado COMPLETO del flujo de registro y dashboard
"""
import requests
import json
import time

def test_complete_registration_flow():
    """Test completo del flujo de registro hasta dashboard"""
    print("🧪 TEST COMPLETO DEL FLUJO DE REGISTRO")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5000"
    
    # Crear una sesión de requests para mantener cookies
    session = requests.Session()
    
    print("1️⃣ Obteniendo página de registro...")
    try:
        response = session.get(f"{base_url}/auth/register?plan=gratuito")
        print(f"   Status: {response.status_code}")
        print(f"   Cookies iniciales: {dict(session.cookies)}")
        
        if response.status_code != 200:
            print(f"❌ Error obteniendo página: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n2️⃣ Simulando registro (sin Firebase real)...")
    # Usar el endpoint de test que simula registro completo
    try:
        response = session.post(f"{base_url}/auth/test-session-flow", 
                               json={'test': 'registration_simulation'})
        print(f"   Status: {response.status_code}")
        print(f"   Cookies después de test: {dict(session.cookies)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Test sesión: {data.get('success', False)}")
            print(f"   📝 Sesión creada: {data.get('session_created', {})}")
        else:
            print(f"   ❌ Error en test: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n3️⃣ Accediendo al dashboard...")
    try:
        response = session.get(f"{base_url}/dashboard", allow_redirects=False)
        print(f"   Status: {response.status_code}")
        print(f"   Cookies enviadas: {dict(session.cookies)}")
        
        if response.status_code == 200:
            print("   ✅ Dashboard accesible directamente")
            return True
        elif response.status_code == 302:
            location = response.headers.get('Location', 'No location header')
            print(f"   ❌ Redirección a: {location}")
            return False
        else:
            print(f"   ❌ Error inesperado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_simple_session_flow():
    """Test del flujo de sesión simple"""
    print("\n🧪 TEST DE SESIÓN SIMPLE")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    print("1️⃣ Creando sesión simple...")
    try:
        response = session.post(f"{base_url}/auth/test-simple-session", 
                               data={'test_value': 'prueba_automatizada'})
        print(f"   Status: {response.status_code}")
        print(f"   Cookies: {dict(session.cookies)}")
        
        if response.status_code != 200:
            print(f"   ❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n2️⃣ Verificando persistencia...")
    try:
        response = session.get(f"{base_url}/auth/test-check-session")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            if 'prueba_automatizada' in response.text:
                print("   ✅ Sesión persiste")
                return True
            else:
                print("   ❌ Sesión no persiste")
                return False
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_dashboard_direct():
    """Test acceso directo al dashboard sin sesión"""
    print("\n🧪 TEST DASHBOARD SIN SESIÓN")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    try:
        response = session.get(f"{base_url}/dashboard", allow_redirects=False)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', 'No location')
            print(f"Redirige a: {location}")
            if 'login' in location.lower():
                print("✅ Comportamiento correcto: redirige a login sin sesión")
            elif 'onboarding' in location.lower():
                print("⚠️ Redirige a onboarding (podría ser correcto)")
            else:
                print("❓ Redirección inesperada")
        elif response.status_code == 200:
            print("❓ Dashboard accesible sin sesión (modo demo?)")
        else:
            print(f"❌ Error inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO BATERÍA COMPLETA DE TESTS")
    print("=" * 70)
    
    # Test 1: Sesión simple
    test1_result = test_simple_session_flow()
    
    # Test 2: Dashboard sin sesión
    test_dashboard_direct()
    
    # Test 3: Flujo completo de registro
    test3_result = test_complete_registration_flow()
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE RESULTADOS:")
    print(f"   Sesión simple: {'✅' if test1_result else '❌'}")
    print(f"   Registro completo: {'✅' if test3_result else '❌'}")
    
    if test1_result and test3_result:
        print("\n✅ TODOS LOS TESTS PASARON - SISTEMA FUNCIONANDO")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON - REVISAR CONFIGURACIÓN")
    print("=" * 70)
