"""
Servicio de gestión de cultivos
CRUD de cultivos con soporte multi-usuario y planes
"""
import datetime
from typing import List, Dict, Optional, Tuple

class CropService:
    """Servicio centralizado para gestión de cultivos"""
    
    def __init__(self, db):
        self.db = db
    
    def get_user_crops(self, user_uid: str) -> List[Dict]:
        """
        Obtener todos los cultivos de un usuario
        
        Args:
            user_uid (str): UID del usuario
            
        Returns:
            List[Dict]: Lista de cultivos del usuario
        """
        try:
            if not self.db:
                return self.get_demo_crops()
            
            crops_ref = self.db.collection('usuarios').document(user_uid).collection('cultivos')
            docs = crops_ref.where('activo', '==', True).order_by('fecha_siembra', direction='DESCENDING').stream()
            
            cultivos = []
            for doc in docs:
                cultivo = doc.to_dict()
                cultivo['id'] = doc.id
                # Convertir timestamps a datetime si es necesario
                cultivo = self._process_cultivo_dates(cultivo)
                cultivos.append(cultivo)
            
            return cultivos
            
        except Exception as e:
            print(f"Error obteniendo cultivos del usuario: {e}")
            return self.get_demo_crops()
    
    def create_crop(self, user_uid: str, crop_data: Dict) -> bool:
        """
        Crear nuevo cultivo para un usuario
        
        Args:
            user_uid (str): UID del usuario
            crop_data (Dict): Datos del cultivo
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            if not self.db:
                return False
            
            # Verificar límites del plan del usuario
            if not self._check_crop_limits(user_uid):
                return False
            
            # Preparar datos del cultivo
            cultivo = {
                'nombre': crop_data.get('nombre', '').lower().strip(),
                'fecha_siembra': datetime.datetime.utcnow(),
                'fecha_cosecha': None,
                'precio_por_kilo': float(crop_data.get('precio', 0)),
                'abonos': [],
                'produccion_diaria': [],
                'activo': True,
                'creado_en': datetime.datetime.utcnow(),
                'actualizado_en': datetime.datetime.utcnow()
            }
            
            # Guardar en Firestore
            crops_ref = self.db.collection('usuarios').document(user_uid).collection('cultivos')
            doc_ref = crops_ref.add(cultivo)
            
            print(f"✅ Cultivo '{cultivo['nombre']}' creado para usuario {user_uid}")
            return True
            
        except Exception as e:
            print(f"Error creando cultivo: {e}")
            return False
    
    def update_production(self, user_uid: str, crop_id: str, kilos: float) -> bool:
        """
        Actualizar producción diaria de un cultivo
        
        Args:
            user_uid (str): UID del usuario
            crop_id (str): ID del cultivo
            kilos (float): Kilogramos producidos
            
        Returns:
            bool: True si se actualizó exitosamente
        """
        try:
            if not self.db:
                return False
            
            # Referencia al cultivo
            crop_ref = self.db.collection('usuarios').document(user_uid).collection('cultivos').document(crop_id)
            
            # Obtener cultivo actual
            crop_doc = crop_ref.get()
            if not crop_doc.exists:
                return False
            
            cultivo = crop_doc.to_dict()
            
            # Añadir nueva producción
            nueva_produccion = {
                'fecha': datetime.datetime.utcnow(),
                'kilos': float(kilos)
            }
            
            produccion_actual = cultivo.get('produccion_diaria', [])
            produccion_actual.append(nueva_produccion)
            
            # Actualizar en Firestore
            crop_ref.update({
                'produccion_diaria': produccion_actual,
                'actualizado_en': datetime.datetime.utcnow()
            })
            
            print(f"✅ Producción actualizada: {kilos}kg para cultivo {crop_id}")
            return True
            
        except Exception as e:
            print(f"Error actualizando producción: {e}")
            return False
    
    def get_user_totals(self, user_uid: str) -> Tuple[float, float]:
        """
        Calcular totales de kilos y beneficios del usuario
        
        Args:
            user_uid (str): UID del usuario
            
        Returns:
            Tuple[float, float]: (total_kilos, total_beneficios)
        """
        try:
            cultivos = self.get_user_crops(user_uid)
            total_kilos = 0
            total_beneficios = 0
            
            for cultivo in cultivos:
                precio_kilo = cultivo.get('precio_por_kilo', 0)
                produccion = cultivo.get('produccion_diaria', [])
                
                kilos_cultivo = sum(p.get('kilos', 0) for p in produccion)
                beneficio_cultivo = kilos_cultivo * precio_kilo
                
                total_kilos += kilos_cultivo
                total_beneficios += beneficio_cultivo
            
            return total_kilos, total_beneficios
            
        except Exception as e:
            print(f"Error calculando totales: {e}")
            return 0, 0
    
    def get_demo_crops(self) -> List[Dict]:
        """Datos demo completos para mostrar funcionalidades premium - 10 plantas distintas"""
        import random
        
        # Plantas variadas con datos realistas
        demo_data = [
            {'nombre': 'tomates', 'precio': 3.50, 'plantas': 15, 'unidades_base': 180},
            {'nombre': 'lechugas', 'precio': 2.80, 'plantas': 12, 'unidades_base': 36},
            {'nombre': 'zanahorias', 'precio': 1.90, 'plantas': 20, 'unidades_base': 240},
            {'nombre': 'pimientos', 'precio': 4.20, 'plantas': 8, 'unidades_base': 96},
            {'nombre': 'berenjenas', 'precio': 3.80, 'plantas': 6, 'unidades_base': 72},
            {'nombre': 'calabacines', 'precio': 2.50, 'plantas': 10, 'unidades_base': 150},
            {'nombre': 'espinacas', 'precio': 4.50, 'plantas': 14, 'unidades_base': 84},
            {'nombre': 'apio', 'precio': 3.20, 'plantas': 8, 'unidades_base': 48},
            {'nombre': 'brócoli', 'precio': 5.20, 'plantas': 7, 'unidades_base': 42},
            {'nombre': 'coliflor', 'precio': 4.80, 'plantas': 6, 'unidades_base': 36}
        ]
        
        crops = []
        base_date = datetime.datetime(2025, 4, 1)  # Comenzar en abril
        
        for i, data in enumerate(demo_data):
            # Fechas escalonadas cada 2 semanas
            fecha_siembra = base_date + datetime.timedelta(weeks=i*2)
            
            # Generar producción diaria realista (últimos 3 meses)
            produccion_diaria = []
            fecha_inicio_cosecha = fecha_siembra + datetime.timedelta(days=60)  # 2 meses después de siembra
            
            # Generar 20-30 días de cosecha con variación realista
            for j in range(random.randint(20, 30)):
                fecha_cosecha = fecha_inicio_cosecha + datetime.timedelta(days=j*2)
                if fecha_cosecha <= datetime.datetime.now():
                    # Producción variable entre 0.5kg y 3kg por día
                    kilos = round(random.uniform(0.5, 3.0), 1)
                    produccion_diaria.append({
                        'fecha': fecha_cosecha,
                        'kilos': kilos
                    })
            
            cultivo = {
                'id': f'demo-{i+1}',
                'nombre': data['nombre'],
                'fecha_siembra': fecha_siembra,
                'precio_por_kilo': data['precio'],
                'plantas_sembradas': data['plantas'],
                'unidades_recolectadas': data['unidades_base'] + random.randint(-20, 40),
                'produccion_diaria': produccion_diaria,
                'activo': i < 8,  # Los primeros 8 están activos, 2 cosechados
                'fecha_cosecha': None if i < 8 else fecha_siembra + datetime.timedelta(days=120)
            }
            
            crops.append(cultivo)
        
        # Calcular kilos_totales y beneficio_total para cada cultivo
        for cultivo in crops:
            produccion = cultivo.get('produccion_diaria', [])
            cultivo['kilos_totales'] = sum(p.get('kilos', 0) for p in produccion)
            cultivo['beneficio_total'] = cultivo['kilos_totales'] * cultivo['precio_por_kilo']
        
        return crops
    
    def get_demo_totals(self) -> Tuple[float, float]:
        """Calcular totales de datos demo"""
        demo_crops = self.get_demo_crops()
        total_kilos = 0
        total_beneficios = 0
        
        for cultivo in demo_crops:
            precio_kilo = cultivo.get('precio_por_kilo', 0)
            produccion = cultivo.get('produccion_diaria', [])
            
            kilos_cultivo = sum(p.get('kilos', 0) for p in produccion)
            beneficio_cultivo = kilos_cultivo * precio_kilo
            
            total_kilos += kilos_cultivo
            total_beneficios += beneficio_cultivo
        
        return total_kilos, total_beneficios
    
    def _check_crop_limits(self, user_uid: str) -> bool:
        """
        Verificar si el usuario puede crear más cultivos según su plan
        
        Args:
            user_uid (str): UID del usuario
            
        Returns:
            bool: True si puede crear más cultivos
        """
        try:
            from app.auth.auth_service import UserService
            from app.utils.helpers import get_plan_limits
            
            user_service = UserService(self.db)
            plan = user_service.get_user_plan(user_uid)
            limits = get_plan_limits(plan)
            
            # Si el plan permite cultivos ilimitados
            if limits['cultivos_max'] is None:
                return True
            
            # Contar cultivos actuales
            current_crops = len(self.get_user_crops(user_uid))
            
            return current_crops < limits['cultivos_max']
            
        except Exception as e:
            print(f"Error verificando límites: {e}")
            return True  # En caso de error, permitir creación
    
    def _process_cultivo_dates(self, cultivo: Dict) -> Dict:
        """Procesar fechas de cultivo para compatibilidad"""
        # Convertir timestamps de Firestore a datetime si es necesario
        for field in ['fecha_siembra', 'fecha_cosecha', 'creado_en', 'actualizado_en']:
            if field in cultivo and cultivo[field]:
                if hasattr(cultivo[field], 'timestamp'):
                    # Es un timestamp de Firestore
                    cultivo[field] = cultivo[field].to_datetime()
        
        # Procesar fechas en produccion_diaria
        if 'produccion_diaria' in cultivo:
            for produccion in cultivo['produccion_diaria']:
                if 'fecha' in produccion and hasattr(produccion['fecha'], 'timestamp'):
                    produccion['fecha'] = produccion['fecha'].to_datetime()
        
        return cultivo
