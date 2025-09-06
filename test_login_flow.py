#!/usr/bin/env python3
"""
Script para probar el flujo completo de login y navegación
"""
import requests
import json
import time

base_url = "http://127.0.0.1:5000"

def test_complete_flow():
    session = requests.Session()
    
    print("=== Test de Flujo Completo de Login ===")
    
    # 1. Ir a login y obtener página
    print("\n1. Accediendo a login...")
    resp = session.get(f"{base_url}/auth/login")
    print(f"Status: {resp.status_code}")
    print(f"URL: {resp.url}")
    
    # 2. Simular login con datos Firebase válidos (temporal para testing)
    print("\n2. Simulando login...")
    login_data = {
        'uid': 'test_user_12345',
        'email': 'test@example.com',
        'name': 'Usuario de Prueba',
        'plan': 'gratuito',
        'email_verified': True
    }
    
    resp = session.post(f"{base_url}/auth/sync-user", 
                       json=login_data,
                       headers={'Content-Type': 'application/json'})
    print(f"Login status: {resp.status_code}")
    print(f"Login response: {resp.text[:200]}...")
    
    # 3. Verificar que dashboard sea accesible
    print("\n3. Accediendo a dashboard después del login...")
    resp = session.get(f"{base_url}/dashboard")
    print(f"Dashboard status: {resp.status_code}")
    print(f"Dashboard URL: {resp.url}")
    
    if resp.status_code == 200:
        print("✅ LOGIN EXITOSO: Dashboard accesible")
    else:
        print("❌ LOGIN FALLÓ: Dashboard no accesible")
    
    # 4. Probar navegación a cultivos
    print("\n4. Accediendo a cultivos...")
    resp = session.get(f"{base_url}/crops")
    print(f"Crops status: {resp.status_code}")
    print(f"Crops URL: {resp.url}")
    
    # 5. Probar navegación a analytics
    print("\n5. Accediendo a analytics...")
    resp = session.get(f"{base_url}/analytics")
    print(f"Analytics status: {resp.status_code}")
    print(f"Analytics URL: {resp.url}")
    
    # 6. Verificar cookies después del login
    print(f"\n6. Cookies finales: {dict(session.cookies)}")

if __name__ == "__main__":
    test_complete_flow()
