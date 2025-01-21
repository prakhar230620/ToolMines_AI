from config.database import db
from datetime import datetime

class Tool:
    def __init__(self, tool_id, name, description, category, route):
        self.tool_id = tool_id  # e.g., "CHAT001" for chatbot, "VOICE001" for voicebot
        self.name = name
        self.description = description
        self.category = category
        self.route = route
        self.created_at = datetime.utcnow()
        self.total_usage = 0

    @staticmethod
    def create(tool_id, name, description, category, route):
        """Create a new tool record"""
        tool = Tool(tool_id, name, description, category, route)
        db.tools.insert_one({
            'tool_id': tool.tool_id,
            'name': tool.name,
            'description': tool.description,
            'category': tool.category,
            'route': tool.route,
            'created_at': tool.created_at,
            'total_usage': tool.total_usage
        })
        return tool

    @staticmethod
    def get_all_tools():
        """Get all tools"""
        return list(db.tools.find())

    @staticmethod
    def increment_usage(tool_id):
        """Increment the usage count of a tool"""
        db.tools.update_one(
            {'tool_id': tool_id},
            {'$inc': {'total_usage': 1}}
        )

    @staticmethod
    def get_tool_by_id(tool_id):
        """Get tool by ID"""
        return db.tools.find_one({'tool_id': tool_id})

    @staticmethod
    def get_real_time_stats():
        """Get real-time usage statistics for all tools"""
        try:
            tools = list(db.tools.find())
            if not tools:
                return {
                    'labels': [],
                    'values': []
                }
            return {
                'labels': [str(tool.get('name', '')) for tool in tools],
                'values': [int(tool.get('total_usage', 0)) for tool in tools]
            }
        except Exception as e:
            print(f"Error getting real-time stats: {str(e)}")
            return {
                'labels': [],
                'values': []
            }
