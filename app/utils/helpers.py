"""
Funciones de utilidad y helpers
Configuración de planes, límites y funciones auxiliares
"""
from flask import current_app

def get_plan_limits(plan_name: str) -> dict:
    """
    Obtener límites y características de un plan
    
    Args:
        plan_name (str): Nombre del plan ('invitado', 'gratuito', 'premium')
        
    Returns:
        dict: Configuración del plan
    """
    plan_configs = {
        'invitado': current_app.config['PLAN_INVITADO'],
        'gratuito': current_app.config['PLAN_GRATUITO'], 
        'premium': current_app.config['PLAN_PREMIUM']
    }
    
    return plan_configs.get(plan_name, plan_configs['invitado'])

def format_currency(amount: float) -> str:
    """
    Formatear cantidad como moneda en euros
    
    Args:
        amount (float): Cantidad a formatear
        
    Returns:
        str: Cantidad formateada (ej: "€15.50")
    """
    return f"€{amount:.2f}"

def format_weight(kilos: float) -> str:
    """
    Formatear peso en kilogramos
    
    Args:
        kilos (float): Peso en kilogramos
        
    Returns:
        str: Peso formateado (ej: "15.5kg")
    """
    return f"{kilos:.1f}kg"

def calculate_days_since(date_obj) -> int:
    """
    Calcular días transcurridos desde una fecha
    
    Args:
        date_obj: Objeto datetime
        
    Returns:
        int: Número de días
    """
    import datetime
    if not date_obj:
        return 0
    
    if hasattr(date_obj, 'timestamp'):
        # Es un timestamp de Firestore
        date_obj = date_obj.to_datetime()
    
    today = datetime.datetime.utcnow()
    delta = today - date_obj
    return delta.days

def should_show_ads(plan: str, action_count: int = 0) -> bool:
    """
    Determinar si mostrar anuncios según el plan y acciones
    
    Args:
        plan (str): Plan del usuario
        action_count (int): Número de acciones realizadas
        
    Returns:
        bool: True si debe mostrar anuncios
    """
    if plan == 'premium':
        return False
    
    if plan == 'invitado':
        # Anuncios cada 3 acciones para invitados
        return action_count > 0 and action_count % 3 == 0
    
    if plan == 'gratuito':
        # Solo banner inferior para usuarios gratuitos
        return True
    
    return True

def generate_crop_emoji(crop_name: str) -> str:
    """
    Generar emoji apropiado para un cultivo
    
    Args:
        crop_name (str): Nombre del cultivo
        
    Returns:
        str: Emoji correspondiente
    """
    emoji_map = {
        'tomate': '🍅',
        'tomates': '🍅',
        'lechuga': '🥬',
        'lechugas': '🥬',
        'zanahoria': '🥕',
        'zanahorias': '🥕',
        'pepino': '🥒',
        'pepinos': '🥒',
        'pimiento': '🌶️',
        'pimientos': '🌶️',
        'calabaza': '🎃',
        'calabazas': '🎃',
        'berenjena': '🍆',
        'berenjenas': '🍆',
        'cebolla': '🧅',
        'cebollas': '🧅',
        'ajo': '🧄',
        'ajos': '🧄',
        'maiz': '🌽',
        'patata': '🥔',
        'patatas': '🥔',
        'fresa': '🍓',
        'fresas': '🍓',
        'manzana': '🍎',
        'manzanas': '🍎'
    }
    
    return emoji_map.get(crop_name.lower(), '🌱')

def validate_email(email: str) -> bool:
    """
    Validar formato de email
    
    Args:
        email (str): Email a validar
        
    Returns:
        bool: True si es válido
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(text: str) -> str:
    """
    Limpiar y sanitizar input del usuario
    
    Args:
        text (str): Texto a sanitizar
        
    Returns:
        str: Texto limpio
    """
    if not text:
        return ""
    
    # Eliminar caracteres peligrosos y espacios extra
    import re
    text = re.sub(r'[<>"\';]', '', text)
    return text.strip()

def get_user_tier_benefits(plan: str) -> list:
    """
    Obtener lista de beneficios de un plan
    
    Args:
        plan (str): Nombre del plan
        
    Returns:
        list: Lista de beneficios
    """
    benefits = {
        'invitado': [
            'Hasta 3 cultivos',
            'Datos en local', 
            'Funciones básicas'
        ],
        'gratuito': [
            'Cultivos ilimitados',
            'Backup en la nube',
            'Analytics básicos',
            'Sincronización multi-dispositivo'
        ],
        'premium': [
            'Todo de Gratuito +',
            'Sin anuncios',
            'Analytics avanzados',
            'Recordatorios push',
            'Exportar datos PDF/Excel',
            'Modo offline completo',
            'Soporte prioritario'
        ]
    }
    
    return benefits.get(plan, benefits['invitado'])

def calculate_roi(inversion: float, beneficios: float) -> float:
    """
    Calcular retorno de inversión (ROI)
    
    Args:
        inversion (float): Inversión inicial
        beneficios (float): Beneficios obtenidos
        
    Returns:
        float: ROI en porcentaje
    """
    if inversion <= 0:
        return 0
    
    return ((beneficios - inversion) / inversion) * 100
