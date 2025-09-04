# Cloud Function que ejecuta TU aplicación Flask EXACTA
# Sin modificaciones, tal como está

import os
import sys

# Agregar el directorio padre al path para importar tu app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar TU aplicación Flask exacta
from run import app

# Esta función es llamada por Firebase Functions
def flaskApp(request):
    """
    Cloud Function que ejecuta tu aplicación Flask tal como está
    """
    # Configurar Flask para Cloud Functions
    with app.app_context():
        # Tu aplicación Flask maneja todo el resto
        return app.full_dispatch_request()

# Para desarrollo local
if __name__ == "__main__":
    # Usar tu run.py exacto
    from run import main
    main()
