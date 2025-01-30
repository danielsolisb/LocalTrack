from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask import Blueprint
from . import db, login_manager
from .models import User, Intersection, Camera, LaneParameter, Measurement, TrafficController, Phase, Flow, AdaptiveControlConfig, AdaptiveResults, user_intersection   # Asegúrate de importar Intersection
from .forms import LoginForm, IntersectionForm, CameraForm, LaneParameterForm, TrafficControllerForm, AddUserForm, PhaseForm, FlowForm, AdaptiveControlForm
from .decorators import admin_required, supervisor_required
from werkzeug.security import check_password_hash, generate_password_hash
import pymysql

from datetime import datetime


routes = Blueprint('routes', __name__)  # Define un Blueprint para las rutas

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@routes.route('/')
def home():
    return redirect(url_for('routes.login'))

@routes.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@routes.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

@routes.route('/register')
@login_required
def register():
    return render_template('register.html')

# Configuración de intersecciones
@routes.route('/configuration', methods=['GET', 'POST'])
@login_required
@admin_required
def configuration():
    form = IntersectionForm()

    # Poblar el campo de usuarios
    all_users = User.query.all()
    form.users.choices = [(user.id, user.username) for user in all_users]

    cloud_intersections = []
    if request.method == 'POST' and 'sync_cloud' in request.form:
        cloud_intersections = fetch_intersections_from_cloud()
        if cloud_intersections is None:
            flash('No se pudo conectar con la base de datos en la nube.', 'danger')
        else:
            flash('Intersecciones sincronizadas desde la nube.', 'success')

    if form.validate_on_submit() and 'manual_submit' in request.form:
        # Guardar intersección manualmente con usuarios relacionados
        intersection = Intersection(
            name=form.name.data,
            address=form.address.data,
            province=form.province.data,
            canton=form.canton.data,
            coordinates=form.coordinates.data,
            cloud_id=form.cloud_id.data if form.cloud_id.data else None,
            num_phases=form.num_phases.data
        )

        # Relacionar usuarios seleccionados
        for user_id in form.users.data:
            user = User.query.get(user_id)
            if user:
                intersection.users.append(user)

        db.session.add(intersection)
        db.session.commit()
        flash('Intersección agregada manualmente.', 'success')
        return redirect(url_for('routes.configuration'))

    local_intersections = Intersection.query.all()
    return render_template(
        'configuration.html',
        form=form,
        local_intersections=local_intersections,
        cloud_intersections=cloud_intersections
    )

@routes.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = AddUserForm()

    if form.validate_on_submit():
        # Crear un nuevo usuario
        new_user = User(
            username=form.username.data,
            password=generate_password_hash(form.password.data),  # Hasheamos la contraseña
            role=form.role.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('routes.add_user'))

    # Obtener todos los usuarios existentes para mostrarlos en la tabla
    users = User.query.all()

    return render_template('add_user.html', form=form, users=users)

@routes.route('/add_controller', endpoint='add_controller',methods=['GET', 'POST'])
@login_required
@admin_required
def add_controller():
    form = TrafficControllerForm()

    # Poblar el campo Intersection en el formulario con las intersecciones disponibles
    form.intersection_id.choices = [(i.id, i.name) for i in Intersection.query.all()]

    if form.validate_on_submit():
        # Crear y guardar el nuevo controlador
        controller = TrafficController(
            name=form.name.data,
            identifier=form.identifier.data,
            ip_address=form.ip_address.data,
            intersection_id=form.intersection_id.data
        )
        db.session.add(controller)
        db.session.commit()
        flash('Traffic Controller added successfully!', 'success')
        return redirect(url_for('routes.add_controller'))

    # Obtener todos los controladores para mostrarlos en la tabla
    controllers = TrafficController.query.all()

    return render_template('add_controller.html', form=form, controllers=controllers)


