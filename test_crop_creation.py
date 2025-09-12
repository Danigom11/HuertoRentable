#!/usr/bin/env python3
"""
Test de crear cultivo con autenticación
"""
import requests
import time

# Configuración
BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()

def test_login_and_crop():
    print("🧪 Test de login y creación de cultivo")
    
    # 1. Intentar hacer login local
    login_data = {
        'email': 'danigom11@gmail.com',
        'password': 'test123'
    }
    
    print("1️⃣ Intentando login...")
    response = session.post(f"{BASE_URL}/auth/login", data=login_data)
    print(f"   Status: {response.status_code}")
    print(f"   URL final: {response.url}")
    
    # Verificar si hay redirección
    if response.status_code == 302:
        print(f"   Redirigido a: {response.headers.get('Location', 'N/A')}")
    
    # 2. Verificar si podemos acceder a crops
    print("\n2️⃣ Intentando acceder a /crops...")
    response = session.get(f"{BASE_URL}/crops")
    print(f"   Status: {response.status_code}")
    print(f"   URL final: {response.url}")
    
    if response.status_code == 200:
        print("   ✅ Acceso exitoso a cultivos")
    else:
        print("   ❌ No se puede acceder a cultivos")
        return
    
    # 3. Intentar crear cultivo
    print("\n3️⃣ Intentando crear cultivo...")
    crop_data = {
        'nombre': 'Tomates Test',
        'precio': '3.50',
        'numero_plantas': '5',
        'peso_promedio': '150.0',
        'color_cultivo': '#28a745',
        'fecha_siembra': '2024-01-15'
    }
    
    response = session.post(f"{BASE_URL}/crops/create", data=crop_data)
    print(f"   Status: {response.status_code}")
    print(f"   URL final: {response.url}")
    
    if response.status_code == 302:
        print(f"   Redirigido a: {response.headers.get('Location', 'N/A')}")
    
    # 4. Verificar si el cultivo se creó
    print("\n4️⃣ Verificando si se creó el cultivo...")
    response = session.get(f"{BASE_URL}/crops")
    if "Tomates Test" in response.text:
        print("   ✅ Cultivo creado exitosamente")
    else:
        print("   ❌ Cultivo no encontrado")

if __name__ == "__main__":
    test_login_and_crop()
