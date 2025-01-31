from . import db
from flask_login import UserMixin

# Modelo de Usuario
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='supervisor')  # 'admin' o 'supervisor'

    def is_admin(self):
        return self.role == 'admin'

    def is_supervisor(self):
        return self.role == 'supervisor'

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
    name = db.Column(db.String(100), nullable=False)  # Nombre del controlador
    identifier = db.Column(db.String(100), nullable=False, unique=True)  # Identificador único del controlador
    ip_address = db.Column(db.String(50), nullable=False)  # Dirección IP del controlador

    # Relación con Intersection
    intersection_id = db.Column(db.Integer, db.ForeignKey('intersection.id'), nullable=False)
    intersection = db.relationship('Intersection', backref=db.backref('traffic_controllers', lazy=True))

class AdaptiveControlConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    controller_id = db.Column(db.Integer, db.ForeignKey('traffic_controller.id', ondelete='CASCADE'), unique=True, nullable=False)
    saturation_flow = db.Column(db.Integer, default=1800, nullable=False)
    amber_time = db.Column(db.Integer, default=3, nullable=False)  # ÁMBAR POR DEFECTO 3
    clearance_time = db.Column(db.Integer, default=1, nullable=False)  # DESPEJE POR DEFECTO 1
    green_time_1 = db.Column(db.Integer, default=0, nullable=False)
    green_time_2 = db.Column(db.Integer, default=0, nullable=False)
    green_time_3 = db.Column(db.Integer, default=0, nullable=False)
    green_time_4 = db.Column(db.Integer, default=0, nullable=False)

    controller = db.relationship('TrafficController', backref=db.backref('adaptive_config', lazy=True, cascade="all, delete-orphan"))


# Modelo de Cámara
class Camera(db.Model):
    __tablename__ = 'camera'
    id = db.Column(db.Integer, primary_key=True)
    cam_id = db.Column(db.String(50), nullable=False)  
    ip_address = db.Column(db.String(50), nullable=False)  
    street = db.Column(db.String(100), nullable=False)  
    direction = db.Column(db.String(50), nullable=False)  
    lanes = db.Column(db.Integer, nullable=False)

    intersection_id = db.Column(db.Integer, db.ForeignKey('intersection.id'), nullable=False)

    intersection = db.relationship('Intersection', backref='cameras', lazy=True)

    # ✅ Relación corregida para eliminar en cascada
    lane_parameters = db.relationship('LaneParameter', back_populates='cam_ref', lazy=True, cascade="all, delete-orphan")
    measurements = db.relationship('Measurement', backref='camera', lazy=True, cascade="all, delete-orphan")

      # ✅ Nuevos campos
    username = db.Column(db.String(50), nullable=True)
    password = db.Column(db.String(100), nullable=True)

# Modelo de Parámetros de Carril
#class LaneParameter(db.Model):
#    __tablename__ = 'lane_parameter'
#    id = db.Column(db.Integer, primary_key=True)
#    lane = db.Column(db.Integer, nullable=False)  # Número de carril
#    straight = db.Column(db.Boolean, default=False)  # Si el carril es recto
#    turn = db.Column(db.Boolean, default=False)  # Si el carril es de giro
#    turn_direction = db.Column(db.String(10), nullable=True)  # Dirección del giro (izquierda, derecha)
#
#    # Clave foránea hacia Camera
#    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)

#class LaneParameter(db.Model):
#    __tablename__ = 'lane_parameter'
#    id = db.Column(db.Integer, primary_key=True)
#    lane = db.Column(db.Integer, nullable=False)  # Número del carril
#    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)
#    
#    # Nueva relación con Flow
#    flow_id = db.Column(db.Integer, db.ForeignKey('flow.id'))
class LaneParameter(db.Model):
    __tablename__ = 'lane_parameter'
    id = db.Column(db.Integer, primary_key=True)
    lane = db.Column(db.Integer, nullable=False)
    straight = db.Column(db.Boolean, default=False)
    turn = db.Column(db.Boolean, default=False)
    turn_direction = db.Column(db.String(10), nullable=True)

    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)
    flow_id = db.Column(db.Integer, db.ForeignKey('flow.id'))  

    # ✅ Relación corregida con alias adicional
    cam_ref = db.relationship('Camera', back_populates='lane_parameters')

    @property
    def camera(self):
        return self.cam_ref  # Alias para evitar errores en templates


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


#Modelo para mostrar datos procesados por el contador
class AdaptiveResults(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    controller_id = db.Column(db.Integer, db.ForeignKey('traffic_controller.id', ondelete='CASCADE'), nullable=False)
    phase = db.Column(db.String(50), nullable=False)
    flow = db.Column(db.Integer, nullable=False)
    sample_time = db.Column(db.Integer, nullable=False)  # Tiempo de muestra en segundos
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    num_vehicles = db.Column(db.Integer, nullable=False)
    num_lanes = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.Boolean, nullable=False)  # 1 = Recto, 0 = Giro

    controller = db.relationship('TrafficController', backref=db.backref('adaptive_results', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<AdaptiveResults {self.id} - Phase {self.phase}>'

class PhaseTimingResults(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    controller_id = db.Column(db.Integer, db.ForeignKey('traffic_controller.id', ondelete='CASCADE'), nullable=False)
    phase = db.Column(db.String(50), nullable=False)
    calculated_time = db.Column(db.Integer, nullable=False)  # Tiempo resultante
    suggested_time = db.Column(db.Integer, nullable=False)  # Tiempo sugerido
    start_time = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # Nueva columna
    end_time = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # Nueva columna
    
    controller = db.relationship('TrafficController', backref=db.backref('phase_timing_results', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<PhaseTimingResults {self.id} - Phase {self.phase}>'    


#modelos hechos con deepseek
#jasfdgsfdhgsfdh
# models.py

# Modelo para Fase
class Phase(db.Model):
    __tablename__ = 'phase'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Nombre de la fase
    intersection_id = db.Column(db.Integer, db.ForeignKey('intersection.id'), nullable=False)  # Relación con Intersección

    # Relación con Intersection
    intersection = db.relationship('Intersection', backref=db.backref('phases', lazy=True))

    # Relación con Flujos
    flows = db.relationship('Flow', backref='phase', lazy=True, cascade="all, delete-orphan")

# Modelo para Flujo
class Flow(db.Model):
    __tablename__ = 'flow'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Nombre del flujo
    phase_id = db.Column(db.Integer, db.ForeignKey('phase.id'), nullable=False)  # Relación con Fase

    # Relación muchos a muchos con LaneParameter (carriles)
    lanes = db.relationship('LaneParameter', secondary='flow_lane', backref=db.backref('flows', lazy=True, cascade="all, delete"))

 #Tabla intermedia para la relación muchos a muchos entre Flow y LaneParameter
flow_lane = db.Table(
    'flow_lane',
    db.Column('flow_id', db.Integer, db.ForeignKey('flow.id'), primary_key=True),
    db.Column('lane_id', db.Integer, db.ForeignKey('lane_parameter.id'), primary_key=True)
)