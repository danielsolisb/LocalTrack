from flask import redirect, url_for, flash
from flask_login import current_user
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("You don't have permission to access this page.", "danger")
            return redirect(url_for('routes.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def supervisor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_supervisor() or current_user.is_admin()):
            flash("You don't have permission to access this page.", "danger")
            return redirect(url_for('routes.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
