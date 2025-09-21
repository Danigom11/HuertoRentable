# Cloud Function Python para HuertoRentable
# Ejecuta la aplicación Flask completa en Firebase Functions

import os
import sys
from pathlib import Path

# Configurar path para importar la aplicación
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Importar dependencias de Firebase Functions
from firebase_functions import https_fn
from firebase_admin import initialize_app

# Inicializar Firebase Admin (solo una vez)
try:
    initialize_app()
except ValueError:
    # Ya está inicializado
    pass

# Importar tu aplicación Flask
from run import app

@https_fn.on_request(cors=https_fn.CorsOptions(
    cors_origins=True,
    cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    cors_allow_headers=["Content-Type", "Authorization"]
))
def flaskApp(req: https_fn.Request) -> https_fn.Response:
    """
    Cloud Function que ejecuta tu aplicación Flask completa
    Maneja todas las rutas: /, /auth/login, /crops, /dashboard, etc.
    """
    # Configurar Flask para Cloud Functions
    with app.app_context():
        # Configurar request context para Flask
        with app.test_request_context(
            path=req.path,
            method=req.method,
            headers=dict(req.headers),
            query_string=req.query_string.decode() if req.query_string else None,
            data=req.get_data(),
            content_type=req.content_type
        ):
            try:
                # Ejecutar la aplicación Flask
                response = app.full_dispatch_request()
                
                # Convertir respuesta Flask a respuesta Cloud Function
                return https_fn.Response(
                    response.get_data(),
                    status=response.status_code,
                    headers=dict(response.headers),
                    mimetype=response.mimetype
                )
            except Exception as e:
                # Manejo de errores
                print(f"Error en Cloud Function: {e}")
                return https_fn.Response(
                    f"Error interno del servidor: {str(e)}",
                    status=500,
                    mimetype="text/plain"
                )