@routes.route('/delete_controller/<int:controller_id>', methods=['POST'])
@login_required
@admin_required
def delete_controller(controller_id):
    controller = TrafficController.query.get_or_404(controller_id)

    # Verificar si tiene carriles relacionados
    lanes = LaneParameter.query.filter_by(controller_id=controller_id).all()
    for lane in lanes:
        db.session.delete(lane)  # Eliminar carriles relacionados

    try:
        db.session.delete(controller)
        db.session.commit()
        flash('Traffic controller deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting controller: {str(e)}', 'danger')

    return redirect(url_for('routes.add_controller'))

@routes.route('/add_adaptive_control/<int:controller_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def adaptive_control(controller_id):
    controller = TrafficController.query.get_or_404(controller_id)
    existing_config = AdaptiveControlConfig.query.filter_by(controller_id=controller_id).first()
    
    form = AdaptiveControlForm(obj=existing_config)  # Cargar datos existentes en el formulario
    
    if form.validate_on_submit():
        if existing_config:
            # Si ya existe, solo actualizar valores
            existing_config.saturation_flow = form.saturation_flow.data
            existing_config.amber_time = form.amber_time.data
            existing_config.clearance_time = form.clearance_time.data
            existing_config.green_time_1 = form.green_time_1.data if form.green_time_1.data is not None else 0
            existing_config.green_time_2 = form.green_time_2.data if form.green_time_2.data is not None else 0
            existing_config.green_time_3 = form.green_time_3.data if form.green_time_3.data is not None else 0
            existing_config.green_time_4 = form.green_time_4.data if form.green_time_4.data is not None else 0
        else:
            # Si no existe, crear una nueva
            config = AdaptiveControlConfig(
                controller_id=controller_id,
                saturation_flow=form.saturation_flow.data,
                amber_time=form.amber_time.data,
                clearance_time=form.clearance_time.data,
                green_time_1=form.green_time_1.data if form.green_time_1.data is not None else 0,
                green_time_2=form.green_time_2.data if form.green_time_2.data is not None else 0,
                green_time_3=form.green_time_3.data if form.green_time_3.data is not None else 0,
                green_time_4=form.green_time_4.data if form.green_time_4.data is not None else 0
            )
            db.session.add(config)
        
        db.session.commit()
        flash('Adaptive control configuration updated successfully!', 'success')
        return redirect(url_for('routes.adaptive_control', controller_id=controller_id))
    
    return render_template('add_adaptive_control.html', controller=controller, form=form, config=existing_config)


@routes.route('/delete_adaptive_control/<int:config_id>', methods=['POST'])
@login_required
@admin_required
def delete_adaptive_control(config_id):
    config = AdaptiveControlConfig.query.get_or_404(config_id)
    db.session.delete(config)
    db.session.commit()
    flash('Adaptive control configuration deleted successfully!', 'danger')
    return redirect(url_for('routes.adaptive_control', controller_id=config.controller_id))


@routes.route('/monitoring')
@login_required
@supervisor_required
def monitoring():
    return render_template('monitoring.html')


@routes.route('/add_camera', methods=['GET', 'POST'])
@login_required
@admin_required
def add_camera():
    
    form = CameraForm()

    # Obtener todas las intersecciones disponibles para el selector
    intersections = Intersection.query.all()
    form.intersection_id.choices = [(i.id, i.name) for i in intersections]

    if form.validate_on_submit():
        # Crear una nueva cámara con los datos del formulario
        camera = Camera(
            cam_id=form.cam_id.data,
            ip_address=form.ip_address.data,
            street=form.street.data,
            direction=form.direction.data,
            lanes=form.lanes.data,
            intersection_id=form.intersection_id.data
        )
        db.session.add(camera)
        db.session.commit()
        flash('Cámara agregada correctamente.', 'success')
        return redirect(url_for('routes.add_camera'))

    # Obtener todas las cámaras existentes
    cameras = Camera.query.all()

    return render_template('add_camera.html', form=form, cameras=cameras)

@routes.route('/delete_camera/<int:camera_id>', methods=['POST'])
@login_required
@admin_required
def delete_camera(camera_id):
    camera = Camera.query.get_or_404(camera_id)

    try:
        db.session.delete(camera)
        db.session.commit()
        flash('Camera deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting camera: {str(e)}', 'danger')

    return redirect(url_for('routes.add_camera'))  # Asegúrate de que esta URL sea la correcta en tu app.


@routes.route('/add_lane', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lane():
    form = LaneParameterForm()
    form.camera_id.choices = [(c.id, c.cam_id) for c in Camera.query.all()]
    form.flow_id.choices = [(f.id, f.name) for f in Flow.query.all()]  # Nueva relación

    if form.validate_on_submit():
        lane_parameter = LaneParameter(
            lane=form.lane.data,
            straight=form.straight.data,
            turn=form.turn.data,
            turn_direction=form.turn_direction.data if form.turn.data else None,
            camera_id=form.camera_id.data,
            flow_id=form.flow_id.data  # Nuevo campo
        )
        db.session.add(lane_parameter)
        db.session.commit()
        flash('Lane Parameter added successfully!', 'success')
        return redirect(url_for('routes.add_lane'))

    lane_parameters = LaneParameter.query.all()
    return render_template('add_lane.html', form=form, lane_parameters=lane_parameters)

@routes.route('/delete_lane_parameter/<int:lane_id>', methods=['POST'])
@login_required
@admin_required
def delete_lane_parameter(lane_id):
    lane = LaneParameter.query.get_or_404(lane_id)

    db.session.delete(lane)
    db.session.commit()

    flash('Lane parameter deleted successfully!', 'success')
    return redirect(url_for('routes.add_lane'))


@routes.route('/measurements', endpoint='measurements', methods=['GET'])
@login_required
@supervisor_required
def measurements():
    # Obtener todos los carriles con sus cámaras asociadas
    lanes = LaneParameter.query.join(Camera).all()

    # Obtener parámetros de búsqueda
    lane_id = request.args.get('lane', type=int)
    start_date = request.args.get('start_date')  # Formato esperado: YYYY-MM-DD
    end_date = request.args.get('end_date')  # Formato esperado: YYYY-MM-DD

    # Base de la consulta
    query = Measurement.query

    # Aplicar filtros correctamente
    if lane_id:
        lane_param = LaneParameter.query.get(lane_id)  # Obtener el objeto LaneParameter
        if lane_param:
            query = query.filter(Measurement.lane == lane_param.lane)  # Filtrar por número de carril
            print(query)

    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Measurement.timestamp >= start_date)
        except ValueError:
            flash('Invalid start date format.', 'danger')

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Measurement.timestamp <= end_date)
        except ValueError:
            flash('Invalid end date format.', 'danger')

    # Obtener resultados y verificar si hay datos
    measurements = query.all()
    print(measurements)  # Depuración para ver si realmente hay datos

    return render_template('measurements.html', lanes=lanes, measurements=measurements)

