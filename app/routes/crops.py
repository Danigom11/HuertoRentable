"""
Rutas de gestión de cultivos
CRUD de cultivos con verificación de planes
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.auth.auth_service import login_required, get_current_user
from app.services.crop_service import CropService
from app.utils.helpers import get_plan_limits

crops_bp = Blueprint('crops', __name__)

@crops_bp.route('/')
def list_crops():
    """Listar cultivos del usuario (modo demo disponible)"""
    from flask import current_app, session
    
    # Detectar usuario primero y solo forzar demo si se pide explícitamente por URL
    user = get_current_user()
    demo_mode = request.args.get('demo') == 'true'
    crop_service = CropService(current_app.db)
    
    if demo_mode:
        # Modo demo: cultivos de ejemplo
        cultivos = crop_service.get_demo_crops()
        return render_template('crops.html', cultivos=cultivos, demo_mode=True, user_uid=None)
    elif user:
        # Usuario autenticado: verificar si es local o Firebase
        if user.get('is_local'):
            cultivos = crop_service.get_local_user_crops(user['uid'])
        else:
            cultivos = crop_service.get_user_crops(user['uid'])
        return render_template('crops.html', cultivos=cultivos, demo_mode=False, user_uid=user['uid'])
    else:
        # Sin usuario: NO activar demo automáticamente
        # Intentar obtener UID de respaldo desde cookies o parámetros de URL y mostrar sus cultivos (solo lectura)
        tentative_uid = request.cookies.get('huerto_user_uid') or request.args.get('uid')
        cultivos = []
        if tentative_uid:
            try:
                cultivos = crop_service.get_user_crops(tentative_uid)
            except Exception as e:
                print('⚠️ Error cargando cultivos con uid tentativo:', e)
        return render_template('crops.html', cultivos=cultivos, demo_mode=False, user_uid=tentative_uid)

@crops_bp.route('/create', methods=['GET', 'POST'])
def create_crop():
    """Crear nuevo cultivo (requiere autenticación)"""
    from flask import current_app, session
    
    # Diagnóstico de cookies/sesión
    try:
        print("🌐 [/crops/create] Cookies:", dict(request.cookies))
        print("🌐 [/crops/create] Session keys:", list(session.keys()))
    except Exception:
        pass

    user = get_current_user()
    print("👤 [/crops/create] Usuario detectado:", bool(user), "UID:", (user or {}).get('uid'))
    
    if not user:
        # No autenticado: redirigir a login manteniendo next
        if request.method == 'POST':
            flash('Inicia sesión para crear cultivos.', 'info')
        return redirect(url_for('auth.login', next=url_for('crops.list_crops')))
    
    if request.method == 'GET':
        print("🌐 [/crops/create:GET] Cookies:", dict(request.cookies))
        # Redirigir a la lista donde está el modal y contexto completos
        return redirect(url_for('crops.list_crops'))
    
    # POST request - crear cultivo
    crop_service = CropService(current_app.db)
    print("🗄️ [/crops/create] DB disponible:", bool(current_app.db))
    
    # Obtener datos del formulario
    crop_data = {
        'nombre': request.form.get('nombre', '').strip(),
        'precio': request.form.get('precio', 0),
        'numero_plantas': request.form.get('numero_plantas', 0),
        'peso_promedio': request.form.get('peso_promedio', 0)
    }
    
    # Validaciones
    if not crop_data['nombre']:
        flash('El nombre del cultivo es obligatorio', 'error')
        return redirect(url_for('crops.create_crop'))
    
    try:
        crop_data['precio'] = float(crop_data['precio'])
        if crop_data['precio'] < 0:
            flash('El precio debe ser positivo', 'error')
            return redirect(url_for('crops.create_crop'))
        
        crop_data['numero_plantas'] = int(crop_data['numero_plantas'])
        if crop_data['numero_plantas'] <= 0:
            flash('El número de plantas debe ser mayor a cero', 'error')
            return redirect(url_for('crops.create_crop'))
            
        crop_data['peso_promedio'] = float(crop_data['peso_promedio'])
        if crop_data['peso_promedio'] <= 0:
            flash('El peso promedio debe ser mayor a cero', 'error')
            return redirect(url_for('crops.create_crop'))
    except ValueError:
        flash('Precio, número de plantas o peso promedio inválido', 'error')
        return redirect(url_for('crops.create_crop'))
    
    # Decidir backend de almacenamiento: priorizar Firestore si hay DB y UID
    target_uid = (user or {}).get('uid') or request.form.get('uid') or request.args.get('uid') or request.cookies.get('huerto_user_uid')
    use_firebase = bool(getattr(current_app, 'db', None)) and bool(target_uid)
    print(f"🧭 [/crops/create] UID destino: {target_uid} | Backend: {'Firebase' if use_firebase else 'Local'}")

    if use_firebase:
        success = crop_service.create_crop(target_uid, crop_data)
    else:
        # Guardado local como último recurso (solo para invitados sin DB)
        if not target_uid:
            # Generar un uid temporal si no existe
            import uuid
            target_uid = f"guest_{uuid.uuid4().hex[:8]}"
        success = crop_service.create_local_crop(target_uid, crop_data)
    print("✅ [/crops/create] Resultado creación:", success)
    
    if success:
        flash(f'Cultivo "{crop_data["nombre"]}" creado exitosamente', 'success')
        # Incluir uid en la redirección para reconstruir contexto aunque el navegador no envíe cookies
        return redirect(url_for('crops.list_crops', uid=target_uid))
    else:
        flash('Error al crear cultivo. Verifica los límites de tu plan.', 'error')
        return redirect(url_for('crops.create_crop'))

@crops_bp.route('/<crop_id>/production', methods=['POST'])
def update_production(crop_id):
    """Actualizar producción de un cultivo (admite kilos y/o unidades con fallback de UID)."""
    from flask import current_app
    crop_service = CropService(current_app.db)

    # Resolver UID de forma robusta
    user = get_current_user()
    uid = (user or {}).get('uid') or request.form.get('uid') or request.args.get('uid') or request.cookies.get('huerto_user_uid')
    if not uid:
        flash('Debes iniciar sesión para registrar producción', 'error')
        return redirect(url_for('auth.login'))

    # Obtener kilos y unidades desde form o JSON
    kilos_raw = request.form.get('kilos')
    unidades_raw = request.form.get('unidades')
    if request.is_json:
        body = request.get_json(silent=True) or {}
        kilos_raw = body.get('kilos', kilos_raw)
        unidades_raw = body.get('unidades', unidades_raw)

    kilos = None
    unidades = None
    try:
        if kilos_raw not in (None, ''):
            kilos = float(kilos_raw)
    except Exception:
        kilos = None
    try:
        if unidades_raw not in (None, ''):
            unidades = int(unidades_raw)
    except Exception:
        unidades = None

    if (kilos is None or kilos <= 0) and (unidades is None or unidades <= 0):
        flash('Indica kilos o unidades válidos (> 0)', 'error')
        return redirect(url_for('main.dashboard', uid=uid))

    ok = crop_service.update_production_generic(uid, crop_id, kilos=kilos, unidades=unidades)
    if ok:
        flash('Producción registrada', 'success')
    else:
        flash('No se pudo registrar la producción', 'error')

    # Volver al dashboard manteniendo uid para contextos sin cookies
    return redirect(url_for('main.dashboard', uid=uid))

@crops_bp.route('/<crop_id>/production/undo', methods=['POST'])
def undo_last_production(crop_id):
    """Deshacer la última producción registrada para un cultivo."""
    from flask import current_app
    crop_service = CropService(current_app.db)

    user = get_current_user()
    uid = (user or {}).get('uid') or request.form.get('uid') or request.args.get('uid') or request.cookies.get('huerto_user_uid')
    if not uid:
        flash('Debes iniciar sesión para deshacer producción', 'error')
        return redirect(url_for('auth.login'))

    ok = crop_service.undo_last_production(uid, crop_id)
    if ok:
        flash('Última recolección deshecha', 'success')
    else:
        flash('No hay recolecciones para deshacer', 'warning')

    return redirect(url_for('main.dashboard', uid=uid))

@crops_bp.route('/api/user-crops')
def api_user_crops():
    """API para obtener cultivos del usuario (modo demo disponible)"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    if user:
        cultivos = crop_service.get_user_crops(user['uid'])
    else:
        cultivos = crop_service.get_demo_crops()
    
    # Serializar cultivos para JSON
    cultivos_json = []
    for cultivo in cultivos:
        cultivo_data = {
            'id': cultivo['id'],
            'nombre': cultivo['nombre'],
            'precio_por_kilo': cultivo['precio_por_kilo'],
            'activo': cultivo['activo'],
            'total_kilos': sum(p.get('kilos', 0) for p in cultivo.get('produccion_diaria', []))
        }
        cultivos_json.append(cultivo_data)
    
    return jsonify(cultivos_json)

