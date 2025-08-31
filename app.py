"""
Punto de entrada compatible con Render.com
""" 

from run import app

if __name__ == "__main__":
    print("🚀 Iniciando servidor en puerto 5000...")
    app.run(host="127.0.0.1", port=5000, debug=True)
