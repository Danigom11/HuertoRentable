#!/usr/bin/env python3
"""
Script de diagnóstico para probar la creación de cultivos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.crop_service import CropService
from app.auth.auth_service import UserService
from app.services.plan_service import PlanService

def test_crop_creation():
    """Probar la creación de cultivos paso a paso"""
    print("🧪 Iniciando test de creación de cultivos...")
    
    # Crear aplicación
    app, db = create_app()
    app.db = db
    
    with app.app_context():
        print(f"📊 Estado Firebase: {'✅ Conectado' if db else '❌ Sin conexión'}")
        
        if not db:
            print("❌ No hay conexión a Firebase, no se puede continuar")
            return
        
        # Datos de prueba
        test_uid = "test_user_debug_123"
        crop_data = {
            'nombre': 'tomates de prueba',
            'precio': 3.50,
            'numero_plantas': 10
        }
        
        print(f"👤 Testeando con UID: {test_uid}")
        print(f"🌱 Datos del cultivo: {crop_data}")
        
        # Servicios
        user_service = UserService(db)
        crop_service = CropService(db)
        plan_service = PlanService(db)
        
        # 1. Verificar/crear usuario de prueba
        print("\n1️⃣ Verificando usuario...")
        user = user_service.get_user_by_uid(test_uid)
        if not user:
            print("   Creando usuario de prueba...")
            user_data = {
                'uid': test_uid,
                'email': 'test@debug.com',
                'name': 'Usuario Debug',
                'plan': 'gratuito'
            }
            created = user_service.create_user(test_uid, user_data)
            print(f"   {'✅' if created else '❌'} Usuario creado: {created}")
        else:
            print(f"   ✅ Usuario existe: plan={user.get('plan', 'no especificado')}")
        
        # 2. Verificar plan
        print("\n2️⃣ Verificando plan...")
        plan = user_service.get_user_plan(test_uid)
        print(f"   📋 Plan del usuario: {plan}")
        
        plan_info = plan_service.get_plan_info(plan)
        print(f"   📊 Límites del plan: {plan_info.get('limits', {})}")
        
        # 3. Verificar cultivos existentes
        print("\n3️⃣ Verificando cultivos existentes...")
        existing_crops = crop_service.get_user_crops(test_uid)
        print(f"   🌱 Cultivos actuales: {len(existing_crops)}")
        
        # 4. Verificar límites
        print("\n4️⃣ Verificando límites...")
        can_create = plan_service.check_plan_limits(test_uid, 'crops')
        print(f"   {'✅' if can_create else '❌'} Puede crear cultivos: {can_create}")
        
        # 5. Intentar crear cultivo
        print("\n5️⃣ Intentando crear cultivo...")
        try:
            success = crop_service.create_crop(test_uid, crop_data)
            print(f"   {'✅' if success else '❌'} Resultado: {success}")
            
            if success:
                # Verificar que se creó
                updated_crops = crop_service.get_user_crops(test_uid)
                print(f"   🌱 Cultivos después de crear: {len(updated_crops)}")
                if updated_crops:
                    print(f"   📝 Último cultivo: {updated_crops[0].get('nombre', 'sin nombre')}")
            
        except Exception as e:
            print(f"   ❌ Error creando cultivo: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_crop_creation()
