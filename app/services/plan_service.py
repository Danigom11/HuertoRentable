"""
Servicio de gestión de planes de suscripción
Manejo de planes, límites y actualizaciones de suscripción
"""
import datetime
from typing import Dict, List, Optional
from app.utils.helpers import PLAN_LIMITS

class PlanService:
    """Servicio centralizado para gestión de planes"""
    
    def __init__(self, db):
        self.db = db
    
    def get_available_plans(self) -> Dict:
        """
        Obtener todos los planes disponibles con sus características
        
        Returns:
            Dict: Planes con precios y características
        """
        return {
            'invitado': {
                'name': 'Invitado',
                'price': 0,
                'price_display': 'Gratis',
                'description': 'Prueba HuertoRentable sin registrarte',
                'features': [
                    'Hasta 3 cultivos',
                    'Datos guardados localmente',
                    'Informes básicos',
                    '⚠️ Los datos pueden perderse'
                ],
                'limitations': [
                    'Sin copia de seguridad en la nube',
                    'Sin sincronización entre dispositivos',
                    'Datos pueden perderse al limpiar navegador'
                ],
                'color': 'secondary',
                'popular': False,
                'storage': 'local'
            },
            'gratuito': {
                'name': 'Gratuito',
                'price': 0,
                'price_display': 'Gratis',
                'description': 'Perfecto para huertos familiares',
                'features': [
                    'Cultivos ilimitados',
                    'Copia de seguridad en la nube',
                    'Sincronización entre dispositivos',
                    'Informes básicos',
                    'Notificaciones básicas'
                ],
                'limitations': [
                    'Anuncios ocasionales',
                    'Informes básicos solamente'
                ],
                'color': 'success',
                'popular': True,
                'storage': 'firebase'
            },
            'premium': {
                'name': 'Premium',
                'price': 0.99,
                'price_display': '€0.99/mes',
                'description': 'Para huertos profesionales',
                'features': [
                    'Todo lo del plan gratuito',
                    'Sin anuncios',
                    'Informes avanzados con gráficas',
                    'Exportar datos a Excel/PDF',
                    'Notificaciones avanzadas',
                    'Soporte prioritario'
                ],
                'limitations': [],
                'color': 'primary',
                'popular': False,
                'storage': 'firebase'
            }
        }
    
    def get_plan_info(self, plan_name: str) -> Dict:
        """
        Obtener información completa de un plan específico
        
        Args:
            plan_name (str): Nombre del plan
            
        Returns:
            Dict: Información del plan con límites y características
        """
        plans = self.get_available_plans()
        plan_info = plans.get(plan_name, plans['invitado'])
        
        # Añadir límites técnicos
        plan_limits = PLAN_LIMITS.get(plan_name, PLAN_LIMITS['invitado'])
        plan_info['limits'] = plan_limits
        
        return plan_info
    
    def create_guest_session(self) -> str:
        """
        Crear sesión temporal para usuario invitado
        
        Returns:
            str: ID de sesión temporal
        """
        import uuid
        guest_id = f"guest_{uuid.uuid4().hex[:8]}"
        
        # Crear entrada temporal en localStorage del cliente
        # Los datos se manejarán completamente en el frontend
        return guest_id
    
    def upgrade_user_plan(self, uid: str, new_plan: str) -> bool:
        """
        Actualizar plan de usuario
        
        Args:
            uid (str): UID del usuario
            new_plan (str): Nuevo plan ('gratuito', 'premium')
            
        Returns:
            bool: True si se actualizó exitosamente
        """
        try:
            if not self.db:
                return False
            
            # Validar que el plan existe
            if new_plan not in ['gratuito', 'premium']:
                return False
            
            # Actualizar plan en Firestore
            self.db.collection('usuarios').document(uid).update({
                'plan': new_plan,
                'fecha_cambio_plan': datetime.datetime.utcnow(),
                'actualizado_en': datetime.datetime.utcnow()
            })
            
            print(f"✅ Usuario {uid[:8]}... actualizado a plan '{new_plan}'")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando plan: {e}")
            return False
    
    def get_plan_usage(self, uid: str) -> Dict:
        """
        Obtener uso actual del usuario respecto a los límites de su plan
        
        Args:
            uid (str): UID del usuario
            
        Returns:
            Dict: Información de uso vs límites
        """
        try:
            from app.auth.auth_service import UserService
            from app.services.crop_service import CropService
            
            user_service = UserService(self.db)
            crop_service = CropService(self.db)
            
            # Obtener plan del usuario
            plan = user_service.get_user_plan(uid)
            plan_info = self.get_plan_info(plan)
            
            # Obtener uso actual
            crops_count = len(crop_service.get_user_crops(uid))
            
            return {
                'plan': plan,
                'plan_info': plan_info,
                'usage': {
                    'crops': {
                        'current': crops_count,
                        'limit': plan_info['limits']['max_crops'],
                        'unlimited': plan_info['limits']['max_crops'] == -1
                    }
                }
            }
            
        except Exception as e:
            print(f"Error obteniendo uso del plan: {e}")
            return {}
    
    def check_plan_limits(self, uid: str, feature: str) -> bool:
        """
        Verificar si el usuario puede usar una característica específica
        
        Args:
            uid (str): UID del usuario
            feature (str): Característica a verificar ('crops', 'export', etc.)
            
        Returns:
            bool: True si puede usar la característica
        """
        try:
            usage = self.get_plan_usage(uid)
            
            if feature == 'crops':
                if usage['usage']['crops']['unlimited']:
                    return True
                return usage['usage']['crops']['current'] < usage['usage']['crops']['limit']
            
            # Para otras características, verificar en plan_info
            plan_limits = usage['plan_info']['limits']
            return plan_limits.get(feature, False)
            
        except Exception as e:
            print(f"Error verificando límites: {e}")
            return True  # En caso de error, permitir
