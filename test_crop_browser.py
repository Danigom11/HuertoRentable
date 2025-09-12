#!/usr/bin/env python3
"""
Test completo de creación de cultivos en navegador con autenticación de desarrollo
"""
import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def test_crop_creation_with_dev_auth():
    """Test de creación de cultivos usando autenticación de desarrollo"""
    session = requests.Session()
    
    print("🔧 Testing crop creation with dev authentication...")
    
    # 1. Primero autenticarse con el token de desarrollo
    print("1. Autenticando con dev_token...")
    response = session.get(f"{BASE_URL}/crops?dev_token=dev_123_local")
    print(f"   Crops page status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Error accediendo a crops: {response.status_code}")
        return False
    
    # 2. Crear un cultivo usando el formulario
    print("2. Creando cultivo 'Tomates Browser Test'...")
    form_data = {
        'nombre': 'Tomates Browser Test',
        'tipo': 'fruto',
        'fecha_siembra': '2025-01-15',
        'precio_por_kilo': '2.50'
    }
    
    response = session.post(f"{BASE_URL}/crops/create", data=form_data)
    print(f"   Creation response: {response.status_code}")
    print(f"   Response URL: {response.url}")
    
    if response.status_code == 302:
        print("✅ Cultivo creado exitosamente (redirect)")
    elif response.status_code == 200:
        print("✅ Cultivo creado exitosamente")
    else:
        print(f"❌ Error creando cultivo: {response.status_code}")
        print(f"Response content: {response.text[:500]}")
        return False
    
    # 3. Verificar que el cultivo aparece en la lista
    print("3. Verificando que el cultivo aparece en la lista...")
    response = session.get(f"{BASE_URL}/crops/")
    if "Tomates Browser Test" in response.text:
        print("✅ Cultivo aparece en la lista!")
        return True
    else:
        print("❌ Cultivo no aparece en la lista")
        return False

def test_dashboard_access():
    """Test de acceso al dashboard con dev auth"""
    session = requests.Session()
    
    print("\n🏠 Testing dashboard access...")
    response = session.get(f"{BASE_URL}/dashboard?dev_token=dev_123_local")
    print(f"Dashboard status: {response.status_code}")
    
    if response.status_code == 200 and "HuertoRentable" in response.text:
        print("✅ Dashboard accesible con dev auth")
        return True
    else:
        print("❌ Dashboard no accesible")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando tests de navegador con autenticación de desarrollo\n")
    
    # Dar tiempo para que Flask arranque
    time.sleep(2)
    
    success = True
    
    try:
        success &= test_dashboard_access()
        success &= test_crop_creation_with_dev_auth()
    except Exception as e:
        print(f"❌ Error en tests: {e}")
        success = False
    
    print(f"\n{'🎉 TODOS LOS TESTS PASARON' if success else '❌ ALGUNOS TESTS FALLARON'}")
