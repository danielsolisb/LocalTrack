from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user  # Agregar login_required
from . import db, login_manager
from .models import User
from .forms import LoginForm


from flask import Blueprint
from . import db, login_manager
from .models import User
from .forms import LoginForm

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
        if user and user.password == form.password.data:  # ¡Usa hashing en producción!
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        flash('Invalid username or password')
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

@routes.route('/configuration')
@login_required
def configuration():
    return render_template('configuration.html')

@routes.route('/monitoring')
@login_required
def monitoring():
    return render_template('monitoring.html')
