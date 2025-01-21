from flask import Blueprint, render_template, jsonify, request
from routes.admin_auth import admin_required
import json
import os

admin_index = Blueprint('admin_index', __name__)

# File path for storing data
INDEX_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
TOOLS_FILE = os.path.join(INDEX_DATA_DIR, 'index_tools.json')

# Ensure data directory exists
os.makedirs(INDEX_DATA_DIR, exist_ok=True)

def load_tools():
    if os.path.exists(TOOLS_FILE):
        with open(TOOLS_FILE, 'r') as f:
            return json.load(f)
    return [
        {
            "id": 1,
            "name": "AI Chatbot",
            "icon": "ph ph-robot",
            "description": "Get instant answers and assistance for any task with our advanced AI chatbot.",
            "badge_type": "popular",
            "link": "/chatbot",
            "features": [
                "24/7 Availability",
                "Multi-language Support",
                "Context Understanding"
            ],
            "button_text": "Try Now"
        },
        {
            "id": 2,
            "name": "Language Translator",
            "icon": "ph ph-translate",
            "description": "Break language barriers with our advanced translation and language processing tools.",
            "badge_type": "trending",
            "link": "/lang_trans",
            "features": [
                "100+ Languages",
                "Real-time Translation",
                "Grammar Check"
            ],
            "button_text": "Translate Now"
        },
        {
            "id": 3,
            "name": "File Format Converter",
            "icon": "ph ph-file-doc",
            "description": "Convert files between different formats quickly and efficiently.",
            "badge_type": "new",
            "link": "/converter",
            "features": [
                "Multiple Formats",
                "Convert Upto 100 MB File Size",
                "High Quality Output"
            ],
            "button_text": "Convert Files"
        }
    ]

def save_tools(tools):
    with open(TOOLS_FILE, 'w') as f:
        json.dump(tools, f, indent=2)

@admin_index.route('/admin/index')
@admin_required
def update_index():
    tools = load_tools()
    return render_template('admin/update_index.html', tools=tools)

@admin_index.route('/api/admin/index/tool/<int:tool_id>', methods=['POST'])
@admin_required
def update_tool(tool_id):
    tools = load_tools()
    tool_data = request.get_json()
    
    # Update existing tool
    for tool in tools:
        if tool['id'] == tool_id:
            tool.update(tool_data)
            break
    
    save_tools(tools)
    return jsonify({'status': 'success'})

@admin_index.route('/api/admin/index/tool/<int:tool_id>', methods=['DELETE'])
@admin_required
def delete_tool(tool_id):
    tools = load_tools()
    tools = [tool for tool in tools if tool['id'] != tool_id]
    save_tools(tools)
    return jsonify({'status': 'success'})

@admin_index.route('/api/admin/index/tool', methods=['PUT'])
@admin_required
def add_tool():
    tools = load_tools()
    new_tool = request.get_json()
    new_tool['id'] = max([tool['id'] for tool in tools], default=0) + 1
    tools.append(new_tool)
    save_tools(tools)
    return jsonify({'status': 'success', 'id': new_tool['id']})
