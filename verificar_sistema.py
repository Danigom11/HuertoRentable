#!/usr/bin/env python3
"""
Script para verificar el estado del sistema de peso promedio
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def verificar_estado_sistema():
    """Verifica el estado actual del sistema de peso promedio"""
    
    print("🔍 VERIFICACIÓN DEL SISTEMA DE PESO PROMEDIO")
    print("=" * 50)
    
    # Obtener cultivos actuales
    print("\n📊 Obteniendo cultivos actuales...")
    resp = requests.get(f"{BASE_URL}/api/crops")
    if resp.status_code != 200:
        print(f"❌ Error obteniendo cultivos: {resp.status_code}")
        return
    
    cultivos_data = resp.json()
    if 'crops' in cultivos_data:
        cultivos = cultivos_data['crops']
    else:
        cultivos = cultivos_data
    
    print(f"✅ {len(cultivos)} cultivos encontrados")
    
    if not cultivos:
        print("\n📝 No hay cultivos creados. Para probar el sistema:")
        print("1. Ve a http://127.0.0.1:5000/crops")
        print("2. Crea un nuevo cultivo")
        print("3. Asegúrate de incluir el peso promedio por unidad")
        print("4. Añade producción con solo unidades para ver el cálculo automático")
        return
    
    print("\n" + "=" * 50)
    print("RESUMEN DE CULTIVOS")
    print("=" * 50)
    
    for i, cultivo in enumerate(cultivos, 1):
        nombre = cultivo.get('nombre', 'Sin nombre')
        precio = cultivo.get('precio_por_kilo', 0)
        peso_promedio = cultivo.get('peso_promedio_gramos', 'No configurado')
        produccion = cultivo.get('produccion_diaria', [])
        
        print(f"\n{i}. CULTIVO: {nombre.upper()}")
        print(f"   💰 Precio por kilo: {precio}€")
        print(f"   ⚖️  Peso promedio por unidad: {peso_promedio}g")
        print(f"   📈 Registros de producción: {len(produccion)}")
        
        if produccion:
            print("   📋 Últimas producciones:")
            for j, prod in enumerate(produccion[-3:], 1):  # Últimas 3
                unidades = prod.get('unidades', 'N/A')
                kilos = prod.get('kilos', 'N/A')
                fecha = prod.get('fecha', 'N/A')
                print(f"      {j}. {unidades} unidades → {kilos} kg ({fecha})")
        
        # Calcular totales
        total_unidades = sum(p.get('unidades', 0) for p in produccion if 'unidades' in p)
        total_kilos = sum(p.get('kilos', 0) for p in produccion if 'kilos' in p)
        beneficio_total = total_kilos * precio
        
        print(f"   📊 TOTALES:")
        print(f"      🔢 Unidades totales: {total_unidades}")
        print(f"      ⚖️  Kilos totales: {total_kilos:.2f} kg")
        print(f"      💰 Beneficio total: {beneficio_total:.2f}€")
    
    print("\n" + "=" * 50)
    print("INSTRUCCIONES PARA PROBAR EL SISTEMA")
    print("=" * 50)
    print("\n1. 🌱 CREAR NUEVO CULTIVO CON PESO:")
    print("   - Ve a http://127.0.0.1:5000/crops")
    print("   - Haz clic en 'Nuevo Cultivo'")
    print("   - Completa todos los campos incluyendo 'Peso promedio por unidad'")
    print("   - Ejemplo: 150g para tomates, 50g para fresas, etc.")
    
    print("\n2. 📊 AÑADIR PRODUCCIÓN AUTOMÁTICA:")
    print("   - Ve al dashboard: http://127.0.0.1:5000/")
    print("   - En cualquier cultivo, introduce solo 'unidades'")
    print("   - El sistema calculará automáticamente los kilos")
    print("   - Ejemplo: 5 unidades de tomates (150g) = 0.75 kg")
    
    print("\n3. 🔍 VERIFICAR CÁLCULOS:")
    print("   - Los kilos se muestran inmediatamente")
    print("   - El beneficio se calcula como: kilos × precio_por_kilo")
    print("   - Usa el botón 'Deshacer' si necesitas corregir")
    
    print("\n4. 📈 VER HISTORIAL:")
    print("   - Usa el botón 'Ver Historial' en cualquier cultivo")
    print("   - Verás gráficas de producción por fecha")
    print("   - Lista completa de todas las producciones")
    
    print(f"\n🌟 Sistema listo en: {BASE_URL}")

if __name__ == "__main__":
    try:
        verificar_estado_sistema()
    except Exception as e:
        print(f"\n💥 Error durante la verificación: {e}")
