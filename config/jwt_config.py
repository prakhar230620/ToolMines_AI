from datetime import datetime, timedelta
import jwt
from functools import wraps
from flask import request, jsonify, current_app

# JWT configuration
JWT_SECRET_KEY = '14701c4d1e765347259951b561146a45'  # Using same secret key as app
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

def generate_token(user_id):
    """Generate a new JWT token for a user"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRES,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def validate_token(token):
    """Validate a JWT token and return the user_id if valid"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                token = auth_header  # Just the token
                
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
            
        user_id = validate_token(token)
        if not user_id:
            return jsonify({'error': 'Token is invalid or expired'}), 401
            
        return f(*args, **kwargs)
    return decorated
