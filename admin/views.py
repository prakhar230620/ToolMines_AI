from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.pymongo import ModelView
from flask_admin.contrib.pymongo.filters import FilterEqual, FilterLike
from flask import redirect, url_for, session
from config.database import db
from wtforms import Form, StringField, BooleanField
from datetime import datetime

class UserForm(Form):
    email = StringField('Email')
    name = StringField('Name')
    is_admin = BooleanField('Is Admin')

class SecureModelView(ModelView):
    def is_accessible(self):
        return 'admin_id' in session

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_auth.admin_login'))

class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return 'admin_id' in session

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_auth.admin_login'))

class UserAdminView(SecureModelView):
    column_list = ('email', 'name', 'is_admin')
    column_searchable_list = ('email', 'name')
    column_filters = ('email', 'name', 'is_admin')
    
    def scaffold_form(self):
        return UserForm
    
    def scaffold_filters(self, name):
        """Return list of filters for the given field name."""
        if name == 'is_admin':
            return [FilterEqual(name, 'Is Admin')]
        if name in ('email', 'name'):
            return [FilterLike(name, name.title())]
        return None
    
    def on_model_change(self, form, model, is_created):
        # Convert form data to dict for MongoDB
        return {
            'email': form.email.data,
            'name': form.name.data,
            'is_admin': form.is_admin.data,
            'created_at': model.get('created_at') if not is_created else datetime.utcnow()
        }

def init_admin(app):
    admin = Admin(
        app,
        name='Jarvis Admin',
        template_mode='bootstrap4',
        index_view=SecureAdminIndexView()
    )
    
    # Add views
    admin.add_view(UserAdminView(db.users, 'Users'))
    
    return admin
