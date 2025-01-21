from models.user import User
from config.database import db
from utils.admin_manager import AdminManager
import logging

logger = logging.getLogger(__name__)

def setup_database():
    """Setup database indexes and initial data if not already initialized"""
    try:
        print("\n=== Checking Database Setup ===")
        
        # Check if database is already initialized by looking for admin users
        admin_manager = AdminManager()
        admins = admin_manager.load_admins()
        existing_admin = db.users.find_one({"email": admins[0]["email"]}) if admins else None
        
        if existing_admin:
            print("Database already initialized, skipping setup...")
            return
            
        print("First-time database initialization...")
        
        # Setup indexes (this is idempotent - safe to run multiple times)
        print("1. Setting up database indexes...")
        User.setup_indexes()
        
        # Create admin users from environment variables
        print("2. Creating admin users...")
        for admin in admins:
            print(f"   Creating admin: {admin['email']}")
            User.create_user(
                email=admin['email'],
                password=admin['password'],
                name=admin['name'],
                is_admin=True
            )
            
        print("=== Database Setup Complete ===\n")
        
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        raise e
