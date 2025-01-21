import os
from typing import List, Dict
from dotenv import load_dotenv
import json
import logging

logger = logging.getLogger(__name__)

class AdminManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdminManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            self.initialized = True
            self.load_admins()

    def load_admins(self) -> List[Dict[str, str]]:
        """Load admin credentials from environment variables"""
        load_dotenv()
        
        # Get the JSON string from environment variable
        admin_json = os.getenv('ADMIN_CREDENTIALS', '{"admins":[]}')
        try:
            # Parse the JSON string into a list of dictionaries
            admin_data = json.loads(admin_json)
            self.admins = admin_data.get('admins', [])
            logger.info(f"Loaded {len(self.admins)} admin credentials")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ADMIN_CREDENTIALS JSON: {str(e)}")
            self.admins = []
        except Exception as e:
            logger.error(f"Error loading admin credentials: {str(e)}")
            self.admins = []
        
        return self.admins

    def is_admin_email(self, email: str) -> bool:
        """Check if an email belongs to an admin"""
        return any(admin['email'].lower() == email.lower() for admin in self.admins)

    def verify_admin(self, email: str, password: str) -> bool:
        """Verify admin credentials"""
        for admin in self.admins:
            if admin['email'].lower() == email.lower() and admin['password'] == password:
                return True
        return False

    def get_admin_name(self, email: str) -> str:
        """Get admin name by email"""
        for admin in self.admins:
            if admin['email'].lower() == email.lower():
                return admin.get('name', 'Admin')
        return None
