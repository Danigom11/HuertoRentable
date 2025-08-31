#!/usr/bin/env python3
"""
Test automatizado para verificar que las sesiones persisten correctamente
"""
import requests
import json
import time

def test_session_persistence():
    """Test la persistencia de sesiones entre requests"""
    print("🧪 TESTING SESSION PERSISTENCE")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    
    # Crear una sesión de requests para mantener cookies
    session = requests.Session()
    
    # Test 1: Crear sesión con test-simple-session
    print("1️⃣ Creando sesión de test...")
    try:
        response = session.post(f"{base_url}/auth/test-simple-session", 
                               data={'test_value': 'valor_prueba_123'})
        print(f"   Status: {response.status_code}")
        print(f"   Cookies recibidas: {list(session.cookies.keys())}")
        
        if response.status_code != 200:
            print(f"❌ Error creando sesión: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en request: {e}")
        return False
    
    # Test 2: Verificar sesión persiste
    print("\n2️⃣ Verificando persistencia de sesión...")
    try:
        response = session.get(f"{base_url}/auth/test-check-session")
        print(f"   Status: {response.status_code}")
        print(f"   Cookies enviadas: {list(session.cookies.keys())}")
        
        if response.status_code == 200:
            if 'valor_prueba_123' in response.text:
                print("   ✅ Sesión persiste correctamente")
                return True
            else:
                print("   ❌ Sesión no contiene los datos esperados")
                print(f"   Contenido: {response.text[:200]}...")
                return False
        else:
            print(f"   ❌ Error verificando sesión: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando sesión: {e}")
        return False

def test_dashboard_access():
    """Test acceso al dashboard tras crear sesión"""
    print("\n🧪 TESTING DASHBOARD ACCESS")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    # Usar endpoint de test que crea sesión completa
    print("1️⃣ Creando sesión completa...")
    try:
        response = session.post(f"{base_url}/auth/test-session-flow", 
                               json={'test': 'value'})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Sesión creada: {data.get('success', False)}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Acceder al dashboard
    print("\n2️⃣ Accediendo al dashboard...")
    try:
        response = session.get(f"{base_url}/dashboard")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Dashboard accesible")
            return True
        elif response.status_code == 302:
            print(f"   ⚠️ Redirección a: {response.headers.get('Location')}")
            return False
        else:
            print(f"   ❌ Error accediendo: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DE SESIÓN")
    print("=" * 60)
    
    # Test básico de persistencia
    test1_result = test_session_persistence()
    
    # Test de acceso al dashboard
    test2_result = test_dashboard_access()
    
    print("\n" + "=" * 60)
    if test1_result and test2_result:
        print("✅ TODOS LOS TESTS PASARON - SESIONES FUNCIONANDO")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print(f"   Test persistencia: {'✅' if test1_result else '❌'}")
        print(f"   Test dashboard: {'✅' if test2_result else '❌'}")
    print("=" * 60)
