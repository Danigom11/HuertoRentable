#!/usr/bin/env python3
"""
Script para verificar problemas de sesión y timestamps
"""
import time
from datetime import datetime

# Verificar timestamp actual
current_timestamp = int(time.time())
current_datetime = datetime.fromtimestamp(current_timestamp)

print(f"Timestamp actual: {current_timestamp}")
print(f"Fecha actual: {current_datetime}")
print(f"Año: {current_datetime.year}")

# Verificar el timestamp problemático que vimos en los logs
problematic_timestamp = 1757015058
problematic_datetime = datetime.fromtimestamp(problematic_timestamp)

print(f"\nTimestamp problemático: {problematic_timestamp}")
print(f"Fecha problemática: {problematic_datetime}")
print(f"Año problemático: {problematic_datetime.year}")

# Calcular diferencia
diff_seconds = problematic_timestamp - current_timestamp
diff_years = diff_seconds / (365.25 * 24 * 3600)

print(f"\nDiferencia: {diff_seconds} segundos")
print(f"Diferencia: {diff_years:.1f} años en el futuro")

# Verificar validez de sesión con 24h de límite
session_age_hours = (current_timestamp - problematic_timestamp) / 3600
print(f"\nEdad de sesión: {session_age_hours:.1f} horas")
print(f"¿Sesión válida? {session_age_hours < 24}")
