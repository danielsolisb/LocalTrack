from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask import Blueprint
from . import db, login_manager
from .models import User, Intersection, Camera, LaneParameter, Measurement, TrafficController # Asegúrate de importar Intersection
from .forms import LoginForm, IntersectionForm, CameraForm, LaneParameterForm, TrafficControllerForm
from werkzeug.security import check_password_hash
import pymysql

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

@routes.route('/add_controller', endpoint='add_controller',methods=['GET', 'POST'])
@login_required
def add_controller():
    form = TrafficControllerForm()

    # Cargar intersecciones existentes
    form.intersection_id.choices = [(i.id, i.name) for i in Intersection.query.all()]

    if form.validate_on_submit():
        # Crear y guardar el controlador en la base de datos
        new_controller = TrafficController(
            controller_name=form.controller_name.data,
            controller_id=form.controller_id.data,
            intersection_id=form.intersection_id.data,
            adaptive_plan=form.adaptive_plan.data,
            green_1=form.green_1.data,
            green_2=form.green_2.data,
            green_3=form.green_3.data,
            green_4=form.green_4.data
        )
        db.session.add(new_controller)
        db.session.commit()
        flash('Traffic controller registered successfully!', 'success')
        return redirect(url_for('routes.add_controller'))

    # Obtener controladores existentes para mostrar en la tabla
    controllers = TrafficController.query.all()

    return render_template('add_controller.html', form=form, controllers=controllers)

@routes.route('/monitoring')
@login_required
def monitoring():
    return render_template('monitoring.html')


@routes.route('/add_camera', methods=['GET', 'POST'])
@login_required
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


@routes.route('/add_lane', methods=['GET', 'POST'])
@login_required
def add_lane():
    form = LaneParameterForm()

    # Obtener todas las cámaras disponibles para llenar el campo SelectField
    cameras = Camera.query.all()
    form.camera_id.choices = [(c.id, c.cam_id) for c in cameras]

    if form.validate_on_submit():
        # Crear un nuevo parámetro de carril con los datos del formulario
        lane_parameter = LaneParameter(
            lane=form.lane.data,
            straight=form.straight.data,
            turn=form.turn.data,
            turn_direction=form.turn_direction.data if form.turn.data else None,
            camera_id=form.camera_id.data
        )
        db.session.add(lane_parameter)
        db.session.commit()
        flash('Parámetro de carril agregado correctamente.', 'success')
        return redirect(url_for('routes.add_lane'))

    # Obtener todos los carriles registrados
    lane_parameters = LaneParameter.query.all()

    return render_template('add_lane.html', form=form, lane_parameters=lane_parameters)


@routes.route('/measurements', endpoint='measurements', methods=['GET'])
@login_required
def measurements():
    # Obtener todos los carriles con sus cámaras asociadas
    lanes = LaneParameter.query.join(Camera).all()

    # Filtros opcionales
    lane_id = request.args.get('lane', type=int)
    start_date = request.args.get('start_date')  # Formato esperado: YYYY-MM-DD
    end_date = request.args.get('end_date')  # Formato esperado: YYYY-MM-DD

    # Base de la consulta
    query = Measurement.query

    # Aplicar filtros
    if lane_id:
        query = query.filter_by(lane=lane_id)
    if start_date:
        query = query.filter(Measurement.timestamp >= start_date)
    if end_date:
        query = query.filter(Measurement.timestamp <= end_date)

    # Obtener resultados
    measurements = query.all()

    return render_template('measurements.html', lanes=lanes, measurements=measurements)
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
