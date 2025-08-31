import requests, sys

BASE = 'http://127.0.0.1:5000'
s = requests.Session()

print('1) POST /auth/test-session-flow (crear sesión de prueba)')
r = s.post(f'{BASE}/auth/test-session-flow', json={'run':'yes'})
print('status:', r.status_code)
print('cookies:', s.cookies.get_dict())
print('body keys:', list(r.json().keys()) if r.headers.get('content-type','').startswith('application/json') else 'no-json')

print('\n2) GET /dashboard (comprobar acceso)')
r2 = s.get(f'{BASE}/dashboard', allow_redirects=False)
print('status:', r2.status_code, 'location:', r2.headers.get('Location'))

print('\n3) POST /crops/create (crear cultivo)')
form = {
  'nombre': 'tomates_test',
  'precio': '3.5',
  'numero_plantas': '7'
}
r3 = s.post(f'{BASE}/crops/create', data=form, allow_redirects=False)
print('status:', r3.status_code, 'location:', r3.headers.get('Location'))

print('\n4) GET /crops/api/user-crops (listar cultivos del usuario)')
r4 = s.get(f'{BASE}/crops/api/user-crops')
print('status:', r4.status_code)
print('json:', r4.json())

print('\nDone.')
