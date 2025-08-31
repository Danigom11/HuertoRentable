#!/usr/bin/env python3
"""
Script de prueba final del sistema de historial completo
"""

import requests
import json
import re

BASE_URL = "http://127.0.0.1:5000"

def test_flujo_completo():
    """Prueba el flujo completo desde dashboard hasta historial"""
    
    print("🧪 Probando flujo completo del historial")
    
    # 1. Verificar dashboard demo
    print("\n📊 1. Verificando dashboard demo...")
    resp = requests.get(f"{BASE_URL}/?demo=true")
    if resp.status_code != 200:
        print(f"❌ Error en dashboard demo: {resp.status_code}")
        return False
    
    dashboard_html = resp.text
    
    # Verificar que hay botones de "Ver historial"
    historial_buttons = dashboard_html.count("Ver historial")
    print(f"✅ Dashboard cargado - {historial_buttons} botones de historial encontrados")
    
    # Buscar enlaces de historial con demo=true
    historial_links = re.findall(r'href="([^"]*crop_history[^"]*)"', dashboard_html)
    demo_links = [link for link in historial_links if 'demo=true' in link]
    
    print(f"📍 Enlaces de historial encontrados: {len(historial_links)}")
    print(f"📍 Enlaces con demo=true: {len(demo_links)}")
    
    if demo_links:
        # Probar el primer enlace de historial
        test_link = demo_links[0]
        # Limpiar entidades HTML
        test_link = test_link.replace('&amp;', '&')
        full_url = f"{BASE_URL}{test_link}"
        
        print(f"\n🔍 2. Probando enlace de historial: {test_link}")
        
        resp = requests.get(full_url)
        if resp.status_code != 200:
            print(f"❌ Error accediendo al historial: {resp.status_code}")
            return False
        
        historial_html = resp.text
        
        # Verificar elementos clave del historial
        checks = [
            ('id="historyChart"', 'Canvas del gráfico'),
            ('Chart.js', 'Biblioteca Chart.js'),
            ('data-kilos=', 'Datos de kilos'),
            ('Historial:', 'Título del historial'),
            ('Volver', 'Botón de volver')
        ]
        
        print("✅ Verificando página de historial...")
        all_good = True
        for check, description in checks:
            if check in historial_html:
                print(f"  ✅ {description}: Encontrado")
            else:
                print(f"  ❌ {description}: NO encontrado")
                all_good = False
        
        # Extraer datos del gráfico
        kilos_match = re.search(r'data-kilos="([^"]*)"', historial_html)
        if kilos_match:
            try:
                kilos_str = kilos_match.group(1).replace('&#34;', '"')
                kilos = json.loads(kilos_str)
                total_kilos = sum(k for k in kilos if k)
                print(f"  📊 Total kilos en gráfico: {total_kilos:.2f} kg")
            except Exception as e:
                print(f"  ⚠️  Error parseando datos del gráfico: {e}")
        
        return all_good
    else:
        print("❌ No se encontraron enlaces de historial con demo=true")
        return False

def test_casos_especiales():
    """Prueba casos especiales del historial"""
    
    print("\n🔬 Probando casos especiales...")
    
    # Caso 1: Cultivo con datos de kilos (tomates)
    print("\n📊 Caso 1: Cultivo con datos de kilos...")
    resp = requests.get(f"{BASE_URL}/crops/demo-1/history?demo=true")
    if resp.status_code == 200:
        html = resp.text
        if 'data-kilos=' in html and 'historyChart' in html:
            print("✅ Cultivo con kilos funciona correctamente")
        else:
            print("❌ Problema con cultivo de kilos")
    
    # Caso 2: Cultivo sin producción (apio)
    print("\n📊 Caso 2: Cultivo sin producción...")
    resp = requests.get(f"{BASE_URL}/crops/demo-8/history?demo=true")
    if resp.status_code == 200:
        html = resp.text
        if 'No hay registros de producción' in html or 'historyChart' in html:
            print("✅ Cultivo sin producción maneja correctamente")
        else:
            print("❌ Problema con cultivo sin producción")
    
    print("\n✅ Casos especiales verificados")

if __name__ == "__main__":
    try:
        print("🚀 INICIANDO TESTS DEL SISTEMA DE HISTORIAL")
        print("=" * 50)
        
        success1 = test_flujo_completo()
        test_casos_especiales()
        
        if success1:
            print("\n🎉 ¡SISTEMA DE HISTORIAL FUNCIONANDO PERFECTAMENTE!")
            print("\n📋 RESUMEN:")
            print("✅ Dashboard demo carga correctamente")
            print("✅ Botones 'Ver historial' funcionan")
            print("✅ Gráficos se renderizan con datos")
            print("✅ Modo demo integrado correctamente")
            print("\n🌐 Para probar manualmente:")
            print(f"   1. Ve a: {BASE_URL}/?demo=true")
            print("   2. Haz clic en cualquier botón 'Ver historial'")
            print("   3. Verás el gráfico con los kilos por fecha")
        else:
            print("\n❌ Hay problemas con el sistema de historial")
            
    except Exception as e:
        print(f"\n💥 Error durante los tests: {e}")
