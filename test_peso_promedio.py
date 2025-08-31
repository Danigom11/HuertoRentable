#!/usr/bin/env python3
"""
Script de prueba para el sistema de peso promedio automático
Verifica que al añadir unidades se calculen automáticamente los kilos
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_peso_promedio_system():
    """Prueba el sistema completo de peso promedio"""
    
    print("🧪 Iniciando pruebas del sistema de peso promedio")
    session = requests.Session()
    
    # 1. Ir a la página principal para obtener sesión
    print("\n📝 1. Obteniendo sesión...")
    resp = session.get(f"{BASE_URL}/")
    if resp.status_code != 200:
        print(f"❌ Error obteniendo sesión: {resp.status_code}")
        return False
    print("✅ Sesión obtenida correctamente")
    
    # 2. Crear un nuevo cultivo con peso promedio
    print("\n🌱 2. Creando cultivo con peso promedio...")
    cultivo_data = {
        'nombre': 'tomates_test_peso',
        'precio': '2.50',
        'numero_plantas': '10',
        'peso_promedio': '150'  # 150 gramos por tomate
    }
    
    resp = session.post(f"{BASE_URL}/api/crops", data=cultivo_data)
    if resp.status_code != 200:
        print(f"❌ Error creando cultivo: {resp.status_code}")
        print(f"Response: {resp.text}")
        return False
    
    result = resp.json()
    if not result.get('success'):
        print(f"❌ Error en respuesta: {result.get('message')}")
        return False
    
    crop_id = result.get('crop_id')
    print(f"✅ Cultivo creado con ID: {crop_id}")
    
    # 3. Añadir producción solo con unidades (debe calcular kilos automáticamente)
    print("\n📊 3. Añadiendo producción con solo unidades...")
    produccion_data = {
        'unidades': '5'  # 5 tomates × 150g = 750g = 0.75kg
    }
    
    resp = session.post(f"{BASE_URL}/api/crops/{crop_id}/production", data=produccion_data)
    if resp.status_code != 200:
        print(f"❌ Error añadiendo producción: {resp.status_code}")
        print(f"Response: {resp.text}")
        return False
    
    result = resp.json()
    if not result.get('success'):
        print(f"❌ Error en respuesta de producción: {result.get('message')}")
        return False
    
    print("✅ Producción añadida correctamente")
    
    # 4. Verificar que se calcularon los kilos automáticamente
    print("\n🔍 4. Verificando cálculo automático de kilos...")
    resp = session.get(f"{BASE_URL}/api/crops")
    if resp.status_code != 200:
        print(f"❌ Error obteniendo cultivos: {resp.status_code}")
        return False
    
    cultivos = resp.json()
    
    # Buscar nuestro cultivo de prueba
    cultivo_test = None
    for cultivo in cultivos:
        if cultivo.get('nombre') == 'tomates_test_peso':
            cultivo_test = cultivo
            break
    
    if not cultivo_test:
        print("❌ No se encontró el cultivo de prueba")
        return False
    
    # Verificar que tiene producción
    produccion = cultivo_test.get('produccion_diaria', [])
    if not produccion:
        print("❌ No se encontró producción en el cultivo")
        return False
    
    ultima_produccion = produccion[-1]
    unidades = ultima_produccion.get('unidades')
    kilos = ultima_produccion.get('kilos')
    
    print(f"📈 Unidades registradas: {unidades}")
    print(f"📈 Kilos calculados: {kilos}")
    
    # Verificar el cálculo: 5 unidades × 150g = 750g = 0.75kg
    esperado_kilos = (5 * 150) / 1000  # 0.75
    
    if abs(kilos - esperado_kilos) < 0.01:  # Tolerancia de 0.01kg
        print(f"✅ Cálculo correcto: {kilos}kg (esperado: {esperado_kilos}kg)")
        
        # Verificar beneficio total
        precio_por_kilo = cultivo_test.get('precio_por_kilo', 0)
        beneficio_esperado = kilos * precio_por_kilo
        
        print(f"💰 Precio por kilo: {precio_por_kilo}€")
        print(f"💰 Beneficio esperado: {beneficio_esperado}€")
        
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("El sistema de peso promedio funciona correctamente")
        return True
    else:
        print(f"❌ Cálculo incorrecto: {kilos}kg (esperado: {esperado_kilos}kg)")
        return False

if __name__ == "__main__":
    try:
        success = test_peso_promedio_system()
        if success:
            print("\n✅ Sistema de peso promedio verificado correctamente")
            sys.exit(0)
        else:
            print("\n❌ Falló la verificación del sistema de peso promedio")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error durante las pruebas: {e}")
        sys.exit(1)
