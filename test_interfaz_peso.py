#!/usr/bin/env python3
"""
Script de prueba simplificado para verificar la interfaz web
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_interfaz_peso_promedio():
    """Prueba la interfaz web del sistema de peso promedio"""
    
    print("🧪 Verificando interfaz de peso promedio")
    
    # 1. Verificar que la página de cultivos carga
    print("\n📝 1. Verificando página de cultivos...")
    resp = requests.get(f"{BASE_URL}/crops")
    if resp.status_code != 200:
        print(f"❌ Error cargando /crops: {resp.status_code}")
        return False
    
    # Verificar que contiene el campo peso_promedio
    html_content = resp.text
    if 'peso_promedio' in html_content:
        print("✅ Campo peso_promedio encontrado en la interfaz")
    else:
        print("❌ Campo peso_promedio NO encontrado en la interfaz")
        return False
    
    # 2. Verificar que el dashboard carga
    print("\n📊 2. Verificando dashboard...")
    resp = requests.get(f"{BASE_URL}/")
    if resp.status_code != 200:
        print(f"❌ Error cargando dashboard: {resp.status_code}")
        return False
    print("✅ Dashboard carga correctamente")
    
    # 3. Verificar que la API de cultivos responde
    print("\n🔍 3. Verificando API de cultivos...")
    resp = requests.get(f"{BASE_URL}/api/crops")
    if resp.status_code == 200:
        cultivos = resp.json()
        print(f"✅ API responde correctamente - {len(cultivos)} cultivos encontrados")
        
        # Verificar si algún cultivo tiene peso_promedio_gramos
        for cultivo in cultivos:
            if 'peso_promedio_gramos' in cultivo:
                print(f"✅ Cultivo '{cultivo.get('nombre')}' tiene peso_promedio_gramos: {cultivo.get('peso_promedio_gramos')}g")
                return True
        
        print("ℹ️ No hay cultivos con peso_promedio_gramos aún")
        return True
    else:
        print(f"❌ Error en API de cultivos: {resp.status_code}")
        return False

if __name__ == "__main__":
    try:
        success = test_interfaz_peso_promedio()
        if success:
            print("\n✅ Interfaz de peso promedio verificada correctamente")
            print("🌟 El sistema está listo para usar")
        else:
            print("\n❌ Falló la verificación de la interfaz")
    except Exception as e:
        print(f"\n💥 Error durante las pruebas: {e}")