@crops_bp.route('/<crop_id>/history')
def crop_history(crop_id):
    """Vista de historial completo de un cultivo con gráfica y lista de registros."""
    from flask import current_app, session
    crop_service = CropService(current_app.db)

    # Detectar modo demo
    demo_mode = request.args.get('demo') == 'true' or session.get('demo_mode_chosen', False)
    
    # Resolver UID de forma robusta
    user = get_current_user()
    uid = (user or {}).get('uid') or request.args.get('uid') or request.cookies.get('huerto_user_uid')
    
    # En modo demo, usar datos demo
    if demo_mode and not uid:
        uid = 'demo-user'
    
    if not uid:
        flash('No se pudo identificar el usuario para mostrar el historial.', 'error')
        return redirect(url_for('auth.login'))

    cultivo = None
    try:
        if demo_mode:
            # Cargar datos de demo
            demo_crops = crop_service.get_demo_crops()
            for demo_crop in demo_crops:
                if demo_crop.get('id') == crop_id:
                    cultivo = demo_crop
                    break
        elif current_app.db:
            doc_ref = current_app.db.collection('usuarios').document(uid).collection('cultivos').document(crop_id)
            doc = doc_ref.get()
            if doc.exists:
                cultivo = doc.to_dict()
                cultivo['id'] = doc.id
                # Normalizar fechas como hace el servicio
                try:
                    cultivo = crop_service._process_cultivo_dates(cultivo)  # noqa: SLF001 uso intencional
                except Exception:
                    pass
        else:
            # Local: desde sesión
            cultivos = session.get(f'crops_{uid}', [])
            for c in cultivos:
                if c.get('id') == crop_id:
                    cultivo = c
                    break
    except Exception as e:
        print('Error obteniendo historial de cultivo:', e)

    if not cultivo:
        flash('Cultivo no encontrado o sin acceso.', 'error')
        return redirect(url_for('main.dashboard', uid=uid))

    # Preparar datos para la gráfica y listado: fechas vs unidades y filas formateadas
    registros_raw = sorted((cultivo.get('produccion_diaria') or []), key=lambda r: r.get('fecha') or 0)
    labels: list[str] = []
    unidades: list[int] = []
    kilos_list: list[float] = []
    registros_view = []
    for r in registros_raw:
        fecha = r.get('fecha')
        try:
            if hasattr(fecha, 'to_datetime') and callable(getattr(fecha, 'to_datetime')):
                fecha = fecha.to_datetime()
        except Exception:
            pass
        # Formato legible
        try:
            etiqueta = fecha.strftime('%Y-%m-%d %H:%M') if fecha else 'N/A'
            fecha_str = fecha.strftime('%d/%m/%Y') if fecha else '—'
            hora_str = fecha.strftime('%H:%M') if fecha else '—'
        except Exception:
            etiqueta = str(fecha)
            fecha_str = etiqueta
            hora_str = ''
        labels.append(etiqueta)
        unidades_val = int(r.get('unidades', 0) or 0)
        unidades.append(unidades_val)
        kilos_val = float(r.get('kilos', 0) or 0)
        kilos_list.append(kilos_val)
        registros_view.append({
            'fecha_str': fecha_str,
            'hora_str': hora_str,
            'unidades': unidades_val,
            'kilos': kilos_val
        })

    # Construir objeto chart_data al estilo analytics para robustez en front
    chart_data = {
        'labels': labels,
        'unidades': unidades,
        'kilos': kilos_list,
    }

    return render_template(
        'crop_history.html',
        cultivo=cultivo,
        chart_data=chart_data,
        registros_view=registros_view,
        uid=uid
    )

