"""Configuration for tool services in production environment"""

# This will be configured during deployment
TOOL_SERVICES = {
    'chatbot': {
        'url': 'http://chatbot-service.example.com',  # Will be replaced with actual domain
        'endpoints': ['/chat', '/reset']
    },
    'voicebot': {
        'url': 'http://voicebot-service.example.com',
        'endpoints': ['/voice', '/stream']
    },
    'lang_trans': {
        'url': 'http://translate-service.example.com',
        'endpoints': ['/translate']
    },
    'converter': {
        'url': 'http://converter-service.example.com',
        'endpoints': ['/convert']
    }
}

def get_tool_service_url(tool_name):
    """Get the URL for a specific tool service"""
    service = TOOL_SERVICES.get(tool_name)
    return service['url'] if service else None

def is_valid_tool_endpoint(tool_name, endpoint):
    """Check if an endpoint is valid for a specific tool"""
    service = TOOL_SERVICES.get(tool_name)
    return service and endpoint in service['endpoints']
