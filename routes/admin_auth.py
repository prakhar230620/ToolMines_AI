from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from models.user import User
from functools import wraps
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_auth = Blueprint('admin_auth', __name__)

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login as admin first', 'warning')
            return redirect(url_for('admin_auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_auth.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Redirect if already logged in as admin
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        logger.info(f"Admin login attempt for: {email}")
        
        user = User.get_user_by_email(email)
        if user and user.is_admin and user.check_password(password):
            session['admin_id'] = user.email
            logger.info(f"Admin login successful for: {email}")
            flash('Welcome to Admin Panel', 'success')
            return redirect(url_for('admin_dashboard.dashboard'))
        
        logger.warning(f"Failed admin login attempt for: {email}")
        flash('Invalid admin credentials', 'error')
        
    return render_template('admin/login.html')

@admin_auth.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('You have been logged out from admin panel', 'info')
    return redirect(url_for('index'))
