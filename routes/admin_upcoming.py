from flask import Blueprint, render_template, jsonify, request
from routes.admin_auth import admin_required
import json
import os

admin_upcoming = Blueprint('admin_upcoming', __name__)

# File paths for storing data
UPCOMING_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
STATS_FILE = os.path.join(UPCOMING_DATA_DIR, 'upcoming_stats.json')
TOOLS_FILE = os.path.join(UPCOMING_DATA_DIR, 'upcoming_tools.json')

# Ensure data directory exists
os.makedirs(UPCOMING_DATA_DIR, exist_ok=True)

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    return {
        'tools_count': 3,
        'progress': 60,
        'quarter': 'Q1',
        'year': 2024
    }

def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f)

def load_tools():
    if os.path.exists(TOOLS_FILE):
        with open(TOOLS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_tools(tools):
    with open(TOOLS_FILE, 'w') as f:
        json.dump(tools, f)

@admin_upcoming.route('/admin/upcoming')
@admin_required
def update_upcoming():
    stats = load_stats()
    tools = load_tools()
    return render_template('admin/update_upcoming.html', stats=stats, tools=tools)

@admin_upcoming.route('/api/admin/upcoming/stats', methods=['POST'])
@admin_required
def update_stats():
    stats = request.get_json()
    save_stats(stats)
    return jsonify({'status': 'success'})

@admin_upcoming.route('/api/admin/upcoming/tool/<int:tool_id>', methods=['POST'])
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

@admin_upcoming.route('/api/admin/upcoming/tool/<int:tool_id>', methods=['DELETE'])
@admin_required
def delete_tool(tool_id):
    tools = load_tools()
    tools = [tool for tool in tools if tool['id'] != tool_id]
    save_tools(tools)
    return jsonify({'status': 'success'})

@admin_upcoming.route('/api/admin/upcoming/tool', methods=['PUT'])
@admin_required
def add_tool():
    tools = load_tools()
    new_tool = request.get_json()
    new_tool['id'] = max([tool['id'] for tool in tools], default=0) + 1
    tools.append(new_tool)
    save_tools(tools)
    return jsonify({'status': 'success', 'id': new_tool['id']})
