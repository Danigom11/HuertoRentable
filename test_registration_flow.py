#!/usr/bin/env python3
"""
Test completo del flujo de registro de HuertoRentable
Simula el comportamiento real del navegador paso a paso
"""

import requests
import json
import uuid
import time
from datetime import datetime

# Configuración
BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()

def log_step(step, message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {step}: {message}")

def log_cookies(step):
    print(f"  🍪 Cookies después de {step}:")
    for cookie in session.cookies:
        print(f"    {cookie.name}={cookie.value[:20]}...")

def test_home_page():
    """Prueba 1: Acceder a la página principal"""
    log_step("1", "Accediendo a página principal...")
    
    response = session.get(f"{BASE_URL}/")
    
    print(f"  Status: {response.status_code}")
    print(f"  Redirección final: {response.url}")
    
    log_cookies("home")
    
    # Verificar que nos lleva al login/onboarding
    assert response.status_code == 200
    return response

def test_registration_page():
    """Prueba 2: Acceder a página de registro"""
    log_step("2", "Accediendo a página de registro...")
    
    response = session.get(f"{BASE_URL}/auth/register")
    
    print(f"  Status: {response.status_code}")
    print(f"  Tiene formulario: {'form' in response.text}")
    
    log_cookies("register_page")
    
    assert response.status_code == 200
    return response

def test_user_registration():
    """Prueba 3: Registrar un nuevo usuario"""
    log_step("3", "Registrando nuevo usuario...")
    
    # Generar datos únicos
    timestamp = int(time.time())
    email = f"test.{timestamp}@huerto.com"
    password = "password123"
    
    # Datos del formulario
    form_data = {
        'email': email,
        'password': password,
        'confirm_password': password,
        'name': f'Usuario Test {timestamp}'
    }
    
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    
    # Hacer POST al endpoint de registro
    response = session.post(
        f"{BASE_URL}/auth/register",
        data=form_data,
        allow_redirects=False  # Importante: no seguir redirects automáticamente
    )
    
    print(f"  Status: {response.status_code}")
    print(f"  Headers: {dict(response.headers)}")
    
    # Si es JSON response
    if response.headers.get('content-type', '').startswith('application/json'):
        try:
            data = response.json()
            print(f"  JSON Response: {data}")
            
            if data.get('success'):
                redirect_url = data.get('redirect_url')
                print(f"  Redirect URL: {redirect_url}")
                return redirect_url, email, password
            else:
                print(f"  Error: {data.get('error')}")
                return None, email, password
        except:
            print(f"  No es JSON válido")
    
    # Si es redirect HTML
    if 300 <= response.status_code < 400:
        redirect_url = response.headers.get('Location')
        print(f"  Redirect Location: {redirect_url}")
        return redirect_url, email, password
    
    print(f"  Response Text (primeros 200 chars): {response.text[:200]}")
    
    log_cookies("after_registration")
    
    return None, email, password

def test_post_registration_redirect(redirect_url, email, password):
    """Prueba 4: Seguir el redirect después del registro"""
    if not redirect_url:
        log_step("4", "❌ No hay URL de redirect, saltando...")
        return None
    
    log_step("4", f"Siguiendo redirect a: {redirect_url}")
    
    # Hacer GET al redirect URL
    full_url = f"{BASE_URL}{redirect_url}" if redirect_url.startswith('/') else redirect_url
    
    response = session.get(full_url, allow_redirects=False)
    
    print(f"  Status: {response.status_code}")
    print(f"  URL final: {response.url if hasattr(response, 'url') else 'N/A'}")
    
    # Si hay otro redirect
    if 300 <= response.status_code < 400:
        next_redirect = response.headers.get('Location')
        print(f"  Nuevo redirect: {next_redirect}")
        
        if next_redirect:
            full_next_url = f"{BASE_URL}{next_redirect}" if next_redirect.startswith('/') else next_redirect
            response = session.get(full_next_url)
            print(f"  Status final: {response.status_code}")
    
    print(f"  Página contiene 'dashboard': {'dashboard' in response.text.lower()}")
    print(f"  Página contiene 'login': {'login' in response.text.lower()}")
    print(f"  Página contiene 'onboarding': {'onboarding' in response.text.lower()}")
    
    log_cookies("after_redirect")
    
    return response

def test_direct_dashboard_access():
    """Prueba 5: Intentar acceder directamente al dashboard"""
    log_step("5", "Intentando acceso directo al dashboard...")
    
    response = session.get(f"{BASE_URL}/dashboard", allow_redirects=False)
    
    print(f"  Status: {response.status_code}")
    
    if 300 <= response.status_code < 400:
        redirect_location = response.headers.get('Location')
        print(f"  Redirected to: {redirect_location}")
        
        # Seguir el redirect
        if redirect_location:
            full_url = f"{BASE_URL}{redirect_location}" if redirect_location.startswith('/') else redirect_location
            final_response = session.get(full_url)
            print(f"  Final status: {final_response.status_code}")
            print(f"  Final URL: {final_response.url if hasattr(final_response, 'url') else 'N/A'}")
            return final_response
    
    log_cookies("dashboard_access")
    
    return response

def test_session_debug():
    """Prueba 6: Endpoint de debug de sesión"""
    log_step("6", "Verificando estado de sesión...")
    
    response = session.get(f"{BASE_URL}/debug/session")
    
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"  Session data: {json.dumps(data, indent=2)}")
        except:
            print(f"  Response: {response.text}")
    
    return response

def main():
    print("🧪 Iniciando test completo del flujo de registro")
    print("=" * 60)
    
    try:
        # Paso 1: Página principal
        home_response = test_home_page()
        
        # Paso 2: Página de registro
        register_response = test_registration_page()
        
        # Paso 3: Registrar usuario
        redirect_url, email, password = test_user_registration()
        
        # Paso 4: Seguir redirect
        final_response = test_post_registration_redirect(redirect_url, email, password)
        
        # Paso 5: Acceso directo al dashboard
        dashboard_response = test_direct_dashboard_access()
        
        # Paso 6: Debug de sesión
        session_response = test_session_debug()
        
        print("\n" + "=" * 60)
        print("🎯 RESUMEN DE RESULTADOS:")
        print(f"  Usuario creado: {email}")
        print(f"  Redirect después del registro: {redirect_url}")
        
        if final_response:
            es_dashboard = 'dashboard' in final_response.text.lower()
            es_login = 'login' in final_response.text.lower()
            es_onboarding = 'onboarding' in final_response.text.lower()
            
            print(f"  Página final es dashboard: {es_dashboard}")
            print(f"  Página final es login: {es_login}")
            print(f"  Página final es onboarding: {es_onboarding}")
            
            if es_dashboard:
                print("  ✅ ÉXITO: Usuario llega al dashboard")
            elif es_login:
                print("  ❌ FALLO: Usuario enviado al login")
            elif es_onboarding:
                print("  ❌ FALLO: Usuario enviado al onboarding")
            else:
                print("  ❓ DESCONOCIDO: Página no identificada")
        
        print("\n🍪 Estado final de cookies:")
        for cookie in session.cookies:
            print(f"  {cookie.name}: {cookie.value}")
        
    except Exception as e:
        print(f"\n❌ Error durante el test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
