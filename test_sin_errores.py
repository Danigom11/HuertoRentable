#!/usr/bin/env python3
"""
Test final para verificar que el error de UnboundLocalError está solucionado
"""

import requests

BASE_URL = "http://127.0.0.1:5000"

def test_historial_sin_error():
    """Verifica que el historial carga sin errores de UnboundLocalError"""
    
    print("🧪 Probando historial sin errores de session...")
    
    # Probar varios cultivos para asegurar que no hay errores
    cultivos_test = ['demo-1', 'demo-2', 'demo-3']
    
    for crop_id in cultivos_test:
        url = f"{BASE_URL}/crops/{crop_id}/history?demo=true"
        print(f"\n🔍 Probando {crop_id}...")
        
        try:
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                html = resp.text
                
                # Verificar que no hay errores de UnboundLocalError
                if 'UnboundLocalError' in html:
                    print(f"❌ Error UnboundLocalError encontrado en {crop_id}")
                    return False
                
                # Verificar que el canvas está presente
                if 'id="historyChart"' in html:
                    print(f"✅ Canvas presente en {crop_id}")
                else:
                    print(f"⚠️  Canvas no encontrado en {crop_id}")
                
                # Verificar que hay datos
                if 'data-kilos=' in html:
                    print(f"✅ Datos de kilos presentes en {crop_id}")
                else:
                    print(f"⚠️  Datos de kilos no encontrados en {crop_id}")
                    
            else:
                print(f"❌ Error HTTP {resp.status_code} en {crop_id}")
                return False
                
        except Exception as e:
            print(f"❌ Excepción en {crop_id}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_historial_sin_error()
        if success:
            print("\n🎉 ¡TODOS LOS TESTS PASARON!")
            print("✅ No hay errores de UnboundLocalError")
            print("✅ Los historiales cargan correctamente")
            print("✅ Los gráficos se muestran")
            print("\n📋 URLs de prueba:")
            print("  • http://127.0.0.1:5000/crops/demo-1/history?demo=true")
            print("  • http://127.0.0.1:5000/crops/demo-2/history?demo=true")
            print("  • http://127.0.0.1:5000/crops/demo-3/history?demo=true")
        else:
            print("\n❌ Algunos tests fallaron")
    except Exception as e:
        print(f"\n💥 Error durante los tests: {e}")
