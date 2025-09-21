import requests

BASE = 'http://127.0.0.1:5000'
s = requests.Session()

print('1) POST /auth/test-session-flow')
r1 = s.post(f'{BASE}/auth/test-session-flow', json={'ok': True}, allow_redirects=False)
print('status:', r1.status_code)
print('cookies:', s.cookies.get_dict())

print('\n2) POST /crops/create con campos completos')
form = {
    'nombre': 'tomates_full',
    'precio': '2.5',
    'numero_plantas': '10',
    'peso_promedio': '120'
}
r2 = s.post(f'{BASE}/crops/create', data=form, allow_redirects=False)
print('status:', r2.status_code, 'location:', r2.headers.get('Location'))

print('\n3) GET /crops/ (seguir redirección)')
r3 = s.get(f'{BASE}/crops/', allow_redirects=True)
print('final status:', r3.status_code)
print('final url:', r3.url)
print('contains tomates_full:', 'tomates_full' in r3.text)
