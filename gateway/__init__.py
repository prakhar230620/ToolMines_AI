from flask import Blueprint, request, jsonify
import requests
from config.jwt_config import token_required, validate_token
from models.tool import Tool
from models.tool_usage import ToolUsage

gateway = Blueprint('gateway', __name__)

# Tool service configurations
TOOL_SERVICES = {
    'chatbot': {
        'url': 'http://localhost:5001',  # Example URL, will be configured during deployment
        'endpoints': ['/chat', '/reset']
    },
    'voicebot': {
        'url': 'http://localhost:5002',
        'endpoints': ['/voice', '/stream']
    },
    'lang_trans': {
        'url': 'http://localhost:5003',
        'endpoints': ['/translate']
    },
    'converter': {
        'url': 'http://localhost:5004',
        'endpoints': ['/convert']
    }
}

def track_tool_usage(tool_name, user_id):
    """Track tool usage in the main platform"""
    tool = Tool.get_tool_by_name(tool_name)
    if tool:
        Tool.increment_usage(tool['id'])
        ToolUsage.create(tool['name'], user_id)

@gateway.route('/api/<tool_name>/<path:endpoint>', methods=['GET', 'POST'])
@token_required
def route_tool_request(tool_name, endpoint):
    # Validate tool exists
    if tool_name not in TOOL_SERVICES:
        return jsonify({'error': 'Tool not found'}), 404
        
    service = TOOL_SERVICES[tool_name]
    
    # Get user_id from token for tracking
    token = request.headers.get('Authorization')
    user_id = validate_token(token.split(" ")[1] if " " in token else token)
    
    # Forward request to tool service
    target_url = f"{service['url']}/{endpoint}"
    
    try:
        # Forward the request with same method and headers
        response = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            stream=True
        )
        
        # Track usage
        track_tool_usage(tool_name, user_id)
        
        # Return the response from the tool service
        return (response.raw.read(),
                response.status_code,
                response.headers.items())
    except requests.RequestException as e:
        return jsonify({'error': f'Service unavailable: {str(e)}'}), 503
