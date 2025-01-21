from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.user import User
from utils.admin_manager import AdminManager
from functools import wraps
from urllib.parse import urlparse, urljoin
import logging
import random
import string
from email.message import EmailMessage
import smtplib
from datetime import datetime
import os
from dotenv import load_dotenv
from contact.email_service import EmailService

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
auth = Blueprint('auth', __name__)
admin_manager = AdminManager()

# Get Google OAuth credentials from environment
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Store the full URL (including query parameters) that the user was trying to access
            next_url = request.url
            session['next_url'] = next_url if is_safe_url(next_url) else None
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            logger.info("\n=== Login Attempt ===")
            logger.info(f"1. Received login attempt for:")
            logger.info(f"   - Email: {email}")
            logger.info(f"   - Password length: {len(password) if password else 0}")
            
            # First check if it's an admin login
            if admin_manager.verify_admin(email, password):
                session['user_id'] = email
                session['is_admin'] = True
                session['name'] = admin_manager.get_admin_name(email)
                return redirect(url_for('admin.index'))
            
            # If not admin, check regular user login
            user = User.get_user_by_email(email)
            if user:
                logger.info("2. User found in database:")
                logger.info(f"   - Name: {user.name}")
                logger.info(f"   - Is Admin: {user.is_admin}")
                logger.info(f"   - Stored password hash: {user._password}")
                
                logger.info("3. Attempting password verification...")
                if user.check_password(password):
                    logger.info("   ✓ Password verified successfully")
                    session['user_id'] = user.email
                    session['is_admin'] = user.is_admin
                    session['name'] = user.name
                    
                    # Get next URL from either form data or session
                    next_url = request.form.get('next') or session.get('next_url')
                    if next_url:
                        session.pop('next_url', None)  # Clear the stored next_url
                        return redirect(next_url)
                    
                    return redirect(url_for('index'))
                else:
                    logger.info("   ✗ Password verification failed")
            else:
                logger.info("2. ✗ User not found in database")
            
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html', error='Invalid email or password')
        
        return render_template('auth/login.html')
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        flash('An error occurred during login', 'error')
        return render_template('auth/login.html', error='An error occurred during login')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            terms_accepted = request.form.get('terms_accepted')
            
            logger.info(f"Registration attempt for email: {email}")
            
            if not all([name, email, password, confirm_password]):
                logger.warning("Missing required fields in registration")
                return render_template('auth/register.html', error='All fields are required')
            
            if not terms_accepted:
                logger.warning("Terms and conditions not accepted")
                return render_template('auth/register.html', 
                                    error='You must accept the Terms and Conditions to register',
                                    name=name,
                                    email=email)
            
            if password != confirm_password:
                logger.warning("Passwords do not match in registration")
                return render_template('auth/register.html', 
                                    error='Passwords do not match',
                                    name=name,
                                    email=email)
                
            existing_user = User.get_user_by_email(email)
            if existing_user:
                logger.warning(f"Attempted registration with existing email: {email}")
                return render_template('auth/register.html', error='Email already registered. Please login or use a different email.')
                
            user = User.create_user(email=email, password=password, name=name)
            session['user_id'] = user.email
            logger.info(f"Successfully registered user: {email}")
            
            # Send welcome email
            try:
                email_service = EmailService()
                success, error = email_service.send_welcome_email(user.email, user.name)
                if not success:
                    logger.error(f"Failed to send welcome email: {error}")
            except Exception as e:
                logger.error(f"Error sending welcome email: {str(e)}")
            
            # Get next URL from either form data or session
            next_url = request.form.get('next') or session.get('next_url')
            if next_url and is_safe_url(next_url):
                session.pop('next_url', None)
                return redirect(next_url)
            
            return redirect(url_for('index'))
            
        return render_template('auth/register.html', google_client_id=GOOGLE_CLIENT_ID)
    except Exception as e:
        logger.error(f"Error in register route: {str(e)}")
        return render_template('auth/register.html', error='An error occurred. Please try again.')

@auth.route('/auth/google/callback', methods=['POST'])
def google_auth_callback():
    try:
        token = request.json.get('credential')
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        
        email = idinfo['email']
        name = idinfo['name']
        google_id = idinfo['sub']
        
        logger.info(f"Google authentication attempt for email: {email}")
        
        existing_user = User.get_user_by_google_id(google_id)
        if not existing_user:
            # Create new user
            user = User.create_user(
                email=email,
                name=name,
                google_id=google_id
            )
            logger.info(f"Created new user from Google auth: {email}")
            
            # Send welcome email for new users
            try:
                email_service = EmailService()
                success, error = email_service.send_welcome_email(user.email, user.name)
                if not success:
                    logger.error(f"Failed to send welcome email: {error}")
            except Exception as e:
                logger.error(f"Error sending welcome email: {str(e)}")
        else:
            user = existing_user
            logger.info(f"Existing user logged in via Google: {email}")
        
        session['user_id'] = user.email
        
        # Get next URL from either query parameters or session
        next_url = request.args.get('next') or session.get('next_url')
        if next_url and is_safe_url(next_url):
            session.pop('next_url', None)
            return jsonify({'success': True, 'redirect': next_url})
            
        return jsonify({'success': True, 'redirect': url_for('index')})
        
    except Exception as e:
        logger.error(f"Error in Google authentication: {str(e)}")
        return jsonify({'success': False, 'error': 'Authentication failed'})

