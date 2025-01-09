from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask import Blueprint
from . import db, login_manager
from .models import User, Intersection, Camera, LaneParameter # Asegúrate de importar Intersection
from .forms import LoginForm, IntersectionForm, CameraForm, LaneParameterForm
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
        if user and user.password == form.password.data:  # Usa hashing en producción
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
    cloud_intersections = []

    if request.method == 'POST' and 'sync_cloud' in request.form:
        # Consultar intersecciones desde la nube
        cloud_intersections = fetch_intersections_from_cloud()
        if cloud_intersections is None:
            flash('No se pudo conectar con la base de datos en la nube.', 'danger')
        else:
            flash('Intersecciones sincronizadas desde la nube.', 'success')

    if form.validate_on_submit() and 'manual_submit' in request.form:
        # Guardar intersección manualmente con ID de la nube opcional
        intersection = Intersection(
            name=form.name.data,
            address=form.address.data,
            province=form.province.data,
            canton=form.canton.data,
            coordinates=form.coordinates.data,
            cloud_id=form.cloud_id.data if form.cloud_id.data else None  # Guardar None si está vacío
        )
        db.session.add(intersection)
        db.session.commit()
        flash('Intersección agregada manualmente.', 'success')
        return redirect(url_for('routes.configuration'))

    # Mostrar todas las intersecciones locales
    local_intersections = Intersection.query.all()
    return render_template(
        'configuration.html',
        form=form,
        local_intersections=local_intersections,
        cloud_intersections=cloud_intersections
    )

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
