from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import db
from utils.admin_manager import AdminManager

class User:
    def __init__(self, email, password=None, google_id=None, name=None, is_admin=None, created_at=None):
        self.email = email
        self.google_id = google_id
        self.name = name or 'Not provided'  # Default value if name is None
        self.created_at = created_at or datetime.utcnow()  # Use provided date or current time
        
        # Check if email is in admin list if is_admin not explicitly set
        if is_admin is None:
            admin_manager = AdminManager()
            self.is_admin = admin_manager.is_admin_email(email)
        else:
            self.is_admin = is_admin
            
        self._password = None
        if password:
            self.set_password(password)

    def set_password(self, password):
        """Set password using Werkzeug's secure hash"""
        self._password = generate_password_hash(password)

    def check_password(self, password):
        """Check password using Werkzeug's secure check"""
        if not self._password:
            return False
        return check_password_hash(self._password, password)

    def to_dict(self):
        return {
            'email': self.email,
            'google_id': self.google_id,
            'name': self.name,
            'password': self._password,
            'created_at': self.created_at,
            'is_admin': self.is_admin
        }

    def save(self):
        """Save or update user in the database"""
        user_data = {
            'email': self.email,
            'password': self._password,
            'google_id': self.google_id,
            'name': self.name,
            'is_admin': self.is_admin,
            'created_at': self.created_at
        }
        
        # Update if exists, insert if not
        db.users.update_one(
            {'email': self.email},
            {'$set': user_data},
            upsert=True
        )

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.email

    @staticmethod
    def create_user(email, password=None, google_id=None, name=None, is_admin=False):
        user = User(email, password, google_id, name, is_admin)
        db.users.insert_one(user.to_dict())
        return user

    @staticmethod
    def get_user_by_email(email):
        user_data = db.users.find_one({'email': email})
        if user_data:
            user = User(
                email=user_data['email'],
                google_id=user_data.get('google_id'),
                name=user_data.get('name', 'Not provided'),  # Default value if name is missing
                is_admin=user_data.get('is_admin', False),
                created_at=user_data.get('created_at', datetime.utcnow())  # Default value if date is missing
            )
            user._password = user_data.get('password')
            return user
        return None

    @staticmethod
    def get_user_by_google_id(google_id):
        user_data = db.users.find_one({'google_id': google_id})
        if user_data:
            user = User(
                email=user_data['email'],
                google_id=google_id,
                name=user_data.get('name', 'Not provided'),  # Default value if name is missing
                is_admin=user_data.get('is_admin', False),
                created_at=user_data.get('created_at', datetime.utcnow())  # Default value if date is missing
            )
            user._password = user_data.get('password')
            return user
        return None

    @staticmethod
    def find_by_email(email):
        """Alias for get_user_by_email to maintain Flask-Login compatibility"""
        return User.get_user_by_email(email)

    @staticmethod
    def setup_indexes():
        """Create necessary indexes for the users collection"""
        from config.database import db
        # Create unique index on email field
        db.users.create_index('email', unique=True)
        # Create index on google_id field
        db.users.create_index('google_id', sparse=True)
