from flask import Blueprint, render_template, jsonify, request
from routes.admin_auth import admin_required
from models.tool import Tool
from models.tool_usage import ToolUsage
from models.user_stats import UserStats
from datetime import datetime, timedelta
import random
from config.database import db

admin_dashboard = Blueprint('admin_dashboard', __name__)

def generate_sample_data():
    """Generate sample tool usage data if none exists"""
    try:
        # Check if we have any data
        if db.tool_usage.count_documents({}) == 0:
            tools = ['AI Chatbot', 'Language Translator', 'Code Generator', 'Image Editor', 'Text Summarizer']
            # Generate data for the last 30 days
            for i in range(30):
                date = datetime.utcnow() - timedelta(days=i)
                # Generate 10-50 uses per tool per day
                for tool in tools:
                    uses = random.randint(10, 50)
                    for _ in range(uses):
                        ToolUsage.create(tool)
    except Exception as e:
        print(f"Error generating sample data: {str(e)}")

@admin_dashboard.route('/admin/dashboard')
@admin_required
def dashboard():
    try:
        # Generate sample data if needed
        generate_sample_data()
        
        # Get real-time tool usage stats
        real_time_stats = Tool.get_real_time_stats()
        
        # Get usage trends for last 7 days
        weekly_stats = ToolUsage.get_usage_stats(days=7)
        if not weekly_stats:
            weekly_stats = {'labels': [], 'values': []}
        
        # Get yearly tool usage statistics
        yearly_stats = ToolUsage.get_yearly_stats()
        
        # Get tool usage statistics
        usage_stats = ToolUsage.get_usage_stats(days=30)
        if not usage_stats:
            usage_stats = {'labels': [], 'values': []}
            
        daily_usage = ToolUsage.get_daily_usage(days=7)
        if not daily_usage:
            daily_usage = {'dates': [], 'tools': [], 'usage_data': {}}
            
        popular_tools = ToolUsage.get_popular_tools(limit=5)
        if not popular_tools:
            popular_tools = []
        
        # Get user statistics
        total_users = UserStats.get_total_users()
        active_users = UserStats.get_active_users(days=30)
        new_users = UserStats.get_new_users(days=30)
        user_growth = UserStats.get_user_growth()
        user_activity = UserStats.get_user_activity()
        
        # Calculate total usage and growth
        total_usage = sum(usage_stats.get('values', [0]))
        prev_month_stats = ToolUsage.get_usage_stats(days=60)
        if not prev_month_stats:
            prev_month_stats = {'values': []}
        prev_month_total = sum(prev_month_stats.get('values', [0]))
        growth_rate = ((total_usage - prev_month_total) / prev_month_total * 100) if prev_month_total > 0 else 0
        
        # Calculate user growth rate
        user_growth_rate = ((new_users) / total_users * 100) if total_users > 0 else 0
        
        # Ensure all data is JSON serializable
        return render_template('admin/admin_dashboard.html',
                           real_time_stats=real_time_stats,
                           weekly_stats={
                               'labels': [str(label) for label in weekly_stats.get('labels', [])],
                               'values': [int(value) for value in weekly_stats.get('values', [])]
                           },
                           yearly_stats=yearly_stats,
                           usage_stats={
                               'labels': [str(label) for label in usage_stats.get('labels', [])],
                               'values': [int(value) for value in usage_stats.get('values', [])]
                           },
                           daily_usage={
                               'dates': [str(date) for date in daily_usage.get('dates', [])],
                               'tools': [str(tool) for tool in daily_usage.get('tools', [])],
                               'usage_data': {str(k): [int(v) for v in vals] 
                                            for k, vals in daily_usage.get('usage_data', {}).items()}
                           },
                           popular_tools=[{
                               '_id': str(tool.get('_id', '')),
                               'count': int(tool.get('count', 0))
                           } for tool in popular_tools],
                           total_usage=int(total_usage),
                           growth_rate=float(growth_rate),
                           # User statistics
                           total_users=int(total_users),
                           active_users=int(active_users),
                           new_users=int(new_users),
                           user_growth_rate=float(user_growth_rate),
                           user_growth=user_growth,
                           user_activity=user_activity)
    except Exception as e:
        print(f"Error in dashboard route: {str(e)}")
        # Return empty data if there's an error
        return render_template('admin/admin_dashboard.html',
                           real_time_stats={'labels': [], 'values': []},
                           weekly_stats={'labels': [], 'values': []},
                           yearly_stats={'labels': [], 'datasets': []},
                           usage_stats={'labels': [], 'values': []},
                           daily_usage={'dates': [], 'tools': [], 'usage_data': {}},
                           popular_tools=[],
                           total_usage=0,
                           growth_rate=0.0,
                           total_users=0,
                           active_users=0,
                           new_users=0,
                           user_growth_rate=0.0,
                           user_growth={'labels': [], 'values': []},
                           user_activity={'labels': [], 'values': []})

