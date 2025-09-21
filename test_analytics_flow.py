#!/usr/bin/env python3
"""
Prueba de sesión al navegar a Analytics y su API sin cierre de sesión.
"""
import requests

BASE = "http://127.0.0.1:5000"

s = requests.Session()

print("1) Crear sesión completa de test (/auth/test-session-flow)")
r = s.post(f"{BASE}/auth/test-session-flow", json={"test": True})
print("   Status:", r.status_code)
print("   Cookies:", list(s.cookies.keys()))

print("2) Ir a /analytics/")
r = s.get(f"{BASE}/analytics/")
print("   Status:", r.status_code)
print("   URL final:", r.url)
print("   Location:", r.headers.get("Location"))

print("3) Llamar /analytics/api/chart-data")
r = s.get(f"{BASE}/analytics/api/chart-data", headers={"Accept": "application/json"})
print("   Status:", r.status_code)
print("   JSON?", r.headers.get("Content-Type"))
print("   Body (inicio):", r.text[:120])

print("4) Ir a /crops/")
r = s.get(f"{BASE}/crops/")
print("   Status:", r.status_code)
print("   URL final:", r.url)
print("   Location:", r.headers.get("Location"))