# Endpoints básicos de edición y borrado (POST para simplicidad)
@crops_bp.route('/<crop_id>/edit', methods=['POST'])
def edit_crop(crop_id):
    """Editar nombre, precio y número de plantas"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login', next=url_for('crops.list_crops')))
    from flask import current_app
    crop_service = CropService(current_app.db)
    try:
        nombre = request.form.get('nombre', '').strip()
        precio = float(request.form.get('precio', 0))
        numero_plantas = int(request.form.get('numero_plantas', 1))
        if not nombre or precio < 0 or numero_plantas <= 0:
            flash('Datos inválidos', 'error')
            return redirect(url_for('crops.list_crops'))
        # Actualizar en Firestore
        if current_app.db:
            crop_ref = current_app.db.collection('usuarios').document(user['uid']).collection('cultivos').document(crop_id)
            crop_ref.update({
                'nombre': nombre.lower(),
                'precio_por_kilo': precio,
                'numero_plantas': numero_plantas,
                'actualizado_en': __import__('datetime').datetime.utcnow()
            })
        flash('Cultivo actualizado', 'success')
    except Exception as e:
        print('Error editando cultivo:', e)
        flash('Error editando cultivo', 'error')
    return redirect(url_for('crops.list_crops'))

@crops_bp.route('/<crop_id>/delete', methods=['POST'])
def delete_crop(crop_id):
    """Borrado suave: marcar activo=False"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login', next=url_for('crops.list_crops')))
    from flask import current_app
    try:
        if current_app.db:
            crop_ref = current_app.db.collection('usuarios').document(user['uid']).collection('cultivos').document(crop_id)
            crop_ref.update({
                'activo': False,
                'actualizado_en': __import__('datetime').datetime.utcnow()
            })
        flash('Cultivo eliminado', 'success')
    except Exception as e:
        print('Error eliminando cultivo:', e)
        flash('Error eliminando cultivo', 'error')
    return redirect(url_for('crops.list_crops'))