@admin_dashboard.route('/api/tool-stats')
def get_tool_stats():
    """API endpoint for real-time tool statistics"""
    return Tool.get_real_time_stats()

@admin_dashboard.route('/api/admin/dashboard/usage-stats')
@admin_required
def get_usage_stats():
    try:
        days = int(request.args.get('days', 30))
        stats = ToolUsage.get_usage_stats(days=days)
        return jsonify({
            'labels': [str(label) for label in stats.get('labels', [])],
            'values': [int(value) for value in stats.get('values', [])]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_dashboard.route('/api/admin/dashboard/daily-usage')
@admin_required
def get_daily_usage():
    try:
        days = int(request.args.get('days', 7))
        usage = ToolUsage.get_daily_usage(days=days)
        return jsonify({
            'dates': [str(date) for date in usage.get('dates', [])],
            'tools': [str(tool) for tool in usage.get('tools', [])],
            'usage_data': {str(k): [int(v) for v in vals] 
                          for k, vals in usage.get('usage_data', {}).items()}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_dashboard.route('/api/admin/dashboard/popular-tools')
@admin_required
def get_popular_tools():
    try:
        limit = int(request.args.get('limit', 5))
        tools = ToolUsage.get_popular_tools(limit=limit)
        return jsonify([{
            '_id': str(tool['_id']),
            'count': int(tool['count'])
        } for tool in tools])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_dashboard.route('/api/admin/dashboard/traffic/<period>')
@admin_required
def admin_traffic_api(period):
    try:
        # TODO: Replace with actual database queries
        if period == 'daily':
            labels = [(datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(7)][::-1]
            values = [random.randint(100, 1000) for _ in range(7)]
        elif period == 'monthly':
            labels = [(datetime.now() - timedelta(days=x*30)).strftime('%Y-%m') for x in range(6)][::-1]
            values = [random.randint(3000, 30000) for _ in range(6)]
        else:  # yearly
            labels = [(datetime.now() - timedelta(days=x*365)).strftime('%Y') for x in range(3)][::-1]
            values = [random.randint(36000, 360000) for _ in range(3)]
        
        return jsonify({'labels': labels, 'values': values})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_dashboard.route('/api/admin/dashboard/new-users')
@admin_required
def admin_new_users_api():
    try:
        # TODO: Replace with actual database queries
        labels = [(datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(7)][::-1]
        values = [random.randint(5, 50) for _ in range(7)]
        return jsonify({'labels': labels, 'values': values})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_dashboard.route('/api/admin/dashboard/tool-usage')
@admin_required
def admin_tool_usage_api():
    try:
        # TODO: Replace with actual database queries
        labels = ['AI Chatbot', 'Language Translator', 'File Converter']
        values = [random.randint(100, 1000) for _ in range(3)]
        return jsonify({'labels': labels, 'values': values})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
