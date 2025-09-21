"""
Rutas de gestión de cultivos - SEGURAS
CRUD de cultivos con verificación de autenticación Firebase real
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from app.middleware.auth_middleware import require_auth, get_current_user, get_current_user_uid
from app.services.crop_service import CropService
from app.utils.helpers import get_plan_limits

crops_bp = Blueprint('crops', __name__)

# Guardia a nivel de blueprint: asegura autenticación antes de cualquier handler
@crops_bp.before_request
def _ensure_auth_crops_bp():
    # Permitir preflight y rutas estáticas si las hubiera
    from flask import request as _req, redirect as _redirect, url_for as _url_for, session as _session, g as _g, current_app as _ca
    if _req.method == 'OPTIONS':
        return None
    try:
        # Traza de entrada para diagnosticar por qué no redirige en no autenticados
        print(f"[crops.before_request] method={_req.method} path={_req.path} args={dict(_req.args)} cookies={list(_req.cookies.keys())}")
    except Exception:
        pass
    # Resolver UID si ya fue establecido por middleware; si no, comprobar señales de auth
    uid = None
    try:
        uid = (_g.current_user.get('uid') if getattr(_g, 'current_user', None) else None)
    except Exception:
        uid = None
    if not uid:
        uid = _session.get('user_uid')

    # Reconstrucción temprana desde cookies de respaldo si falta sesión pero hay cookies
    if not uid:
        try:
            backup_uid = _req.cookies.get('huerto_user_uid')
            backup_data = _req.cookies.get('huerto_user_data')
            if backup_uid:
                _session.permanent = True
                _session['user_uid'] = backup_uid
                _session['is_authenticated'] = True
                # Cargar mínimos desde cookie JSON si existe
                try:
                    import json as _json
                    bd = _json.loads(backup_data) if backup_data else {}
                except Exception:
                    bd = {}
                _session['user'] = {
                    'uid': backup_uid,
                    'email': bd.get('email'),
                    'name': bd.get('name') or (bd.get('email') or 'Usuario'),
                    'plan': bd.get('plan', 'gratuito')
                }
                _session.modified = True
                # Exponer en g para capas superiores
                try:
                    _g.current_user = _session['user']
                except Exception:
                    pass
                uid = backup_uid
                try:
                    print("[crops.before_request] Sesión reconstruida desde cookies de respaldo")
                except Exception:
                    pass
        except Exception:
            pass

    # Reconstrucción adicional: intentar extraer UID del Referer si aún no hay UID
    if not uid:
        try:
            ref = _req.headers.get('Referer') or _req.headers.get('Referer'.lower())
            if ref:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(ref)
                q = parse_qs(parsed.query or '')
                ref_uid = (q.get('uid') or q.get('user_uid') or [None])[0]
                if ref_uid:
                    _session.permanent = True
                    _session['user_uid'] = ref_uid
                    _session['is_authenticated'] = True
                    # Inicializar user mínimo
                    _session['user'] = _session.get('user') or {
                        'uid': ref_uid,
                        'email': None,
                        'name': 'Usuario',
                        'plan': 'gratuito'
                    }
                    _session.modified = True
                    try:
                        _g.current_user = _session['user']
                    except Exception:
                        pass
                    uid = ref_uid
                    try:
                        print("[crops.before_request] Sesión reconstruida desde Referer")
                    except Exception:
                        pass
        except Exception:
            pass
    # Permitir token de desarrollo en local
    dev_token = _req.args.get('dev_token')
    if dev_token == 'dev_123_local' and (_ca.config.get('ENV') == 'development' or _ca.debug):
        try:
            print("[crops.before_request] dev_token válido en desarrollo; permitiendo acceso")
        except Exception:
            pass
        return None
    # No redirigir desde aquí; dejar que @require_auth gestione autenticación/redirects.
    # Este hook solo reconstruye desde cookies si es posible y registra trazas.
    return None

@crops_bp.route('/')
def list_crops():
    """Listar cultivos del usuario (requiere autenticación)."""
    from flask import current_app, session
    # Trazas de diagnóstico de entrada
    try:
        print(f"[/crops/] IN - cookies={list((request.cookies or {}).keys())} has_session={bool(session.get('is_authenticated'))} session_uid={session.get('user_uid')} g_uid={get_current_user_uid()}")
    except Exception:
        pass

    # Defensa adicional: si falta UID, permitir seguir si hay señales de auth
    # para que @require_auth pueda reconstruir; evita redirecciones falsas post-acción
    user_uid_safe = get_current_user_uid() or session.get('user_uid')
    if not (session.get('is_authenticated') and session.get('user_uid')):
        # Comprobar señales de autent. presentes en la petición
        has_auth_header = bool(request.headers.get('Authorization'))
        has_firebase_cookie = 'firebase_id_token' in request.cookies
        has_user_cookie = 'huerto_user_uid' in request.cookies or 'huerto_user_data' in request.cookies
        has_uid_param = bool(request.args.get('uid') or request.args.get('user_uid'))
        came_from_auth = request.args.get('from') in ("login", "register")
        # Nueva señal: UID en el Referer
        try:
            from urllib.parse import urlparse, parse_qs
            ref = request.headers.get('Referer') or ''
            ref_q = parse_qs(urlparse(ref).query or '') if ref else {}
            has_uid_in_ref = bool((ref_q.get('uid') or ref_q.get('user_uid') or [None])[0])
        except Exception:
            has_uid_in_ref = False
        try:
            print(f"[/crops/] Sin sesión válida. señales: auth_header={has_auth_header} firebase_cookie={has_firebase_cookie} user_cookie={has_user_cookie} uid_param={has_uid_param} from_auth={came_from_auth} uid_in_ref={has_uid_in_ref}")
        except Exception:
            pass
        if not (has_auth_header or has_firebase_cookie or has_user_cookie or has_uid_param or came_from_auth or has_uid_in_ref):
            try:
                print("[/crops/] Refuerzo handler: sesión inválida SIN señales → redirect onboarding")
            except Exception:
                pass
            from flask import redirect as _redirect, url_for as _url_for
            # Redirigir al dashboard para rehidratar sesión, preservando uid si es posible
            try:
                from urllib.parse import urlparse, parse_qs
                ref = request.headers.get('Referer') or ''
                ref_q = parse_qs(urlparse(ref).query or '') if ref else {}
                ref_uid = (ref_q.get('uid') or ref_q.get('user_uid') or [None])[0]
            except Exception:
                ref_uid = None
            target_uid = (request.args.get('uid') or request.args.get('user_uid')
                          or ref_uid or session.get('user_uid')
                          or request.cookies.get('huerto_user_uid'))
            return _redirect(_url_for('main.dashboard', uid=target_uid) if target_uid else _url_for('main.dashboard'))
        # Hay señales, continuar; @require_auth ya validó antes de este punto
    try:
        print(f"[/crops/] Guardia en handler - user_uid_safe={user_uid_safe}")
    except Exception:
        pass
    if not user_uid_safe:
        # Si no hay UID pero hay señales de auth, permitir continuar (evitar falso logout)
        has_auth_header = bool(request.headers.get('Authorization'))
        has_firebase_cookie = 'firebase_id_token' in request.cookies
        has_user_cookie = 'huerto_user_uid' in request.cookies or 'huerto_user_data' in request.cookies
        has_uid_param = bool(request.args.get('uid') or request.args.get('user_uid'))
        came_from_auth = request.args.get('from') in ("login", "register")
        try:
            print(f"[/crops/] Sin UID seguro. señales: auth_header={has_auth_header} firebase_cookie={has_firebase_cookie} user_cookie={has_user_cookie} uid_param={has_uid_param} from_auth={came_from_auth}")
        except Exception:
            pass
        if not (has_auth_header or has_firebase_cookie or has_user_cookie or has_uid_param or came_from_auth):
            from flask import redirect, url_for
            # En ausencia total de señales, mejor volver al dashboard
            try:
                from urllib.parse import urlparse, parse_qs
                ref = request.headers.get('Referer') or ''
                ref_q = parse_qs(urlparse(ref).query or '') if ref else {}
                ref_uid = (ref_q.get('uid') or ref_q.get('user_uid') or [None])[0]
            except Exception:
                ref_uid = None
            target_uid = (request.args.get('uid') or request.args.get('user_uid')
                          or ref_uid or session.get('user_uid')
                          or request.cookies.get('huerto_user_uid'))
            return redirect(url_for('main.dashboard', uid=target_uid) if target_uid else url_for('main.dashboard'))

    # Usuario autenticado y UID seguro
    user_uid = (user_uid_safe or request.args.get('uid'))
    crop_service = CropService(current_app.db)

    # Usuario autenticado: usar Firestore si está disponible; si no, fallback local
    if current_app.db:
        cultivos = crop_service.get_user_crops(user_uid)
    else:
        cultivos = crop_service.get_local_user_crops(user_uid)
    return render_template('crops.html', cultivos=cultivos, user_uid=user_uid)

@crops_bp.route('/create', methods=['GET', 'POST'])
@require_auth
def create_crop():
    """Crear nuevo cultivo - REQUIERE AUTENTICACIÓN SEGURA"""
    from flask import current_app, session
    
    # Obtener usuario autenticado de forma segura
    user = get_current_user()
    # Resolver UID de forma robusta: contexto -> form/query -> cookie
    user_uid = (
        get_current_user_uid()
    or request.form.get('user_uid')
    or request.form.get('uid')  # aceptar nombre de campo 'uid' del formulario
        or request.args.get('uid')
        or request.cookies.get('huerto_user_uid')
    )
    
    print("👤 [/crops/create] Usuario autenticado:", user_uid)
    # El decorador @require_auth ya verificó la autenticación
    # Si llegamos aquí, el usuario está autenticado y user_uid es seguro

    # Si es POST, procesar creación y salir; si no, mostrar formulario (GET por defecto)
    if request.method == 'POST':
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
            # Redirección RELATIVA para no salir de web.app (evitar run.app)
            from flask import make_response
            resp = make_response('', 303)
            resp.headers['Location'] = '/crops/create'
            return resp

        try:
            crop_data['precio'] = float(crop_data['precio'])
            if crop_data['precio'] < 0:
                flash('El precio debe ser positivo', 'error')
                from flask import make_response
                resp = make_response('', 303)
                resp.headers['Location'] = '/crops/create'
                return resp

            crop_data['numero_plantas'] = int(crop_data['numero_plantas'])
            if crop_data['numero_plantas'] <= 0:
                flash('El número de plantas debe ser mayor a cero', 'error')
                from flask import make_response
                resp = make_response('', 303)
                resp.headers['Location'] = '/crops/create'
                return resp

            crop_data['peso_promedio'] = float(crop_data['peso_promedio'])
            if crop_data['peso_promedio'] <= 0:
                flash('El peso promedio debe ser mayor a cero', 'error')
                from flask import make_response
                resp = make_response('', 303)
                resp.headers['Location'] = '/crops/create'
                return resp
        except ValueError:
            flash('Precio, número de plantas o peso promedio inválido', 'error')
            from flask import make_response
            resp = make_response('', 303)
            resp.headers['Location'] = '/crops/create'
            return resp

        # Usar UID del usuario autenticado de forma segura
        # Si no hay DB (modo local), usar almacenamiento local como fallback
        if not current_app.db:
            success = crop_service.create_local_crop(user_uid, crop_data)
        else:
            success = crop_service.create_crop(user_uid, crop_data)
        print("✅ [/crops/create] Resultado creación:", success)

        if success:
            flash(f'Cultivo "{crop_data["nombre"]}" creado exitosamente', 'success')
            # PRG con 303 y redirección RELATIVA + uid para reforzar sesión
            from flask import make_response
            resp = make_response('', 303)
            resp.headers['Location'] = f"/crops/?uid={user_uid}"
            return resp
        else:
            flash('Error al crear cultivo. Verifica los límites de tu plan.', 'error')
            from flask import make_response
            resp = make_response('', 303)
            resp.headers['Location'] = '/crops/create'
            return resp

    # GET por defecto: mostrar formulario de creación
    return render_template('crops.html', show_create_form=True, user_uid=user_uid)

@crops_bp.route('/<crop_id>/production', methods=['POST'])
@require_auth
def update_production(crop_id):
    """Actualizar producción de un cultivo - SEGURO"""
    from flask import current_app
    crop_service = CropService(current_app.db)
    
    # Obtener UID del usuario autenticado (con fallbacks)
    user_uid = (
        get_current_user_uid()
        or request.form.get('user_uid')
        or request.form.get('uid')
        or request.args.get('uid')
        or request.cookies.get('huerto_user_uid')
    )
    
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

    # Obtener UID del usuario autenticado (con fallbacks)
    user_uid = (
        get_current_user_uid()
        or request.form.get('user_uid')
        or request.form.get('uid')
        or request.args.get('uid')
        or request.cookies.get('huerto_user_uid')
    )

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

    # Obtener UID del usuario autenticado de forma segura (con fallbacks)
    user_uid = (
        get_current_user_uid()
        or request.form.get('user_uid')
        or request.form.get('uid')
        or request.args.get('uid')
        or request.cookies.get('huerto_user_uid')
    )
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

    # Obtener UID del usuario autenticado de forma segura (con fallbacks)
    user_uid = (
        get_current_user_uid()
        or request.args.get('uid')
    )

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

    # Obtener UID del usuario autenticado de forma segura (con fallbacks)
    user_uid = (
        get_current_user_uid()
        or request.form.get('user_uid')
        or request.form.get('uid')
        or request.args.get('uid')
        or request.cookies.get('huerto_user_uid')
    )


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

    # Obtener UID del usuario autenticado de forma segura (con fallbacks)
    user_uid = (
        get_current_user_uid()
        or request.form.get('user_uid')
        or request.form.get('uid')
        or request.args.get('uid')
        or request.cookies.get('huerto_user_uid')
    )


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
    user_uid = (
        get_current_user_uid()
        or request.form.get('user_uid')
        or request.form.get('uid')
        or request.args.get('user_uid')
        or request.args.get('uid')
        or request.cookies.get('huerto_user_uid')
    )
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

    # Redirección con PRG y preservando uid para reforzar sesión
    from flask import make_response
    resp = make_response('', 303)
    # Incluir uid en la query para facilitar reconstrucción en /crops/
    target_uid = user_uid or get_current_user_uid() or request.args.get('uid') or request.cookies.get('huerto_user_uid')
    resp.headers['Location'] = f"/crops/?uid={target_uid}" if target_uid else "/crops/"
    return resp

@crops_bp.route('/api/user-crops')
@require_auth
def api_user_crops():
    """API para obtener cultivos del usuario (requiere autenticación)."""
    from flask import current_app
    
    user_uid = get_current_user_uid()
    crop_service = CropService(current_app.db)
    cultivos = crop_service.get_user_crops(user_uid)
    
    # Serializar cultivos para JSON
    cultivos_json = []
    for cultivo in cultivos:
        cultivo_data = {
            'id': cultivo['id'],
            'nombre': cultivo['nombre'],
            'precio_por_kilo': cultivo.get('precio_por_kilo'),
            'activo': cultivo.get('activo', True),
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

    # Resolver UID de forma robusta
    user = get_current_user()
    user_uid = get_current_user_uid() or request.args.get('user_uid')
    
    if not user_uid:
        flash('No se pudo identificar el usuario para mostrar el historial.', 'error')
        return redirect(url_for('auth.login'))

    cultivo = None
    if current_app.db:
        try:
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
        except Exception as e:
            print('Error obteniendo historial de cultivo (Firestore):', e)
    else:
        # Local: desde sesión
        try:
            cultivos = session.get(f'crops_{user_uid}', [])
            for c in cultivos:
                if c.get('id') == crop_id:
                    cultivo = c
                    break
        except Exception as e:
            print('Error obteniendo historial de cultivo (local):', e)

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
    user_uid = (
        get_current_user_uid()
        or request.form.get('user_uid')
        or request.form.get('uid')
        or request.args.get('uid')
        or request.cookies.get('huerto_user_uid')
    )
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
    # Redirección con PRG y preservando uid en la query
    from flask import make_response
    resp = make_response('', 303)
    target_uid = user_uid or get_current_user_uid() or request.args.get('uid') or request.cookies.get('huerto_user_uid')
    resp.headers['Location'] = f"/crops/?uid={target_uid}" if target_uid else "/crops/"
    return resp

@crops_bp.route('/<crop_id>/color', methods=['POST'])
@require_auth
def update_crop_color(crop_id):
    """Actualizar solo el color de un cultivo - para uso con AJAX"""
    user = get_current_user()
    user_uid = (
        get_current_user_uid()
        or request.form.get('user_uid')
        or request.form.get('uid')
        or request.args.get('uid')
        or request.cookies.get('huerto_user_uid')
    )
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
    user_uid = get_current_user_uid() or request.form.get('user_uid') or request.args.get('uid') or request.cookies.get('huerto_user_uid')
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
    # Redirección con PRG y preservando uid
    from flask import make_response
    resp = make_response('', 303)
    target_uid = user_uid or get_current_user_uid() or request.args.get('uid') or request.cookies.get('huerto_user_uid')
    resp.headers['Location'] = f"/crops/?uid={target_uid}" if target_uid else "/crops/"
    return resp
