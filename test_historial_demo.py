#!/usr/bin/env python3
"""
Script de prueba mejorado para verificar el historial del cultivo en modo demo
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_historial_demo():
    """Prueba el historial específicamente en modo demo"""
    
    print("🧪 Probando el historial en modo demo")
    
    # Probar directamente el historial del cultivo demo-1 con parámetro demo=true
    crop_id = "demo-1"
    url = f"{BASE_URL}/crops/{crop_id}/history?demo=true"
    
    print(f"\n🔍 Accediendo a: {url}")
    
    resp = requests.get(url)
    
    if resp.status_code != 200:
        print(f"❌ Error accediendo al historial: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    html_content = resp.text
    
    # Verificar elementos clave
    print("\n✅ Verificando contenido de la página...")
    
    checks = [
        ('id="historyChart"', 'Canvas del gráfico'),
        ('data-labels=', 'Atributo de etiquetas'),
        ('data-unidades=', 'Atributo de unidades'),
        ('data-kilos=', 'Atributo de kilos'),
        ('Chart.js', 'Biblioteca Chart.js'),
        ('Historial:', 'Título del historial'),
        ('Producción por fecha', 'Título del gráfico'),
        ('Registros de producción', 'Título de la tabla')
    ]
    
    all_good = True
    for check, description in checks:
        if check in html_content:
            print(f"  ✅ {description}: Encontrado")
        else:
            print(f"  ❌ {description}: NO encontrado")
            all_good = False
    
    # Extraer y verificar datos del gráfico
    print("\n📊 Verificando datos del gráfico...")
    
    import re
    
    # Buscar data-labels
    labels_match = re.search(r'data-labels="([^"]*)"', html_content)
    if labels_match:
        try:
            labels_str = labels_match.group(1).replace('&#34;', '"')
            labels = json.loads(labels_str)
            print(f"  📅 Etiquetas encontradas: {len(labels)} fechas")
            if len(labels) > 0:
                print(f"    Primera fecha: {labels[0]}")
                print(f"    Última fecha: {labels[-1]}")
        except Exception as e:
            print(f"  ⚠️  Error parseando etiquetas: {e}")
    
    # Buscar data-kilos
    kilos_match = re.search(r'data-kilos="([^"]*)"', html_content)
    if kilos_match:
        try:
            kilos_str = kilos_match.group(1).replace('&#34;', '"')
            kilos = json.loads(kilos_str)
            total_kilos = sum(k for k in kilos if k)
            print(f"  ⚖️  Datos de kilos: {len(kilos)} registros, total: {total_kilos:.2f} kg")
        except Exception as e:
            print(f"  ⚠️  Error parseando kilos: {e}")
    
    # Buscar data-unidades
    unidades_match = re.search(r'data-unidades="([^"]*)"', html_content)
    if unidades_match:
        try:
            unidades_str = unidades_match.group(1).replace('&#34;', '"')
            unidades = json.loads(unidades_str)
            total_unidades = sum(u for u in unidades if u)
            print(f"  🔢 Datos de unidades: {len(unidades)} registros, total: {total_unidades}")
        except Exception as e:
            print(f"  ⚠️  Error parseando unidades: {e}")
    
    if all_good:
        print(f"\n🎉 ¡Historial funcionando correctamente!")
        print(f"🌐 URL: {url}")
        return True
    else:
        print(f"\n⚠️  Historial con algunos problemas")
        return False

if __name__ == "__main__":
    try:
        success = test_historial_demo()
        if success:
            print("\n✅ Test de historial demo completado exitosamente")
        else:
            print("\n❌ Test de historial demo con problemas")
    except Exception as e:
        print(f"\n💥 Error durante el test: {e}")
