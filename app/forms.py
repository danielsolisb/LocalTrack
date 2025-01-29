from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField, IntegerField, BooleanField, SelectMultipleField, ValidationError
from wtforms.validators import DataRequired, Optional, IPAddress, NumberRange, IPAddress
from wtforms.validators import Length



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

class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('supervisor', 'Supervisor')], validators=[DataRequired()])
    submit = SubmitField('Add User')


class TrafficControllerForm(FlaskForm):
    name = StringField('Controller Name', validators=[DataRequired()])
    identifier = StringField('Controller Identifier', validators=[DataRequired()])
    ip_address = StringField('Controller IP Address', validators=[DataRequired(), IPAddress()])
    intersection_id = SelectField('Intersection', coerce=int, validators=[DataRequired()])

class AdaptiveControlForm(FlaskForm):
    saturation_flow = SelectField('Saturation Flow', choices=[(1800, '1 Hour (1800)'), (900, '30 Minutes (900)'), (450, '15 Minutes (450)')], coerce=int)
    amber_time = IntegerField('Amber Time (seconds)', validators=[DataRequired()])
    clearance_time = IntegerField('Clearance Time (seconds)', validators=[DataRequired()])
    green_time_1 = IntegerField('Green Time 1 (seconds)', validators=[Optional()], default=0)
    green_time_2 = IntegerField('Green Time 2 (seconds)', validators=[Optional()], default=0)
    green_time_3 = IntegerField('Green Time 3 (seconds)', validators=[Optional()], default=0)
    green_time_4 = IntegerField('Green Time 4 (seconds)', validators=[Optional()], default=0)

    submit = SubmitField('Save Configuration')

class CameraForm(FlaskForm):
    cam_id = StringField('Camera Name', validators=[DataRequired()])
    ip_address = StringField('IP Address', validators=[DataRequired(), IPAddress()])
    street = StringField('Street', validators=[DataRequired()])
    direction = StringField('Direction (e.g., North, South)', validators=[DataRequired()])
    lanes = IntegerField('Number of Lanes', validators=[DataRequired()])
    intersection_id = SelectField('Intersection', choices=[], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Camera')

#class LaneParameterForm(FlaskForm):
#    lane = IntegerField('Lane Number', validators=[DataRequired()])
#    straight = BooleanField('Straight', default=False)
#    turn = BooleanField('Turn', default=False)
#    turn_direction = StringField('Turn Direction (e.g., Left, Right)', validators=[Optional()])
#    camera_id = SelectField('Camera', choices=[], coerce=int, validators=[DataRequired()])
#    submit = SubmitField('Save Lane Parameter')
class LaneParameterForm(FlaskForm):
    lane = IntegerField('Lane Number', validators=[DataRequired()])
    straight = BooleanField('Straight', default=False)
    turn = BooleanField('Turn', default=False)
    turn_direction = StringField('Turn Direction (e.g., Left, Right)', validators=[Optional()])
    camera_id = SelectField('Camera', choices=[], coerce=int, validators=[DataRequired()])
    flow_id = SelectField('Flow', choices=[], coerce=int, validators=[Optional()])  # Nuevo campo
    submit = SubmitField('Save Lane Parameter')

    # 🔴 Validación para evitar que un carril sea "Straight" y "Turn" a la vez
    def validate_turn(self, field):
        if self.turn.data and self.straight.data:
            raise ValidationError("A lane cannot be both Straight and Turn at the same time.")
        
#----------------------#
# forms con deepseek

# forms.py

class PhaseForm(FlaskForm):
    name = StringField('Phase Number', validators=[DataRequired()])
    intersection_id = SelectField('Intersection', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Phase')

class FlowForm(FlaskForm):
    name = StringField('Flow Number', validators=[DataRequired()])
    phase_id = SelectField('Phase', coerce=int, validators=[DataRequired()])
    lanes = SelectMultipleField('Lanes', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Flow')

