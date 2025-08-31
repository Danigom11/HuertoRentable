import requests
import time
import json

# Test básico de conectividad
print("🧪 Test básico de conectividad")

try:
    response = requests.get("http://127.0.0.1:5000/", timeout=5)
    print(f"✅ Servidor responde: {response.status_code}")
    print(f"📄 Contenido: {response.text[:100]}...")
    
    # Test del endpoint de registro
    print("\n🧪 Test de página de registro")
    reg_response = requests.get("http://127.0.0.1:5000/auth/register", timeout=5)
    print(f"✅ Página registro: {reg_response.status_code}")
    
    # Test con datos de formulario
    print("\n🧪 Test de envío de formulario")
    session = requests.Session()
    
    # Primero ir a la página de registro para obtener cookies
    session.get("http://127.0.0.1:5000/auth/register")
    
    form_data = {
        'email': f'test.{int(time.time())}@huerto.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'name': 'Usuario Test'
    }
    
    print(f"📧 Email: {form_data['email']}")
    
    post_response = session.post(
        "http://127.0.0.1:5000/auth/register", 
        data=form_data,
        timeout=10
    )
    
    print(f"✅ POST registro: {post_response.status_code}")
    print(f"📍 URL final: {post_response.url}")
    print(f"🔄 Historial redirects: {[r.url for r in post_response.history]}")
    
    if post_response.headers.get('content-type', '').startswith('application/json'):
        print(f"📝 JSON Response: {post_response.json()}")
    else:
        print(f"📄 HTML Response: {'dashboard' in post_response.text.lower()}")
    
    print(f"🍪 Cookies: {session.cookies}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