@auth.route('/profile')
@login_required
def profile():
    try:
        user = User.get_user_by_email(session['user_id'])
        return render_template('auth/profile.html', user=user)
    except Exception as e:
        logger.error(f"Error in profile route: {str(e)}")
        return redirect(url_for('auth.login'))

@auth.route('/logout', methods=['POST'])
def logout():
    """Logout the current user."""
    logger.info(f"User {session.get('user_id', 'Unknown')} logged out")
    session.clear()  # Clear all session data
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('index'))  # Always redirect to index page

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.get_user_by_email(email)
        
        if not user:
            return render_template('auth/forgot_password.html', error='No account found with this email.')
        
        # Generate a random 6-digit code
        reset_code = ''.join(random.choices(string.digits, k=6))
        
        # Store the reset code in session with expiry
        session['reset_code'] = reset_code
        session['reset_email'] = email
        
        # Create email service instance
        email_service = EmailService()
        
        # Create reset code email message
        subject = "Password Reset Code"
        message = f"""
        <h2>Password Reset Code</h2>
        <p>Hello {user.name},</p>
        <p>You have requested to reset your password. Here is your reset code:</p>
        <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; font-size: 24px; text-align: center; font-family: monospace;">
            {reset_code}
        </div>
        <p>If you did not request this password reset, please ignore this email.</p>
        <p>Best regards,<br>Your App Team</p>
        """
        
        try:
            # Send reset code via email
            msg = email_service.create_email_message(
                sender_name="Your App",
                sender_email=email_service.smtp_username,
                subject=subject,
                message=message,
                to_email=email
            )
            
            with smtplib.SMTP_SSL(email_service.smtp_host, email_service.smtp_port) as server:
                server.login(email_service.smtp_username, email_service.smtp_password)
                server.send_message(msg)
            
            return render_template('auth/forgot_password.html', 
                                success='Reset code has been sent to your email.')
        except Exception as e:
            logger.error(f"Failed to send reset code email: {e}")
            return render_template('auth/forgot_password.html', 
                                error='Failed to send reset code. Please try again.')
    
    return render_template('auth/forgot_password.html')

@auth.route('/verify-code', methods=['POST'])
def verify_code():
    code = request.form.get('code')
    email = request.form.get('email')
    stored_code = session.get('reset_code')
    stored_email = session.get('reset_email')
    
    if not all([code, email, stored_code, stored_email]):
        return render_template('auth/reset_password.html', 
                            error='Invalid request. Please try again.',
                            email=email)
    
    if email != stored_email:
        return render_template('auth/reset_password.html', 
                            error='Invalid email address.',
                            email=email)
    
    if code != stored_code:
        return render_template('auth/reset_password.html', 
                            error='Invalid reset code.',
                            email=email)
    
    # Code is verified, show password reset form
    return render_template('auth/reset_password.html', 
                         email=email,
                         code=code,
                         code_verified=True)

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        code = request.form.get('code')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        stored_code = session.get('reset_code')
        stored_email = session.get('reset_email')
        
        # Verify all required fields and code again
        if not all([code, email, password, confirm_password, stored_code, stored_email]):
            return render_template('auth/reset_password.html', 
                                error='Invalid request. Please try again.',
                                email=email)
        
        if email != stored_email or code != stored_code:
            return render_template('auth/reset_password.html', 
                                error='Invalid reset code or email.',
                                email=email)
        
        if password != confirm_password:
            return render_template('auth/reset_password.html', 
                                error='Passwords do not match.',
                                email=email,
                                code=code,
                                code_verified=True)
        
        # Update user's password
        user = User.get_user_by_email(email)
        if user:
            user.set_password(password)
            user.save()
            
            # Clear reset code from session
            session.pop('reset_code', None)
            session.pop('reset_email', None)
            
            flash('Your password has been successfully reset. Please login with your new password.', 'success')
            return redirect(url_for('auth.login'))
        
    # GET request - show initial code verification form
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/reset_password.html', email=email)

@auth.route('/terms')
def terms():
    return render_template('legal/terms.html', current_date=datetime.now().strftime('%B %d, %Y'))

@auth.route('/privacy')
def privacy():
    return render_template('legal/privacy.html', current_date=datetime.now().strftime('%B %d, %Y'))

