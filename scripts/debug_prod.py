import sys
import requests


BASE = "https://huerto-rentable.web.app"


def main():
    s = requests.Session()

    def log(label, r):
        try:
            sc = ", ".join([f"{k}={v[:20]}" for k, v in s.cookies.get_dict(domain="huerto-rentable.web.app").items()])
        except Exception:
            sc = str(s.cookies.get_dict())
        loc = r.headers.get("Location")
        ct = r.headers.get("Content-Type")
        print(f"{label}: {r.status_code} loc={loc} ct={ct} cookies=[{sc}]")

    # 1) Crear sesión de prueba
    r1 = s.post(f"{BASE}/auth/test-session-flow", json={"test": True}, allow_redirects=False)
    print("SET-COOKIE:", r1.headers.get("Set-Cookie"))
    log("STEP1 /auth/test-session-flow", r1)

    # 2) Verificar estado de sesión (HTML)
    r2 = s.get(f"{BASE}/auth/test-check-session", allow_redirects=False)
    log("STEP2 /auth/test-check-session", r2)
    if r2.text:
        print("CHECK body start:", r2.text[:160].replace("\n", " "))

    # 2b) Dashboard HTML real y enlace a Editar Cultivos
    # Importante: en Firebase Hosting, "/" sirve un index estático; el dashboard dinámico está en "/dashboard".
    rD = s.get(f"{BASE}/dashboard", allow_redirects=False)
    log("STEP2b /dashboard (dashboard)", rD)
    dash_html = rD.text or ""
    # Buscar enlace hacia /crops/ con posible uid en la query
    import re as _re
    m = _re.search(r"href=\"(/crops/[^\"]*)\"", dash_html)
    crops_href = m.group(1) if m else None
    print("DASH crops href:", crops_href)
    if crops_href:
        # Simular click al enlace del dashboard
        rD2 = s.get(f"{BASE}{crops_href}", allow_redirects=False)
        log("STEP2c GET enlace dashboard→crops", rD2)
    else:
        # Mostrar un trozo del HTML para diagnóstico rápido
        preview = dash_html[:300].replace("\n", " ")
        print("DASH html preview:", preview)

    # 3) /analytics/ UI
    r3 = s.get(f"{BASE}/analytics/", allow_redirects=False)
    log("STEP3 /analytics/", r3)

    # 4) API JSON
    r4 = s.get(f"{BASE}/analytics/api/chart-data", headers={"Accept": "application/json"}, allow_redirects=False)
    log("STEP4 /analytics/api/chart-data", r4)
    if r4.text:
        print("API body start:", r4.text[:160])

    # 5) /crops/
    r5 = s.get(f"{BASE}/crops/", allow_redirects=False)
    log("STEP5 /crops/", r5)

    # 6) Echo cookies desde backend
    r6 = s.post(f"{BASE}/auth/test-cookie-simple", allow_redirects=False)
    log("STEP6 /auth/test-cookie-simple", r6)
    try:
        print("ECHO cookies recibidas:", r6.json().get("received_cookies"))
    except Exception:
        print("ECHO body:", r6.text[:200].replace("\n", " "))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
            print("ERROR:", e)
            sys.exit(1)
