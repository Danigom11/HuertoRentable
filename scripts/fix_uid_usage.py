#!/usr/bin/env python3
"""
Script para limpiar uso inseguro de UID en funciones que ya tienen @require_auth
"""
import re

# Leer el archivo
with open('app/routes/crops.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patrones a reemplazar solo en funciones con @require_auth
patterns = [
    # Patrón para líneas que obtienen UID de forma insegura
    (
        r'(\s+)user = get_current_user\(\)\s*\n\s+uid = \(user or \{\}\)\.get\([\'"]uid[\'"].*?\n\s+if not uid:\s*\n\s+return jsonify\(\{[\'"]error[\'"].*?\}\), 401',
        r'\1# Obtener UID del usuario autenticado de forma segura\n\1user_uid = get_current_user_uid()\n\1user = get_current_user()'
    ),
    # Reemplazar referencias a uid por user_uid
    (r'\buid\b(?!\s*=)', 'user_uid'),
]

# Aplicar reemplazos
for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

# Escribir el archivo corregido
with open('app/routes/crops.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo crops.py actualizado con uso seguro de UID")
