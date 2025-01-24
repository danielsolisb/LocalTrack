from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField, IntegerField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, Optional, IPAddress, NumberRange, IPAddress



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
    cloud_id = StringField('Cloud ID (optional)', validators=[Optional()])
    num_phases = IntegerField('Number of Phases', validators=[DataRequired(), NumberRange(min=1)])
    users = SelectMultipleField('Users', choices=[], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Intersection')




class TrafficControllerForm(FlaskForm):
    name = StringField('Controller Name', validators=[DataRequired()])
    identifier = StringField('Controller Identifier', validators=[DataRequired()])
    ip_address = StringField('Controller IP Address', validators=[DataRequired(), IPAddress()])
    intersection_id = SelectField('Intersection', coerce=int, validators=[DataRequired()])


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