@routes.route('/adaptive_results', methods=['GET', 'POST'])
@login_required
@admin_required
def adaptive_results():
    # Obtener los controladores del usuario logeado a través de las intersecciones que administra
    controllers = TrafficController.query.join(Intersection).join(user_intersection).filter(
        user_intersection.c.user_id == current_user.id
    ).all()

    # Inicializar variables
    results = None
    selected_controller = None

    # Si el usuario selecciona un controlador y envía el formulario
    if request.method == 'POST':
        controller_id = request.form.get('controller_id')

        # Filtrar el controlador seleccionado asegurando que pertenece a una intersección del usuario
        selected_controller = TrafficController.query.join(Intersection).join(user_intersection).filter(
            TrafficController.id == controller_id,
            user_intersection.c.user_id == current_user.id
        ).first()

        if selected_controller:
            results = AdaptiveResults.query.filter_by(controller_id=selected_controller.id).all()
        else:
            flash("Invalid selection or no access to this controller.", "danger")

    return render_template('adaptive_results.html', controllers=controllers, selected_controller=selected_controller, results=results)


#@routes.route('/measurements', endpoint='measurements', methods=['GET'])
#@login_required
#@supervisor_required
#def measurements():
#    # Obtener todos los carriles con sus cámaras asociadas
#    lanes = LaneParameter.query.join(Camera).all()
#
#    # Filtros opcionales
#    lane_id = request.args.get('lane', type=int)
#    start_date = request.args.get('start_date')  # Formato esperado: YYYY-MM-DD
#    end_date = request.args.get('end_date')  # Formato esperado: YYYY-MM-DD
#
#    # Base de la consulta
#    query = Measurement.query
#
#    # Aplicar filtros
#    if lane_id:
#        query = query.filter_by(lane=lane_id)
#    if start_date:
#        query = query.filter(Measurement.timestamp >= start_date)
#    if end_date:
#        query = query.filter(Measurement.timestamp <= end_date)
#
#    # Obtener resultados
#    measurements = query.all()
#    print(measurements)
#
#    return render_template('measurements.html', lanes=lanes, measurements=measurements)
#--------------------------------#
# FUNCIONES EXTRAS #
def fetch_intersections_from_cloud():
    try:
        # Establecer la conexión
        connection = pymysql.connect(
            host="35.222.201.195",
            user="root",
            password="daniel586",
            database="FlowTrack",  # Nombre de la base de datos
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            query = """
            SELECT id, name, address, province, canton, coordinates
            FROM Portal_intersection
            """
            cursor.execute(query)
            results = cursor.fetchall()  # Obtener todas las filas
        connection.close()
        return results  # Retornar los datos como una lista de diccionarios
    except pymysql.MySQLError:
        return None  # Devuelve None si hay un error de conexión

#--------------------------------#
#rutas con deepseek

# routes.py

@routes.route('/add_phase', methods=['GET', 'POST'])
@login_required
@admin_required
def add_phase():
    form = PhaseForm()

    # Poblar el campo de intersecciones
    form.intersection_id.choices = [(i.id, i.name) for i in Intersection.query.all()]

    if form.validate_on_submit():
        phase = Phase(
            name=form.name.data,
            intersection_id=form.intersection_id.data
        )
        db.session.add(phase)
        db.session.commit()
        flash('Phase added successfully!', 'success')
        return redirect(url_for('routes.add_phase'))

    phases = Phase.query.all()
    return render_template('add_phase.html', form=form, phases=phases)

@routes.route('/delete_phase/<int:phase_id>', methods=['POST'])
@login_required
@admin_required
def delete_phase(phase_id):
    phase = Phase.query.get_or_404(phase_id)

    db.session.delete(phase)
    db.session.commit()

    flash('Phase deleted successfully!', 'success')
    return redirect(url_for('routes.add_phase'))


@routes.route('/add_flow', methods=['GET', 'POST'])
@login_required
@admin_required
def add_flow():
    form = FlowForm()

    # Poblar el campo de fases
    form.phase_id.choices = [(p.id, p.name) for p in Phase.query.all()]

    # Poblar el campo de carriles
    form.lanes.choices = [(l.id, f"Lane {l.lane} (Camera {l.camera.cam_id})") for l in LaneParameter.query.all()]

    if form.validate_on_submit():
        flow = Flow(
            name=form.name.data,
            phase_id=form.phase_id.data
        )
        # Asociar carriles al flujo
        for lane_id in form.lanes.data:
            lane = LaneParameter.query.get(lane_id)
            if lane:
                flow.lanes.append(lane)
        db.session.add(flow)
        db.session.commit()
        flash('Flow added successfully!', 'success')
        return redirect(url_for('routes.add_flow'))

    flows = Flow.query.all()
    return render_template('add_flow.html', form=form, flows=flows)

@routes.route('/delete_flow/<int:flow_id>', methods=['POST'])
@login_required
@admin_required
def delete_flow(flow_id):
    flow = Flow.query.get_or_404(flow_id)

    db.session.delete(flow)
    db.session.commit()

    flash('Flow deleted successfully!', 'success')
    return redirect(url_for('routes.add_flow'))
