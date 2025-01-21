from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response, flash
from flask_socketio import SocketIO
from flask_cors import CORS
from chatbot import setup_chatbot_routes
from converters.converter import setup_converter_routes
from contact.contact_handler import setup_contactform_routes
from voicebot import setup_voicebot_routes
from lang_trans import setup_lang_trans_routes
from contact import ContactHandler, ContactForm, setup_contactform_routes
from routes.auth import auth, login_required
from routes.admin_auth import admin_auth
from routes.admin_dashboard import admin_dashboard
from routes.admin_upcoming import admin_upcoming
from routes.admin_index import admin_index
from functools import wraps
import re
from contact.email_service import EmailService,setup_newsletter_service
import datetime
from models.user import User
from config.database import db
from config.setup_db import setup_database
from config.init_tools import initialize_tools
from models.tool import Tool
from models.tool_usage import ToolUsage
import pandas as pd
import io
import os
import sys
from flask_login import LoginManager, current_user
from admin import init_admin



# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
app.config['SECRET_KEY'] = '14701c4d1e765347259951b561146a45'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['FLASK_ADMIN_TEMPLATE_MODE'] = 'bootstrap4'
app.config['FLASK_ADMIN_BASE_TEMPLATE'] = 'admin/base.html'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.find_by_email(user_id)

# Initialize Flask-Admin
admin = init_admin(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(admin_auth)
app.register_blueprint(admin_dashboard)
app.register_blueprint(admin_upcoming)
app.register_blueprint(admin_index)

# Initialize contact handler
contact_handler = ContactHandler()

# Initialize email service
email_service = EmailService()

# Authentication decorator
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Database setup
setup_database()
initialize_tools()  # Initialize tools in database

def track_tool_usage(tool_id, user_id=None):
    """Track tool usage and update statistics"""
    tool = Tool.get_tool_by_id(tool_id)
    if tool:
        Tool.increment_usage(tool_id)
        ToolUsage.create(tool['name'], user_id)

# Main route
@app.route('/')
def index():
    from routes.admin_index import load_tools
    tools = load_tools()
    return render_template('index/index.html', tools=tools)

@app.route('/about')
def about():
    return render_template('index/about.html')

@app.route('/contact')
def contact():
    return render_template('index/contact.html')

@app.route('/tools')
@auth_required
def tools():
    """Display all tools page."""
    return render_template('all tools/tools.html')

@app.route('/upcoming')
def upcoming():
    from routes.admin_upcoming import load_stats, load_tools
    stats = load_stats()
    tools = load_tools()
    return render_template('index/upcoming.html', stats=stats, tools=tools)

# Register tools routes with authentication and usage tracking
setup_chatbot_routes(app, auth_required=auth_required, track_tool_usage=track_tool_usage)
setup_voicebot_routes(app, socketio, auth_required=auth_required, track_tool_usage=track_tool_usage)
setup_lang_trans_routes(app, auth_required=auth_required, track_tool_usage=track_tool_usage)
setup_converter_routes(app, socketio, auth_required=auth_required, track_tool_usage=track_tool_usage)

# Register contact form and newsletter routes
setup_newsletter_service(app,email_service)
setup_contactform_routes(app)

# Run the app
if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
