from . import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'  # Nombre explícito de la tabla
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Modelo de Intersección
class Intersection(db.Model):
    __tablename__ = 'intersection'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    coordinates = db.Column(db.String(100), nullable=False)

    # Relación con cámaras
    cameras = db.relationship('Camera', backref='intersection', lazy=True)

# Modelo de Cámara
class Camera(db.Model):
    __tablename__ = 'camera'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    street = db.Column(db.String(100), nullable=False)
    lanes = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.String(50), nullable=False)

    # Clave foránea hacia Intersection
    intersection_id = db.Column(db.Integer, db.ForeignKey('intersection.id'), nullable=False)

    # Relación con Flujos
    flows = db.relationship('Flow', backref='camera', lazy=True)

# Modelo de Flujo
class Flow(db.Model):
    __tablename__ = 'flow'
    id = db.Column(db.Integer, primary_key=True)
    lane = db.Column(db.Integer, nullable=False)
    flow_value = db.Column(db.Float, nullable=False)

    # Clave foránea hacia Camera
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)
