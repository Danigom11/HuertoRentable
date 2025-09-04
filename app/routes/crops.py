"""
Rutas de gestión de cultivos - SEGURAS
CRUD de cultivos con verificación de autenticación Firebase real
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.middleware.auth_middleware import require_auth, get_current_user, get_current_user_uid, optional_auth
from app.services.crop_service import CropService
from app.utils.helpers import get_plan_limits

crops_bp = Blueprint('crops', __name__)

@crops_bp.route('/')
@optional_auth
def list_crops():
    """Listar cultivos del usuario (modo demo disponible) - SEGURO"""
    from flask import current_app, session
    
    # Obtener usuario autenticado de forma segura
    user = get_current_user()
    user_uid = get_current_user_uid()
    demo_mode = request.args.get('demo') == 'true'
    crop_service = CropService(current_app.db)
    
    if demo_mode:
        # Modo demo: cultivos de ejemplo
        cultivos = crop_service.get_demo_crops()
        return render_template('crops.html', cultivos=cultivos, demo_mode=True, user_uid=None)
    elif user and user_uid:
        # Usuario autenticado: usar user_uid desde middleware
        if user.get('is_local'):
            cultivos = crop_service.get_local_user_crops(user_uid)
        else:
            cultivos = crop_service.get_user_crops(user_uid)
        return render_template('crops.html', cultivos=cultivos, demo_mode=False, user_uid=user_uid)
    else:
        # Sin usuario: NO activar demo automáticamente
        # Intentar obtener UID de respaldo desde cookies o parámetros de URL y mostrar sus cultivos (solo lectura)
        tentative_uid = request.cookies.get('huerto_user_uid') or request.args.get('user_uid')
        cultivos = []
        if tentative_uid:
            try:
                cultivos = crop_service.get_user_crops(tentative_uid)
            except Exception as e:
                print('⚠️ Error cargando cultivos:', e)
        return render_template('crops.html', cultivos=cultivos, demo_mode=False, user_uid=tentative_uid)

@crops_bp.route('/create', methods=['GET', 'POST'])
@require_auth
def create_crop():
    """Crear nuevo cultivo - REQUIERE AUTENTICACIÓN SEGURA"""
    from flask import current_app, session
    
    # Obtener usuario autenticado de forma segura
    user = get_current_user()
    user_uid = get_current_user_uid()
    
    print("👤 [/crops/create] Usuario autenticado:", user_uid)
    # El decorador @require_auth ya verificó la autenticación
    # Si llegamos aquí, el usuario está autenticado y user_uid es seguro
    
    if request.method == 'GET':
        return render_template('crops.html', show_create_form=True)
    
    # POST request - crear cultivo SEGURO
    crop_service = CropService(current_app.db)
    print("🗄️ [/crops/create] DB disponible:", bool(current_app.db))
    
    # Obtener datos del formulario
    crop_data = {
        'nombre': request.form.get('nombre', '').strip(),
        'precio': request.form.get('precio', 0),
        'numero_plantas': request.form.get('numero_plantas', 0),
        'peso_promedio': request.form.get('peso_promedio', 0),
        'color_cultivo': request.form.get('color_cultivo', '#28a745')
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
    
    # Usar UID del usuario autenticado de forma segura
    # Ya no necesitamos verificar múltiples fuentes - el decorador garantiza autenticación
    success = crop_service.create_crop(user_uid, crop_data)
    print("✅ [/crops/create] Resultado creación:", success)
    
    if success:
        flash(f'Cultivo "{crop_data["nombre"]}" creado exitosamente', 'success')
        return redirect(url_for('crops.list_crops'))
    else:
        flash('Error al crear cultivo. Verifica los límites de tu plan.', 'error')
        return redirect(url_for('crops.create_crop'))

@crops_bp.route('/<crop_id>/production', methods=['POST'])
@require_auth
def update_production(crop_id):
    """Actualizar producción de un cultivo - SEGURO"""
    from flask import current_app
    crop_service = CropService(current_app.db)
    
    # Obtener UID del usuario autenticado
    user_uid = get_current_user_uid()
    
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
        return redirect(url_for('main.dashboard'))

    ok = crop_service.update_production_generic(user_uid, crop_id, kilos=kilos, unidades=unidades)
    if ok:
        flash('Producción registrada', 'success')
    else:
        flash('No se pudo registrar la producción', 'error')

    return redirect(url_for('main.dashboard'))

@crops_bp.route('/<crop_id>/production/undo', methods=['POST'])
@require_auth
def undo_last_production(crop_id):
    """Deshacer la última producción registrada - SEGURO"""
    from flask import current_app
    crop_service = CropService(current_app.db)

    # Obtener UID del usuario autenticado
    user_uid = get_current_user_uid()

    ok = crop_service.undo_last_production(user_uid, crop_id)
    if ok:
        flash('Última recolección deshecha', 'success')
    else:
        flash('No hay recolecciones para deshacer', 'warning')

    return redirect(url_for('main.dashboard'))

@crops_bp.route('/<crop_id>/abono', methods=['POST'])
@require_auth
def add_abono(crop_id):
    """Añadir abono a un cultivo - SEGURO"""
    from flask import current_app
    crop_service = CropService(current_app.db)

    # Obtener UID del usuario autenticado de forma segura
    user_uid = get_current_user_uid()
    user = get_current_user()

    # Obtener descripción del abono desde form o JSON
    descripcion = request.form.get('descripcion')
    if request.is_json:
        body = request.get_json(silent=True) or {}
        descripcion = body.get('descripcion', descripcion)

    if not descripcion or not descripcion.strip():
        return jsonify({'error': 'La descripción del abono es obligatoria'}), 400

    ok = crop_service.add_abono(user_uid, crop_id, descripcion.strip())
    if ok:
        return jsonify({'success': True, 'message': 'Abono añadido correctamente'})
    else:
        return jsonify({'error': 'No se pudo añadir el abono'}), 500

@crops_bp.route('/<crop_id>/abonos', methods=['GET'])
@require_auth
def get_abonos(crop_id):
    """Obtener historial de abonos de un cultivo."""
    from flask import current_app
    crop_service = CropService(current_app.db)

    # Obtener UID del usuario autenticado de forma segura
    user_uid = get_current_user_uid()

    try:
        abonos = crop_service.get_crop_abonos(user_uid, crop_id)
        return jsonify({'abonos': abonos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@crops_bp.route('/<crop_id>/abono/<int:abono_index>/edit', methods=['POST'])
@require_auth
def edit_abono(crop_id, abono_index):
    """Editar un abono específico de un cultivo."""
    from flask import current_app
    crop_service = CropService(current_app.db)

    # Obtener UID del usuario autenticado de forma segura


    user_uid = get_current_user_uid()


    user = get_current_user()

    # Obtener nueva descripción
    descripcion = request.form.get('descripcion')
    if request.is_json:
        body = request.get_json(silent=True) or {}
        descripcion = body.get('descripcion', descripcion)

    if not descripcion or not descripcion.strip():
        return jsonify({'error': 'La descripción del abono es obligatoria'}), 400

    ok = crop_service.edit_abono(user_uid, crop_id, abono_index, descripcion.strip())
    if ok:
        return jsonify({'success': True, 'message': 'Abono editado correctamente'})
    else:
        return jsonify({'error': 'No se pudo editar el abono'}), 500

@crops_bp.route('/<crop_id>/abono/<int:abono_index>/delete', methods=['POST'])
@require_auth
def delete_abono(crop_id, abono_index):
    """Eliminar un abono específico de un cultivo."""
    from flask import current_app
    crop_service = CropService(current_app.db)

    # Obtener UID del usuario autenticado de forma segura


    user_uid = get_current_user_uid()


    user = get_current_user()

    ok = crop_service.delete_abono(user_uid, crop_id, abono_index)
    if ok:
        return jsonify({'success': True, 'message': 'Abono eliminado correctamente'})
    else:
        return jsonify({'error': 'No se pudo eliminar el abono'}), 500

@crops_bp.route('/<crop_id>/finish', methods=['POST'])
@require_auth
def finish_crop(crop_id):
    """Finalizar un cultivo específico."""
    from flask import current_app
    import datetime
    crop_service = CropService(current_app.db)

    user = get_current_user()
    user_uid = get_current_user_uid() or request.form.get('user_uid') or request.args.get('user_uid') or request.cookies.get('huerto_user_uid')
    if not user_uid:
        flash('Debes iniciar sesión para finalizar cultivos', 'error')
        return redirect(url_for('auth.login'))

    try:
        # Obtener fecha de cosecha del formulario (opcional)
        fecha_cosecha_str = request.form.get('fecha_cosecha')
        if fecha_cosecha_str:
            fecha_cosecha = datetime.datetime.strptime(fecha_cosecha_str, '%Y-%m-%d')
        else:
            fecha_cosecha = datetime.datetime.utcnow()

        ok = crop_service.finish_crop(user_uid, crop_id, fecha_cosecha)
        if ok:
            flash('Cultivo finalizado exitosamente', 'success')
        else:
            flash('Error al finalizar el cultivo', 'error')
            
    except Exception as e:
        flash(f'Error inesperado: {str(e)}', 'error')
        print(f"Error en finish_crop: {e}")

    return redirect(url_for('crops.list_crops'))

@crops_bp.route('/api/user-crops')
def api_user_crops():
    """API para obtener cultivos del usuario (modo demo disponible)"""
    from flask import current_app
    
    user = get_current_user()
    user_uid = get_current_user_uid()
    crop_service = CropService(current_app.db)
    
    if user and user_uid:
        cultivos = crop_service.get_user_crops(user_uid)
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
@require_auth
def crop_history(crop_id):
    """Vista de historial completo de un cultivo con gráfica y lista de registros."""
    from flask import current_app, session
    crop_service = CropService(current_app.db)

    # Detectar modo demo
    demo_mode = request.args.get('demo') == 'true' or session.get('demo_mode_chosen', False)
    
    # Resolver UID de forma robusta
    user = get_current_user()
    user_uid = get_current_user_uid() or request.args.get('user_uid') or request.cookies.get('huerto_user_uid')
    
    # En modo demo, usar datos demo
    if demo_mode and not user_uid:
        user_uid = 'demo-user'
    
    if not user_uid:
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
            doc_ref = current_app.db.collection('usuarios').document(user_uid).collection('cultivos').document(crop_id)
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
            cultivos = session.get(f'crops_{user_uid}', [])
            for c in cultivos:
                if c.get('id') == crop_id:
                    cultivo = c
                    break
    except Exception as e:
        print('Error obteniendo historial de cultivo:', e)

    if not cultivo:
        flash('Cultivo no encontrado o sin acceso.', 'error')
        return redirect(url_for('main.dashboard', uid=user_uid))

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
        uid=user_uid
    )

# Endpoints básicos de edición y borrado (POST para simplicidad)
@crops_bp.route('/<crop_id>/edit', methods=['POST'])
@require_auth
def edit_crop(crop_id):
    """Editar nombre, precio y número de plantas"""
    user = get_current_user()
    user_uid = get_current_user_uid()
    if not user or not user_uid:
        return redirect(url_for('auth.login', next=url_for('crops.list_crops')))
    from flask import current_app
    crop_service = CropService(current_app.db)
    try:
        nombre = request.form.get('nombre', '').strip()
        precio = float(request.form.get('precio', 0))
        numero_plantas = int(request.form.get('numero_plantas', 1))
        peso_promedio = float(request.form.get('peso_promedio', 0))
        color_cultivo = request.form.get('color_cultivo', '#28a745')
        
        if not nombre or precio < 0 or numero_plantas <= 0 or peso_promedio <= 0:
            flash('Datos inválidos', 'error')
            return redirect(url_for('crops.list_crops'))
        # Actualizar en Firestore
        if current_app.db:
            crop_ref = current_app.db.collection('usuarios').document(user_uid).collection('cultivos').document(crop_id)
            crop_ref.update({
                'nombre': nombre.strip(),
                'precio_por_kilo': precio,
                'numero_plantas': numero_plantas,
                'peso_promedio': peso_promedio,
                'color_cultivo': color_cultivo,
                'actualizado_en': __import__('datetime').datetime.utcnow()
            })
        flash('Cultivo actualizado', 'success')
    except Exception as e:
        print('Error editando cultivo:', e)
        flash('Error editando cultivo', 'error')
    return redirect(url_for('crops.list_crops'))

@crops_bp.route('/<crop_id>/color', methods=['POST'])
@require_auth
def update_crop_color(crop_id):
    """Actualizar solo el color de un cultivo - para uso con AJAX"""
    user = get_current_user()
    user_uid = get_current_user_uid()
    if not user or not user_uid:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    from flask import current_app
    try:
        color = request.get_json().get('color') if request.is_json else request.form.get('color')
        if not color:
            return jsonify({'success': False, 'error': 'Color requerido'}), 400
        
        if current_app.db:
            crop_ref = current_app.db.collection('usuarios').document(user_uid).collection('cultivos').document(crop_id)
            crop_ref.update({
                'color_cultivo': color,
                'actualizado_en': __import__('datetime').datetime.utcnow()
            })
            return jsonify({'success': True, 'color': color})
        else:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
    except Exception as e:
        print('Error actualizando color:', e)
        return jsonify({'success': False, 'error': str(e)}), 500

@crops_bp.route('/<crop_id>/delete', methods=['POST'])
@require_auth
def delete_crop(crop_id):
    """Borrado suave: marcar activo=False"""
    user = get_current_user()
    user_uid = get_current_user_uid()
    if not user or not user_uid:
        return redirect(url_for('auth.login', next=url_for('crops.list_crops')))
    from flask import current_app
    try:
        if current_app.db:
            crop_ref = current_app.db.collection('usuarios').document(user_uid).collection('cultivos').document(crop_id)
            crop_ref.update({
                'activo': False,
                'actualizado_en': __import__('datetime').datetime.utcnow()
            })
        flash('Cultivo eliminado', 'success')
    except Exception as e:
        print('Error eliminando cultivo:', e)
        flash('Error eliminando cultivo', 'error')
    return redirect(url_for('crops.list_crops'))
