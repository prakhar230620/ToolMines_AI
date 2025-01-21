from models.tool import Tool
from config.database import db

def initialize_tools():
    # Clear existing tools
    db.tools.delete_many({})

    # Define initial tools
    tools = [
        {
            'tool_id': 'CHAT001',
            'name': 'Chatbot',
            'description': 'Experience the future of conversation with our AI chatbot',
            'category': 'conversation',
            'route': '/chatbot'
        },
        {
            'tool_id': 'VOICE001',
            'name': 'Voicebot',
            'description': 'Translate your voice between different languages in real-time',
            'category': 'conversion',
            'route': '/voicebot'
        },
        {
            'tool_id': 'CONV001',
            'name': 'File Format Converter',
            'description': 'Convert files between multiple formats',
            'category': 'conversion',
            'route': '/converter'
        },
        {
            'tool_id': 'TRANS001',
            'name': 'Text Translator',
            'description': 'Translate text between 100+ languages instantly',
            'category': 'translation',
            'route': '/lang_trans'
        }
    ]

    # Insert tools into database
    for tool in tools:
        Tool.create(
            tool_id=tool['tool_id'],
            name=tool['name'],
            description=tool['description'],
            category=tool['category'],
            route=tool['route']
        )
