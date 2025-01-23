from . import db
from flask_login import UserMixin

# Modelo de Usuario
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

# Modelo de Intersección
# Tabla intermedia para la relación muchos a muchos
user_intersection = db.Table(
    'user_intersection',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('intersection_id', db.Integer, db.ForeignKey('intersection.id'), primary_key=True)
)
class Intersection(db.Model):
    __tablename__ = 'intersection'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(50), nullable=True)
    province = db.Column(db.String(50), nullable=True)
    canton = db.Column(db.String(50), nullable=True)
    coordinates = db.Column(db.String(100), nullable=True)
    cloud_id = db.Column(db.Integer, nullable=True)
    num_phases = db.Column(db.Integer, nullable=False, default=1)
    
    # Relación con usuarios
    users = db.relationship('User', secondary=user_intersection, backref=db.backref('intersections', lazy='dynamic'))

# Modelo para el controlador semafórico
class TrafficController(db.Model):
    __tablename__ = 'traffic_controller'
    id = db.Column(db.Integer, primary_key=True)
    controller_name = db.Column(db.String(100), nullable=False)  # Nombre del controlador
    controller_id = db.Column(db.String(50), nullable=False)  # Identificador del controlador
    intersection_id = db.Column(db.Integer, db.ForeignKey('intersection.id'), nullable=False)  # Relación con Intersection
    adaptive_plan = db.Column(db.String(20), nullable=False)  # Registro de plan adaptativo (valor hex)
    green_1 = db.Column(db.String(20), nullable=False)  # Verde 1 (valor hex)
    green_2 = db.Column(db.String(20), nullable=False)  # Verde 2 (valor hex)
    green_3 = db.Column(db.String(20), nullable=False)  # Verde 3 (valor hex)
    green_4 = db.Column(db.String(20), nullable=False)  # Verde 4 (valor hex)

    # Relación con Intersection
    intersection = db.relationship('Intersection', backref='traffic_controllers', lazy=True)


# Modelo de Cámara
class Camera(db.Model):
    __tablename__ = 'camera'
    id = db.Column(db.Integer, primary_key=True)
    cam_id = db.Column(db.String(50), nullable=False)  # ID de la cámara
    ip_address = db.Column(db.String(50), nullable=False)  # Dirección IP
    street = db.Column(db.String(100), nullable=False)  # Calle
    direction = db.Column(db.String(50), nullable=False)  # Dirección (norte, sur, etc.)
    lanes = db.Column(db.Integer, nullable=False)  # Número de carriles

    # Clave foránea hacia Intersection
    intersection_id = db.Column(db.Integer, db.ForeignKey('intersection.id'), nullable=False)

    # Relación con Intersection
    intersection = db.relationship('Intersection', backref='cameras', lazy=True)

    # Relación con LaneParameters
    lane_parameters = db.relationship('LaneParameter', backref='camera', lazy=True)

    # Relación con Measurements
    measurements = db.relationship('Measurement', backref='camera', lazy=True)


# Modelo de Parámetros de Carril
class LaneParameter(db.Model):
    __tablename__ = 'lane_parameter'
    id = db.Column(db.Integer, primary_key=True)
    lane = db.Column(db.Integer, nullable=False)  # Número de carril
    straight = db.Column(db.Boolean, default=False)  # Si el carril es recto
    turn = db.Column(db.Boolean, default=False)  # Si el carril es de giro
    turn_direction = db.Column(db.String(10), nullable=True)  # Dirección del giro (izquierda, derecha)

    # Clave foránea hacia Camera
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)

# Modelo de Medición
class Measurement(db.Model):
    __tablename__ = 'measurement'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())  # Marca de tiempo
    lane = db.Column(db.Integer, nullable=False)  # Carril
    vehicles_class_a = db.Column(db.Integer, default=0)  # Vehículos clase A
    vehicles_class_b = db.Column(db.Integer, default=0)  # Vehículos clase B
    vehicles_class_c = db.Column(db.Integer, default=0)  # Vehículos clase C
    average_speed = db.Column(db.Float, default=0.0)  # Velocidad promedio
    headway = db.Column(db.Float, default=0.0)  # Tiempo entre vehículos

    # Clave foránea hacia Camera
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)
