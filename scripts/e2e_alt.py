import requests
import sys

BASE = 'http://127.0.0.1:5000'
s = requests.Session()

def log(step, resp):
    ct = resp.headers.get('content-type','')
    print(f'[{step}] status={resp.status_code} url={resp.url}')
    print(' cookies:', s.cookies.get_dict())
    if 'application/json' in ct:
        try:
            print(' json keys:', list(resp.json().keys()))
        except Exception:
            print(' json parse error')
    else:
        print(' body preview:', resp.text[:200].replace('\n',' '))

try:
    r1 = s.post(f'{BASE}/auth/test-session-flow', json={'run':'yes'})
    log('1 POST /auth/test-session-flow', r1)
except Exception as e:
    print('ERROR in step 1:', e)
    sys.exit(1)

try:
    r2 = s.get(f'{BASE}/dashboard', allow_redirects=False)
    log('2 GET /dashboard', r2)
except Exception as e:
    print('ERROR in step 2:', e)
    sys.exit(1)

form = {
  'nombre': 'tomates_test',
  'precio': '3.5',
  'numero_plantas': '7'
}
try:
    r3 = s.post(f'{BASE}/crops/create', data=form, allow_redirects=False)
    log('3 POST /crops/create', r3)
except Exception as e:
    print('ERROR in step 3:', e)
    sys.exit(1)

try:
    r4 = s.get(f'{BASE}/crops/api/user-crops')
    log('4 GET /crops/api/user-crops', r4)
    print('4 JSON:', r4.json())
except Exception as e:
    print('ERROR in step 4:', e)
    sys.exit(1)

print('Done.')
