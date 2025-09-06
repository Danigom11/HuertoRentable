#!/usr/bin/env python3
"""
Script para probar el flujo de login y detección de problemas de sesión
"""
import requests
import time

base_url = "http://127.0.0.1:5000"

def test_session_flow():
    session = requests.Session()
    
    print("=== Test de Flujo de Sesión ===")
    
    # 1. Verificar estado inicial
    print("\n1. Verificando estado inicial...")
    resp = session.get(f"{base_url}/")
    print(f"Status: {resp.status_code}")
    print(f"URL final: {resp.url}")
    print(f"Cookies recibidas: {dict(session.cookies)}")
    
    # 2. Ir a login
    print("\n2. Accediendo a página de login...")
    resp = session.get(f"{base_url}/auth/login")
    print(f"Status: {resp.status_code}")
    print(f"URL: {resp.url}")
    
    # 3. Verificar si hay sesión activa persistente
    print("\n3. Verificando si hay sesión persistente...")
    resp = session.get(f"{base_url}/dashboard")
    print(f"Status: {resp.status_code}")
    print(f"URL final: {resp.url}")
    
    if resp.status_code == 200:
        print("⚠️ PROBLEMA: Dashboard accesible sin login!")
        print("Esto indica que hay una sesión antigua que no se está limpiando correctamente")
    else:
        print("✅ Dashboard no accesible sin login (correcto)")

if __name__ == "__main__":
    test_session_flow()
