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
            List[Dict]: Lista de cultivos del usuario (vacía si es usuario nuevo)
        """
        try:
            if not self.db:
                # Sin conexión a Firebase, devolver lista vacía para usuarios reales
                return []
            
            crops_ref = self.db.collection('usuarios').document(user_uid).collection('cultivos')
            # Evitar order_by que puede requerir índices si combinamos con where.
            # Obtenemos activos y ordenamos en memoria por fecha_siembra descendente.
            docs = crops_ref.where('activo', '==', True).stream()
            
            cultivos = []
            for doc in docs:
                cultivo = doc.to_dict()
                cultivo['id'] = doc.id
                # Convertir timestamps a datetime si es necesario
                cultivo = self._process_cultivo_dates(cultivo)
                cultivos.append(cultivo)
            
            # Ordenar por fecha_siembra descendente si está disponible
            try:
                cultivos.sort(key=lambda c: c.get('fecha_siembra') or c.get('creado_en') or datetime.datetime.min, reverse=True)
            except Exception:
                pass
            return cultivos
            
        except Exception as e:
            print(f"Error obteniendo cultivos del usuario {user_uid}: {e}")
            # Para usuarios reales, devolver lista vacía en lugar de datos demo
            return []
    
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
                'numero_plantas': int(crop_data.get('numero_plantas', 1)),
                'peso_promedio_gramos': float(crop_data.get('peso_promedio', 100)),  # Peso en gramos por unidad
                'abonos': [],
                'produccion_diaria': [],
                'activo': True,
                'creado_en': datetime.datetime.utcnow(),
                'actualizado_en': datetime.datetime.utcnow()
            }
            
            # Asegurar que el documento del usuario existe antes de escribir subcolecciones
            user_ref = self.db.collection('usuarios').document(user_uid)
            user_doc = user_ref.get()
            if not user_doc.exists:
                # Crear documento mínimo del usuario si no existe (fallback seguro)
                user_ref.set({
                    'uid': user_uid,
                    'plan': 'gratuito',
                    'fecha_registro': datetime.datetime.utcnow(),
                    'ultimo_acceso': datetime.datetime.utcnow()
                }, merge=True)

            # Guardar en Firestore
            crops_ref = user_ref.collection('cultivos')
            doc_ref = crops_ref.add(cultivo)
            
            print(f"✅ Cultivo '{cultivo['nombre']}' creado para usuario {user_uid}")
            return True
            
        except Exception as e:
            import traceback
            print(f"Error creando cultivo: {e}")
            traceback.print_exc()
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
        # Mantener compatibilidad con APIs existentes
        return self.update_production_generic(user_uid, crop_id, kilos=kilos, unidades=None)

    def update_production_generic(self, user_uid: str, crop_id: str, kilos: float | None = None, unidades: int | None = None) -> bool:
        """
        Actualizar producción diaria (kilos y/o unidades) de un cultivo.
        Si se proporciona uno de los dos, se añade un único registro con los campos presentes.
        Soporta Firestore y almacenamiento local (sesión) cuando no hay DB.
        """
        try:
            # Validación mínima
            has_kilos = kilos is not None and float(kilos) > 0
            has_units = unidades is not None and int(unidades) > 0
            if not has_kilos and not has_units:
                return False

            nueva_produccion = { 'fecha': datetime.datetime.utcnow() }
            if has_kilos:
                try:
                    nueva_produccion['kilos'] = float(kilos)
                except Exception:
                    pass
            if has_units:
                try:
                    nueva_produccion['unidades'] = int(unidades)
                    # Si solo se proporcionan unidades, calcular kilos automáticamente
                    if not has_kilos:
                        # Necesitamos obtener el peso promedio del cultivo
                        peso_promedio = self._get_peso_promedio_cultivo(user_uid, crop_id)
                        if peso_promedio > 0:
                            kilos_calculados = (int(unidades) * peso_promedio) / 1000  # gramos a kilos
                            nueva_produccion['kilos'] = round(kilos_calculados, 2)
                except Exception:
                    pass

            if not self.db:
                # Almacenamiento local en sesión
                from flask import session
                session_key = f'crops_{user_uid}'
                cultivos = session.get(session_key, [])
                # Buscar cultivo por id
                for c in cultivos:
                    if c.get('id') == crop_id:
                        produccion = c.get('produccion_diaria', [])
                        produccion.append(nueva_produccion)
                        c['produccion_diaria'] = produccion
                        break
                session[session_key] = cultivos
                return True

            # Firestore
            crop_ref = self.db.collection('usuarios').document(user_uid).collection('cultivos').document(crop_id)
            crop_doc = crop_ref.get()
            if not crop_doc.exists:
                return False
            cultivo = crop_doc.to_dict()

            produccion_actual = cultivo.get('produccion_diaria', [])
            produccion_actual.append(nueva_produccion)

            crop_ref.update({
                'produccion_diaria': produccion_actual,
                'actualizado_en': datetime.datetime.utcnow()
            })
            print(f"✅ Producción actualizada para cultivo {crop_id}: kilos={nueva_produccion.get('kilos')}, unidades={nueva_produccion.get('unidades')}")
            return True
        except Exception as e:
            print(f"Error actualizando producción (genérica): {e}")
            return False

    def _get_peso_promedio_cultivo(self, user_uid: str, crop_id: str) -> float:
        """
        Obtener el peso promedio de un cultivo específico
        
        Args:
            user_uid (str): UID del usuario
            crop_id (str): ID del cultivo
            
        Returns:
            float: Peso promedio en gramos (por defecto 100g si no se encuentra)
        """
        try:
            if not self.db:
                # Almacenamiento local en sesión
                from flask import session
                session_key = f'crops_{user_uid}'
                cultivos = session.get(session_key, [])
                for cultivo in cultivos:
                    if cultivo.get('id') == crop_id:
                        return cultivo.get('peso_promedio_gramos', 100.0)
                return 100.0  # Valor por defecto
            
            # Firestore
            crop_ref = self.db.collection('usuarios').document(user_uid).collection('cultivos').document(crop_id)
            crop_doc = crop_ref.get()
            if crop_doc.exists:
                cultivo = crop_doc.to_dict()
                return cultivo.get('peso_promedio_gramos', 100.0)
            
            return 100.0  # Valor por defecto
        except Exception as e:
            print(f"Error obteniendo peso promedio del cultivo {crop_id}: {e}")
            return 100.0

    def undo_last_production(self, user_uid: str, crop_id: str) -> bool:
        """
        Deshacer (eliminar) el último registro de producción del cultivo indicado.
        Soporta Firestore y almacenamiento local de sesión cuando no hay DB.
        """
        try:
            if not self.db:
                # Almacenamiento local en sesión
                from flask import session
                session_key = f'crops_{user_uid}'
                cultivos = session.get(session_key, [])
                for c in cultivos:
                    if c.get('id') == crop_id:
                        produccion = c.get('produccion_diaria', [])
                        if not produccion:
                            return False
                        produccion.pop()
                        c['produccion_diaria'] = produccion
                        # Recalcular agregados locales si existen
                        try:
                            kilos_total = sum(p.get('kilos', 0) for p in produccion)
                            c['kilos_totales'] = kilos_total
                            c['beneficio_total'] = kilos_total * c.get('precio_por_kilo', 0)
                        except Exception:
                            pass
                        session[session_key] = cultivos
                        return True
                return False

            # Firestore
            crop_ref = self.db.collection('usuarios').document(user_uid).collection('cultivos').document(crop_id)
            crop_doc = crop_ref.get()
            if not crop_doc.exists:
                return False
            cultivo = crop_doc.to_dict()
            produccion_actual = cultivo.get('produccion_diaria', [])
            if not produccion_actual:
                return False
            # Eliminar último elemento
            produccion_actual.pop()
            crop_ref.update({
                'produccion_diaria': produccion_actual,
                'actualizado_en': datetime.datetime.utcnow()
            })
            print(f"↩️ Deshecha última producción para cultivo {crop_id}")
            return True
        except Exception as e:
            print(f"Error deshaciendo última producción: {e}")
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
    
    def _get_peso_promedio_cultivo(self, user_uid: str, crop_id: str) -> float:
        """
        Obtener el peso promedio en gramos de un cultivo específico
        
        Args:
            user_uid (str): UID del usuario
            crop_id (str): ID del cultivo
            
        Returns:
            float: Peso promedio en gramos, 100 por defecto si no se encuentra
        """
        try:
            if not self.db:
                # Modo local
                from flask import session
                cultivos = session.get(f'crops_{user_uid}', [])
                for c in cultivos:
                    if c.get('id') == crop_id:
                        return float(c.get('peso_promedio_gramos', 100))
                return 100.0
            
            # Firestore
            crop_ref = self.db.collection('usuarios').document(user_uid).collection('cultivos').document(crop_id)
            crop_doc = crop_ref.get()
            if crop_doc.exists:
                cultivo = crop_doc.to_dict()
                return float(cultivo.get('peso_promedio_gramos', 100))
            return 100.0
            
        except Exception as e:
            print(f"Error obteniendo peso promedio: {e}")
            return 100.0
    
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
            from app.services.plan_service import PlanService
            
            plan_service = PlanService(self.db)
            
            print(f"🔍 Verificando límites de cultivos para usuario {user_uid[:8]}...")
            
            # Verificar límites usando el servicio de planes
            can_create = plan_service.check_plan_limits(user_uid, 'crops')
            
            print(f"{'✅' if can_create else '❌'} {'Puede' if can_create else 'No puede'} crear más cultivos")
            return can_create
            
        except Exception as e:
            print(f"❌ Error verificando límites: {e}")
            import traceback
            traceback.print_exc()
            # SOLUCIÓN TEMPORAL MEJORADA: Si hay error en la verificación, permitir crear cultivos
            # Esto evita que usuarios con plan gratuito tengan problemas
            print("🔧 Aplicando solución temporal: permitiendo creación de cultivo por error en verificación")
            return True
    
    def _process_cultivo_dates(self, cultivo: Dict) -> Dict:
        """Procesar fechas de cultivo para compatibilidad"""
        import datetime as _dt
        # Helper local para convertir a datetime cuando sea posible
        def _to_dt(value):
            try:
                # Si es objeto Timestamp de Firestore
                if hasattr(value, 'to_datetime') and callable(getattr(value, 'to_datetime')):
                    return value.to_datetime()
            except Exception:
                pass
            # Si ya es datetime, devolver tal cual
            if isinstance(value, _dt.datetime):
                return value
            # Si viene como string ISO
            if isinstance(value, str):
                try:
                    return _dt.datetime.fromisoformat(value)
                except Exception:
                    return value
            return value

        # Convertir timestamps/strings de Firestore a datetime si es necesario
        for field in ['fecha_siembra', 'fecha_cosecha', 'creado_en', 'actualizado_en']:
            if field in cultivo and cultivo[field]:
                cultivo[field] = _to_dt(cultivo[field])
        
        # Procesar fechas en produccion_diaria
        if 'produccion_diaria' in cultivo:
            for produccion in cultivo['produccion_diaria']:
                if 'fecha' in produccion and produccion['fecha']:
                    produccion['fecha'] = _to_dt(produccion['fecha'])
                # Normalizar kilos a float
                if 'kilos' in produccion:
                    try:
                        produccion['kilos'] = float(produccion['kilos'])
                    except Exception:
                        pass
        
        return cultivo
    
    # ==========================================
    # MÉTODOS PARA USUARIOS LOCALES (SIN FIREBASE)
    # ==========================================
    
    def get_local_user_crops(self, user_uid: str) -> List[Dict]:
        """
        Obtener cultivos de usuario local (guardados en sesión)
        
        Args:
            user_uid (str): UID del usuario local
            
        Returns:
            List[Dict]: Lista de cultivos del usuario
        """
        from flask import session
        
        # Obtener cultivos de la sesión
        session_key = f'crops_{user_uid}'
        cultivos = session.get(session_key, [])
        
        # Procesar fechas y añadir IDs si no los tienen
        for i, cultivo in enumerate(cultivos):
            if 'id' not in cultivo:
                cultivo['id'] = f"local_{i}_{cultivo.get('nombre', 'cultivo')}"
            
            # Convertir strings de fecha a datetime si es necesario
            if isinstance(cultivo.get('fecha_siembra'), str):
                try:
                    cultivo['fecha_siembra'] = datetime.datetime.fromisoformat(cultivo['fecha_siembra'])
                except:
                    cultivo['fecha_siembra'] = datetime.datetime.utcnow()
        
        return cultivos
    
    def create_local_crop(self, user_uid: str, crop_data: Dict) -> bool:
        """
        Crear cultivo para usuario local (sin Firebase)
        
        Args:
            user_uid (str): UID del usuario local
            crop_data (Dict): Datos del cultivo
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            from flask import session
            
            # Preparar datos del cultivo
            cultivo = {
                'id': f"local_{len(self.get_local_user_crops(user_uid))}_{crop_data.get('nombre', 'cultivo')}",
                'nombre': crop_data.get('nombre', '').lower().strip(),
                'fecha_siembra': datetime.datetime.utcnow(),
                'fecha_cosecha': None,
                'precio_por_kilo': float(crop_data.get('precio', 0)),
                'numero_plantas': int(crop_data.get('numero_plantas', 1)),
                'peso_promedio_gramos': float(crop_data.get('peso_promedio', 100)),
                'abonos': [],
                'produccion_diaria': [],
                'activo': True,
                'creado_en': datetime.datetime.utcnow(),
                'kilos_totales': 0,
                'beneficio_total': 0
            }
            
            # Obtener cultivos actuales
            session_key = f'crops_{user_uid}'
            cultivos = session.get(session_key, [])
            
            # Añadir nuevo cultivo
            cultivos.append(cultivo)
            
            # Guardar en sesión
            session[session_key] = cultivos
            
            print(f"✅ Cultivo local '{cultivo['nombre']}' creado para usuario {user_uid}")
            return True
            
        except Exception as e:
            print(f"Error creando cultivo local: {e}")
            return False
    
    def get_local_user_totals(self, user_uid: str) -> Tuple[float, float]:
        """
        Calcular totales para usuario local
        
        Args:
            user_uid (str): UID del usuario local
            
        Returns:
            Tuple[float, float]: (total_kilos, total_beneficios)
        """
        cultivos = self.get_local_user_crops(user_uid)
        total_kilos = 0
        total_beneficios = 0
        
        for cultivo in cultivos:
            kilos = cultivo.get('kilos_totales', 0)
            precio = cultivo.get('precio_por_kilo', 0)
            total_kilos += kilos
            total_beneficios += kilos * precio
        
        return total_kilos, total_beneficios
