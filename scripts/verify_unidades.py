import re
import sys
import time
from datetime import datetime

import requests


BASE = "http://127.0.0.1:5000"


def log(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main():
    s = requests.Session()

    # 1) Crear una sesión de prueba en el backend
    r = s.post(f"{BASE}/auth/test-session-flow")
    r.raise_for_status()
    log(f"test-session-flow: {r.status_code} -> {r.json().get('message','')} ")

    # 2) Crear un cultivo nuevo
    nombre = f"prueba-unidades-{int(time.time())}"
    r = s.post(
        f"{BASE}/api/crops",
        json={"nombre": nombre, "precio": 1.5},
        allow_redirects=False,
    )
    r.raise_for_status()
    log(f"create crop: {r.status_code} -> {r.json()}")

    # 3) Listar cultivos y obtener el ID del cultivo recién creado
    r = s.get(f"{BASE}/api/crops")
    r.raise_for_status()
    data = r.json()
    crops = data.get("crops", [])
    crop = next((c for c in crops if c.get("nombre") == nombre), None)
    if not crop:
        raise SystemExit("No se encontró el cultivo creado en /api/crops")
    crop_id = crop.get("id")
    log(f"crop_id: {crop_id}")

    # 4) Añadir 5 unidades a la producción usando la ruta HTML (form-urlencoded)
    r = s.post(
        f"{BASE}/crops/{crop_id}/production",
        data={"unidades": 5},
        allow_redirects=False,
    )
    log(f"add unidades (expect 302/303): {r.status_code}")

    # 5) Consultar el dashboard y verificar que aparezcan 5 unidades en el bloque del cultivo
    r = s.get(f"{BASE}/dashboard", allow_redirects=True)
    r.raise_for_status()
    html = r.text

    # Buscar el bloque del cultivo por nombre y extraer el número de unidades cercano
    # Estrategia: encontrar el índice del nombre y luego, en una ventana de 800 chars, buscar 'unidades' seguido de un número
    idx = html.lower().find(nombre.lower())
    if idx == -1:
        raise SystemExit("El dashboard no contiene el nombre del cultivo creado")

    window = html[idx : idx + 2000]
    # Extraer específicamente el valor numérico que precede al label "Unidades"
    # Estructura en el template:
    # <div class="fw-bold text-warning h5 mb-0"> N </div>
    # <small class="text-muted">Unidades</small>
    m = re.search(
        r"<div[^>]*class=\"fw-bold[^\"]*\">\s*([0-9]+)\s*</div>\s*<small[^>]*>\s*Unidades\s*</small>",
        window,
        re.IGNORECASE | re.DOTALL,
    )
    unidades_val = int(m.group(1)) if m else None
    log(f"unidades encontradas en dashboard: {unidades_val}")

    ok = unidades_val == 5
    print({
        "nombre": nombre,
        "crop_id": crop_id,
        "unidades_dashboard": unidades_val,
        "ok": ok,
        "timestamp": datetime.utcnow().isoformat(),
    })
    if not ok:
        raise SystemExit("Las unidades no coinciden con 5")


if __name__ == "__main__":
    main()
