from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required

def owner_required(f):
    @login_required
    @wraps(f) # Important for preserving the original function's metadata
    def decorated_function(*args, **kwargs):
        if current_user.role != 'owner':
            flash('Access denied: Owners only.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def worker_required(f):
    @login_required
    @wraps(f) # Important for preserving the original function's metadata
    def decorated_function(*args, **kwargs):
        if current_user.role != 'worker':
            flash('Access denied: Workers only.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function