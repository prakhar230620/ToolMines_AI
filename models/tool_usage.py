from datetime import datetime, timedelta
from config.database import db

class ToolUsage:
    def __init__(self, tool_name, user_id=None, used_at=None):
        self.tool_name = tool_name
        self.user_id = user_id
        self.used_at = used_at or datetime.utcnow()

    @staticmethod
    def create(tool_name, user_id=None):
        """Create a new tool usage record"""
        usage = ToolUsage(tool_name, user_id)
        db.tool_usage.insert_one({
            'tool_name': usage.tool_name,
            'user_id': usage.user_id,
            'used_at': usage.used_at
        })
        return usage

    @staticmethod
    def get_usage_stats(days=7):
        """Get tool usage statistics for the last n days"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            pipeline = [
                {
                    '$match': {
                        'used_at': {'$gte': start_date}
                    }
                },
                {
                    '$group': {
                        '_id': '$tool_name',
                        'count': {'$sum': 1}
                    }
                },
                {
                    '$sort': {'count': -1}
                }
            ]
            stats = list(db.tool_usage.aggregate(pipeline))
            
            # Convert MongoDB cursor to simple Python types
            return {
                'labels': [str(stat['_id']) for stat in stats],
                'values': [int(stat['count']) for stat in stats]
            }
        except Exception as e:
            print(f"Error in get_usage_stats: {str(e)}")
            return {'labels': [], 'values': []}

    @staticmethod
    def get_daily_usage(days=7):
        """Get daily tool usage for the last n days"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            pipeline = [
                {
                    '$match': {
                        'used_at': {'$gte': start_date}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$used_at'}},
                            'tool': '$tool_name'
                        },
                        'count': {'$sum': 1}
                    }
                },
                {
                    '$sort': {'_id.date': 1}
                }
            ]
            daily_stats = list(db.tool_usage.aggregate(pipeline))
            
            # Convert MongoDB cursor to simple Python types
            dates = sorted(list(set(str(stat['_id']['date']) for stat in daily_stats)))
            tools = sorted(list(set(str(stat['_id']['tool']) for stat in daily_stats)))
            
            # Create a matrix of usage data
            usage_data = {str(tool): [0] * len(dates) for tool in tools}
            for stat in daily_stats:
                tool = str(stat['_id']['tool'])
                date_idx = dates.index(str(stat['_id']['date']))
                usage_data[tool][date_idx] = int(stat['count'])
            
            return {
                'dates': dates,
                'tools': tools,
                'usage_data': usage_data
            }
        except Exception as e:
            print(f"Error in get_daily_usage: {str(e)}")
            return {'dates': [], 'tools': [], 'usage_data': {}}

    @staticmethod
    def get_yearly_stats():
        """Get tool usage statistics starting from January 2025"""
        try:
            start_date = datetime(2025, 1, 1)
            current_date = datetime.utcnow()
            months_data = {}
            labels = []

            # Initialize data structure for all tools
            tools = db.tools.distinct('tool_id')
            
            while start_date <= current_date:
                end_date = datetime(start_date.year, start_date.month + 1, 1) if start_date.month < 12 else datetime(start_date.year + 1, 1, 1)
                month_label = start_date.strftime("%B %Y")
                
                # Get usage count for each tool in this month
                for tool_id in tools:
                    if tool_id not in months_data:
                        months_data[tool_id] = []
                    
                    count = db.tool_usage.count_documents({
                        "tool_id": tool_id,
                        "timestamp": {
                            "$gte": start_date,
                            "$lt": end_date
                        }
                    })
                    months_data[tool_id].append(count)
                
                labels.append(month_label)
                
                # Move to next month
                if start_date.month == 12:
                    start_date = datetime(start_date.year + 1, 1, 1)
                else:
                    start_date = datetime(start_date.year, start_date.month + 1, 1)

            # Create datasets with smooth curves
            return {
                "labels": labels,
                "datasets": [
                    {
                        "label": tool_id,
                        "data": months_data[tool_id],
                        "borderColor": f"hsl({i * 360 / len(tools)}, 70%, 50%)",
                        "tension": 0.4,  # Makes the line smoother
                        "fill": False
                    } for i, tool_id in enumerate(tools)
                ]
            }
        except Exception as e:
            print(f"Error getting yearly stats: {str(e)}")
            return {
                "labels": [],
                "datasets": []
            }

    @staticmethod
    def get_popular_tools(limit=5):
        """Get the most popular tools"""
        try:
            pipeline = [
                {
                    '$group': {
                        '_id': '$tool_name',
                        'count': {'$sum': 1}
                    }
                },
                {
                    '$sort': {'count': -1}
                },
                {
                    '$limit': limit
                }
            ]
            results = list(db.tool_usage.aggregate(pipeline))
            
            # Convert MongoDB cursor to simple Python types
            return [{'_id': str(result['_id']), 'count': int(result['count'])} for result in results]
        except Exception as e:
            print(f"Error in get_popular_tools: {str(e)}")
            return []
