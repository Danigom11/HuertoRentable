#!/usr/bin/env python3
"""
Script de prueba para verificar el historial del cultivo
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_historial_cultivo():
    """Prueba el historial de un cultivo específico"""
    
    print("🧪 Probando el historial de cultivos")
    
    # 1. Obtener lista de cultivos disponibles
    print("\n📊 1. Obteniendo cultivos disponibles...")
    resp = requests.get(f"{BASE_URL}/api/crops")
    if resp.status_code != 200:
        print(f"❌ Error obteniendo cultivos: {resp.status_code}")
        return False
    
    data = resp.json()
    cultivos = data.get('crops', [])
    
    if not cultivos:
        print("❌ No hay cultivos disponibles para probar")
        return False
    
    # Buscar un cultivo con producción
    cultivo_con_produccion = None
    for cultivo in cultivos:
        produccion = cultivo.get('produccion_diaria', [])
        if produccion and len(produccion) > 0:
            cultivo_con_produccion = cultivo
            break
    
    if not cultivo_con_produccion:
        print("❌ No hay cultivos con producción para probar el historial")
        return False
    
    crop_id = cultivo_con_produccion['id']
    nombre = cultivo_con_produccion['nombre']
    produccion_total = len(cultivo_con_produccion.get('produccion_diaria', []))
    
    print(f"✅ Probando historial del cultivo: {nombre} (ID: {crop_id})")
    print(f"📈 Registros de producción: {produccion_total}")
    
    # 2. Probar la página de historial
    print(f"\n🔍 2. Accediendo al historial: /crops/{crop_id}/history")
    
    session = requests.Session()
    resp = session.get(f"{BASE_URL}/crops/{crop_id}/history")
    
    if resp.status_code != 200:
        print(f"❌ Error accediendo al historial: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    html_content = resp.text
    
    # 3. Verificar que el HTML contiene los elementos necesarios
    print("\n✅ 3. Verificando contenido de la página de historial...")
    
    checks = [
        ('historyChart', 'Canvas del gráfico'),
        ('data-labels', 'Atributo de etiquetas'),
        ('data-unidades', 'Atributo de unidades'),
        ('data-kilos', 'Atributo de kilos'),
        ('Chart.js', 'Biblioteca Chart.js')
    ]
    
    all_good = True
    for check, description in checks:
        if check in html_content:
            print(f"  ✅ {description}: Encontrado")
        else:
            print(f"  ❌ {description}: NO encontrado")
            all_good = False
    
    # 4. Verificar datos específicos del cultivo seleccionado
    print(f"\n📊 4. Verificando datos del cultivo '{nombre}'...")
    
    # Buscar las unidades en los registros
    registros = cultivo_con_produccion.get('produccion_diaria', [])
    total_unidades = 0
    total_kilos = 0
    
    for registro in registros:
        unidades = registro.get('unidades', 0)
        kilos = registro.get('kilos', 0)
        total_unidades += unidades if unidades else 0
        total_kilos += kilos if kilos else 0
    
    print(f"  📈 Total unidades registradas: {total_unidades}")
    print(f"  ⚖️  Total kilos registrados: {total_kilos:.2f}")
    
    if total_unidades > 0:
        print("  ✅ El cultivo tiene registros de unidades para mostrar en el gráfico")
        
        # Verificar que los datos estén en el HTML
        if 'data-unidades' in html_content and str(total_unidades) in html_content:
            print("  ✅ Los datos de unidades están presentes en el HTML")
        else:
            print("  ⚠️  Los datos de unidades pueden no estar correctamente en el HTML")
    else:
        print("  ⚠️  El cultivo no tiene registros de unidades (solo kilos)")
    
    if all_good:
        print(f"\n🎉 Historial funcionando correctamente para '{nombre}'")
        print(f"🌐 Puedes verlo en: {BASE_URL}/crops/{crop_id}/history")
        return True
    else:
        print(f"\n⚠️  Historial con algunos problemas para '{nombre}'")
        return False

if __name__ == "__main__":
    try:
        success = test_historial_cultivo()
        if success:
            print("\n✅ Test de historial completado exitosamente")
        else:
            print("\n❌ Test de historial con problemas")
    except Exception as e:
        print(f"\n💥 Error durante el test: {e}")
