from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, IPAddress

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])  # Cambia a PasswordField
    submit = SubmitField('Login')

# Formulario para agregar intersecciones manualmente
class IntersectionForm(FlaskForm):
    name = StringField('Intersection Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    province = StringField('Province', validators=[DataRequired()])
    canton = StringField('Canton', validators=[DataRequired()])
    coordinates = StringField('Coordinates', validators=[DataRequired()])
    cloud_id = StringField('Cloud ID (optional)', validators=[Optional()])  # Campo opcional
    submit = SubmitField('Save Intersection')


class CameraForm(FlaskForm):
    cam_id = StringField('Camera ID', validators=[DataRequired()])
    ip_address = StringField('IP Address', validators=[DataRequired(), IPAddress()])
    street = StringField('Street', validators=[DataRequired()])
    direction = StringField('Direction (e.g., North, South)', validators=[DataRequired()])
    lanes = IntegerField('Number of Lanes', validators=[DataRequired()])
    intersection_id = SelectField('Intersection', choices=[], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Camera')

class LaneParameterForm(FlaskForm):
    lane = IntegerField('Lane Number', validators=[DataRequired()])
    straight = BooleanField('Straight', default=False)
    turn = BooleanField('Turn', default=False)
    turn_direction = StringField('Turn Direction (e.g., Left, Right)', validators=[Optional()])
    camera_id = SelectField('Camera', choices=[], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Lane Parameter')
